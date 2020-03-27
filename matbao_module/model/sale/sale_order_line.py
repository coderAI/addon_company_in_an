# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import Warning
import odoo.addons.decimal_precision as dp


REGISTER_TYPE = [("register", "Register"),
                 ("renew", "Renew"),
                 ("transfer", "Transfer")]

SERVICE_STATUS = [("draft", "Draft"),
                  ("waiting", "Waiting for Activation"),
                  ("done", "Done"),
                  ("refused", "Refused")]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    register_type = fields.Selection(
        REGISTER_TYPE, required=True, string="Register Type")
    parent_product_id = fields.Many2one('product.product',
                                        string="Parent Product")
    service_status = fields.Selection(
        SERVICE_STATUS, string="Status", readonly=True, default='draft',
        copy=False)
    product_category_id = fields.Many2one(
        'product.category', string="Product Category", required=True)
    register_untaxed_price = fields.Float('Setup Untaxed Price',
                                          readonly=True)
    register_taxed_price = fields.Float('Setup Taxed Price',
                                        readonly=True)
    renew_untaxed_price = fields.Float('Renew Untaxed Price', readonly=True)
    renew_taxed_price = fields.Float('Renew taxed Price', readonly=True)
    register_taxed_amount = fields.Float('Setup Taxed Amount',
                                         readonly=True)
    renew_taxed_amount = fields.Float('Renew taxed Amount', readonly=True)
    time = fields.Float("Time", required=True)
    price_updated = fields.Boolean(
        string="price updated?",
        readonly=True, copy=False)
    fully_paid = fields.Boolean('Fully Paid?', related='order_id.fully_paid')

    fix_subtotal = fields.Float('Subtotal',
                                digits=dp.get_precision('Product Price'),
                                default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount',
                                     string='Subtotal', readonly=True,
                                     store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes',
                                readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total',
                                  readonly=True, store=True)
    template = fields.Char(string='Template')

    @api.depends('product_uom_qty', 'discount', 'price_unit',
                 'register_untaxed_price', 'register_taxed_price',
                 'register_taxed_amount', 'renew_untaxed_price',
                 'renew_taxed_price', 'renew_taxed_amount',
                 'register_type', 'time')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            # total = line.fix_subtotal or 0.0
            total = 0.0
            tax_amount = 0.0

            taxes = line.tax_id.compute_all(
                        line.register_taxed_price, line.order_id.currency_id,
                        line.product_uom_qty, product=line.product_id,
                        partner=line.order_id.partner_shipping_id)
            renew_taxes = line.tax_id.compute_all(
                        line.renew_taxed_price, line.order_id.currency_id,
                        line.product_uom_qty, product=line.product_id,
                        partner=line.order_id.partner_shipping_id)
            register_tax_amount = taxes['total_included'] - taxes['total_excluded']
            renew_tax_amount = renew_taxes['total_included'] - renew_taxes['total_excluded']

            # Compute total
            if not total:
                    total = sum([line.register_untaxed_price,
                                line.register_taxed_price,
                                register_tax_amount,
                                line.renew_untaxed_price,
                                line.renew_taxed_price,
                                renew_tax_amount])

            # Compute taxes
            tax_amount += register_tax_amount + renew_tax_amount

            line.update({'price_tax': tax_amount,
                         'price_total': total,
                         'price_subtotal': total - tax_amount})

    def prepare_po_vals(self):
        """
            TO DO:
            - Prepare values to create purchase order
        """
        self.ensure_one()
        ir_values_obj = self.env['ir.values']
        partner_id = ir_values_obj.get_default('purchase.config.settings',
                                               'partner_id')
        if not partner_id:
            raise Warning(_('The default Vendor has been deleted!'))
        return {'partner_id': partner_id,
                'date_planned': fields.Datetime.now(),
                'sale_order_line_id': self.id,
                'company_id': self.order_id.company_id.id}

    @api.multi
    def create_po(self):
        """
            TO DO:
            - Create First Purchase Order with qty =1:
            - if register_type == 'register' and time > 1.0:
                Create a renew Purchase Order
        """

        PurchaseOrder = self.env['purchase.order'].with_context(company_id=self.order_id.partner_id.company_id.id, force_company=self.order_id.partner_id.company_id.id)
        PurchaseOrderLine = self.env['purchase.order.line'].with_context(company_id=self.order_id.partner_id.company_id.id, force_company=self.order_id.partner_id.company_id.id)

        new_pos = self.env['purchase.order']
        for order_line in self:
            # Check PO exists
            if PurchaseOrder.search([('sale_order_line_id', '=', order_line.id)]):
                raise Warning(_("Can't create PO. Order Line have created PO."))
            # Create new Purchase Order
            po_vals = self.with_context(force_company=self.order_id.partner_id.company_id.id).prepare_po_vals()
            new_po = PurchaseOrder.with_context(force_company=self.order_id.partner_id.company_id.id).create(po_vals)
            new_pos |= new_po
            # Create new purchase order lines
            template=''

            if self.license:
                template = str(self.license or 1)
            else:
                template = self.template or '1'
            line_vals = {
                'name': self.product_id.display_name,
                'product_id': order_line.product_id.id,
                # 'product_qty': (order_line.register_type == 'register' and
                #                 order_line.time > 1.0 and 1.0
                #                 ) or order_line.time,
                'product_qty': order_line.time,
                'price_unit': 0,
                'taxes_id': [],
                'order_id': new_po.id,
                # 'product_uom': self.product_id.uom_po_id.id,
                'product_uom': order_line.product_uom and order_line.product_uom.id or order_line.product_id.uom_po_id.id,
                'date_planned': new_po.date_order,
                'sale_order_line_id': self.id,
                'register_type': self.register_type,
                'company_id': self.order_id.company_id.id,
                'template': template,
                }
            PurchaseOrderLine.with_context(company_id = self.order_id.partner_id.company_id.id, force_company=self.order_id.partner_id.company_id.id).create(line_vals)
            # Create renew Request for Quotation
            # ----------------------Close by Hai 13/10/2017------------------------#
            # if order_line.register_type == 'register' and \
            #         order_line.time > 1.0:
            #     renew_vals = self.prepare_po_vals()
            #     renew_po = PurchaseOrder.create(renew_vals)
            #     line_vals.update({'product_qty': order_line.time - 1.0,
            #                       'order_id': renew_po.id,
            #                       'date_planned': renew_po.date_order,
            #                       'register_type': 'renew'})
            #     PurchaseOrderLine.create(line_vals)
            #     new_pos |= renew_po
            # ------------------------------- end ---------------------------------#
        return new_pos

    @api.multi
    def create_service(self):
        SaleService = self.env['sale.service'].with_context(company_id=self.order_id.company_id.id, force_company=self.order_id.partner_id.company_id.id)
        for record in self:
            reseller_id = self.env['reseller.customer'].search([('code', '=', record.reseller)], limit=1)
            data = {
                'customer_id': record.order_id.partner_id.id,
                'product_category_id': record.product_category_id.id,
                'product_id': record.product_id.id,
                'salesperson_id': record.order_id.user_id.id,
                'sales_order_ids': [(4, record.order_id.id)],
                'time': record.time,
                'reseller_id':reseller_id and reseller_id.id or False,
                'uom_id': record.product_uom.id,
                'status': 'waiting',
                'so_line_id': record.id
            }
            domain = [('customer_id', '=', record.order_id.partner_id.id),
                      ('product_category_id', '=', record.product_category_id.id),
                      ('product_id', '=', record.product_id.id)]
            if record.parent_product_id:  # addon
                data['parent_product_id'] = record.parent_product_id.id
                args = [('product_id', '=', record.parent_product_id.id),
                        '|', '&',
                        ('sales_order_ids', 'not in', [record.order_id.id]),
                        ('status', '=', 'active'),
                        '&',
                        ('sales_order_ids', 'in', [record.order_id.id]),
                        ('status', 'in', ('waiting', 'draft'))]
                parent_service = SaleService.search(args, limit=1)
                if parent_service:
                    data['parent_id'] = parent_service.id
                    domain += [('parent_id', '=', parent_service.id)]
                old_services = SaleService.search(domain)
                if not old_services:
                    old_services = SaleService.with_context(force_company=self.order_id.partner_id.company_id.id).create(data)
                else:
                    old_services.write({
                        'so_line_id': record.id,
                        'sales_order_ids': [(4, record.order_id.id)]})
                return old_services

            else:  # service
                service = SaleService.search(domain)
                if not service:
                    service = SaleService.with_context(force_company=self.order_id.partner_id.company_id.id).create(data)
                else:
                    service.write({
                        'so_line_id': record.id,
                        'sales_order_ids': [(4, record.order_id.id)]})

                args = [('sales_order_ids', 'in', [record.order_id.id]),
                        ('parent_product_id', '=', data['product_id']),
                        ('parent_id', '=', False)]
                addon_list = SaleService.search(args)
                addon_vals = []
                for addon in addon_list:
                    addon_vals += [(4, addon.id, None)]
                if addon_vals:
                    service.addon_list_ids = addon_vals
                return service

    @api.multi
    def activate(self):
        """
            TO DO:
            - Update service status to Waiting
            - Create Purchase Order
            - Create services
        """
        self.write({'service_status': 'waiting'})
        self.create_po()
        service = self.create_service()
        return service

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        line_vals = super(SaleOrderLine, self.with_context(force_company=self.order_id.partner_id.company_id.id))._prepare_invoice_line(qty)
        line_vals.update({
            'register_type': self.register_type,
        })
        return line_vals
