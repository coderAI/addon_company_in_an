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
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging
from odoo.exceptions import Warning
from odoo.osv.orm import setup_modifiers
from lxml import etree


STATUS = [('draft', 'Draft'),
          ('waiting', 'Waiting for Activation'),
          ('active', 'Active'),
          ('refused', 'Refused'),
          ('closed', 'Closed')]


class SaleService(models.Model):
    _name = 'sale.service'
    _rec_name = 'name'

    @api.multi
    def _compute_invoice_count(self):
        for service in self:
            service.invoice_count = sum(service.sales_order_ids.mapped('invoice_count'))

    name = fields.Char("Name", default=lambda self: _('New'))
    customer_id = fields.Many2one(
        'res.partner', required=True, string="Customer")
    ip_hosting = fields.Char("IP Hosting")
    ip_email = fields.Char("IP Email")
    product_category_id = fields.Many2one(
        'product.category', required=True, string="Product Category")
    product_id = fields.Many2one(
        'product.product', required=True, string="Product")
    parent_id = fields.Many2one(
        'sale.service', string="Parent Service")
    parent_product_id = fields.Many2one(
        'product.product', string="Parent Product")
    reference = fields.Char(string="Reference", readonly=True)
    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    start_date = fields.Date("Start Date", default=fields.Date.context_today)
    end_date = fields.Date("End Date")
    addon_list_ids = fields.One2many('sale.service', 'parent_id',
                                     string="ADD-ON LIST")
    status = fields.Selection(
        STATUS, string="Status", readonly=True, default='draft')
    sales_order_ids = fields.Many2many('sale.order', string="Sales Order")
    invoice_count = fields.Integer(
        "Invoice Count", compute="_compute_invoice_count", readonly=True)
    description = fields.Char('Description')
    time = fields.Float("Time")
    uom_id = fields.Many2one('product.uom', string="UOM")
    so_line_id = fields.Many2one('sale.order.line', string="Sale order line")

    @api.model
    def create(self, vals):
        res = super(SaleService, self).create(vals)
        if not res.reference:
            if res.product_category_id.code:
                if res.product_category_id.service_sequence_id:
                    sequence_number = \
                        res.product_category_id.service_sequence_id.next_by_id()
                    res.reference = ''.join(
                        [res.product_category_id.code, sequence_number])
            else:
                raise Warning(_("Please update the product category code!"))
        if res.reference:
            res.name = res.reference + ' - ' + res.product_id.name
        else:
            res.name = res.product_id.name
        return res

    @api.multi
    def start(self):
        self.write({'status': 'active'})
        # for record in self:
        #     record.status = 'active'
            # record.start_date = fields.Date.context_today(self)

    @api.multi
    def close(self):
        self.write({'status': 'closed'})
        # for record in self:
        #     record.status = 'closed'
            # record.end_date = fields.Date.context_today(self)

    @api.multi
    def action_view_invoice(self):
        self.ensure_one()
        if self.sales_order_ids:
            return self.sales_order_ids.action_view_invoice()
        return False

    @api.model
    def renew_sales_orders(self):
        """
            TO DO:
            - Create Renewed Sale Orders automatically
        """

        logging.info("=== START: SCHEDULER RENEW SALE ORDERS ===")
        IrValues = self.env['ir.values']
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        ProductCategory = self.env['product.category']
        ProductUom = self.env['product.uom']

        days_to_renew = IrValues.get_default('sale.config.settings',
                                             'days_to_renew')
        if not days_to_renew:
            logging.error("=== Error: Can't get number days of renew ===")
            return False

        uom_ids = ProductUom.search([('to_be_renewed', '=', True)])
        if not uom_ids:
            logging.info("=== END: SCHEDULER RENEW SALE ORDERS ===")
            return True

        args = [('order_id.state', 'in',
                 ('not_received', 'draft', 'sale', 'cancel'))]
        categ_ids = ProductCategory.search([('to_be_renewed', '=', True)])
        if not categ_ids:
            logging.info("=== END: SCHEDULER RENEW SALE ORDERS ===")
            return True

        renew_categ_ids = ProductCategory.search(
            [('id', 'child_of', categ_ids.ids),
             ('uom_id', 'in', uom_ids.ids)])

        deadline = datetime.now().date() + timedelta(days=days_to_renew)

        renew_service_ids = self.search(
            [('status', '=', 'active'),
             # ('end_date', '>=', datetime.now().date()),
             ('end_date', '=', deadline),
             ('product_category_id', 'in', renew_categ_ids.ids),
             ('customer_id.company_type', '!=', 'agency')])
        logging.info("=== LIST SERVICES %s ===" % renew_service_ids)
        if not renew_service_ids:
            logging.info("=== END: SCHEDULER RENEW SALE ORDERS ===")
            return True

        product_ids = renew_service_ids.mapped('product_id')
        logging.info("=== PRODUCTS %s ===" % product_ids)
        args += [('product_id', 'in', product_ids.ids)]
        # logging.info("=== ARGS %s ===" % args)

        renew_line_ids = SaleOrderLine.search(args)


        # logging.info("=== SO LINE %s ===" % renew_line_ids)
        # logging.info("=== LIST SO LINE %s ===" % product_ids)

        renewed_product_ids = renew_line_ids.mapped('product_id')
        logging.info("=== PRODUCT BEFORE %s ===" % renewed_product_ids)
        if product_ids and renewed_product_ids:
            all = product_ids.ids
            renew = renewed_product_ids.ids
            nonmatch = list(set(all) - set(renew))
            renewed_product_ids = self.env['product.product'].browse(nonmatch)
        else:
            renewed_product_ids = product_ids
        logging.info("=== PRODUCT AFTER %s ===" % renewed_product_ids)

        if renewed_product_ids:
            renew_service_ids = renew_service_ids.filtered(
                lambda r: r.product_id.id in renewed_product_ids.ids)
        else:
            logging.info("=== END: SCHEDULER RENEW SALE ORDERS ===")
            return True
        logging.info("=== SERVICE %s ===" % renew_service_ids)
        # return True
        # Get Company, Team
        arrs = []
        companys = self.env['res.company'].search([])
        for com in companys:
            dict = {}
            team_count = self.env['crm.team'].search_count([('company_id', '=', com.id), ('type', '=', 'cs')])
            if team_count:
                dict.update({'company_id': com.id, 'team': team_count, 'orders': 0})
                arrs.append(dict)
        logging.info("=== LIST TEAM %s ===" % arrs)

        data = {}
        for service in renew_service_ids:
            # if one of the parent categories has to_be_renewed = True
            customer_id = service.customer_id.id
            vals = {
                'register_type': 'renew',
                'product_category_id': service.product_category_id.id,
                'product_id': service.product_id.id,
                'parent_product_id': service.parent_product_id.id,
                'time': service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name.lower() == u'năm' and 1 or 12,
                'product_uom': service.product_id.uom_id.id,
                'service_status': 'draft',
                'company_id': service.customer_id.company_id.id
            }
            if customer_id not in data:
                # Count Orders for company_id
                for arr in arrs:
                    if arr.get('company_id', 0) == service.customer_id.company_id.id:
                        arr['orders'] += 1
                # create new record for new customer
                data[customer_id] = {
                    'type': 'renewed',
                    'partner_id': customer_id,
                    'state': 'not_received',
                    'date_order': datetime.now(),
                    'order_line': [(0, 0, vals)],
                    'user_id': False,
                    'team_id': False,
                    'company_id': service.customer_id.company_id.id
                }
                # add to order_line in existing record
            else:
                data[customer_id]['order_line'].append((0, 0, vals))
        # Phan bo don hang cho team
        logging.info("=== DATA %s ===" % arrs)
        for arr in arrs:
            store_team = []
            bonus = 0
            sale_teams = self.env['crm.team'].search([('company_id', '=', arr.get('company_id')), ('type', '=', 'cs')])
            if arr.get('team'):
                for team in sale_teams:
                    item = []
                    if bonus < (arr.get('orders') % arr.get('team')):
                        bonus += 1
                        item += [team.id, arr.get('orders') / arr.get('team') + 1]
                    else:
                        item += [team.id, arr.get('orders') / arr.get('team')]
                    store_team.append(item)
            arr.update({'store_team': store_team})
        logging.info("=== DATA AFTER UPDATE TEAM %s ===" % arrs)

        # return True
        # orders = SaleOrder
        logging.info("=== COUNT DATA %s ===" % len(data))
        for index, order in enumerate(data):
            if arrs:
                for item in arrs:
                    flag = False
                    if item.get('company_id') == data[order].get('company_id') and item.get('store_team'):
                        for t in item.get('store_team'):
                            if t[1] > 0:
                                data[order].update({'team_id': t[0]})
                                t[1] -= 1
                                flag = True
                                break
                    if flag:
                        break
            logging.info("=== DATA %s ===" % data[order])
            SaleOrder.with_context(force_company=data[order].get('company_id')).create(data[order])

            # self._cr.commit()
            # orders |= r
            # try:
            #     orders.update_price()
            # except:
            #     continue
        logging.info("=== END: SCHEDULER RENEW SALE ORDERS ===")
        return True

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleService, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                     submenu=submenu)
        if view_type <> 'form':
            return res
        doc = etree.XML(res['arch'])
        check_customer = doc.xpath("//field[@name='customer_id']")
        check_product = doc.xpath("//field[@name='product_id']")
        if check_customer or check_product:
            fields_parent = doc.xpath("//field")
            for node in fields_parent:
                if (self.user_has_groups('base.group_system') or self.user_has_groups('mb_sale_contract.group_operator_mb_sale_contract')) and \
                                node in (check_customer[0], check_product[0]):
                    node.set('options', "{}")
                    setup_modifiers(node)
                elif not self.user_has_groups('base.group_system') and not self.user_has_groups('mb_sale_contract.group_operator_mb_sale_contract') and \
                                node in (check_customer[0], check_product[0]):
                    node.set('options', "{'no_create_edit': True}")
                    setup_modifiers(node)
        res['arch'] = etree.tostring(doc)

        return res
