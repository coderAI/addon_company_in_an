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

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools.float_utils import float_compare
from odoo.osv.orm import setup_modifiers
from odoo.tools.safe_eval import safe_eval
from lxml import etree
import urllib2
import urllib
import json


STATES = [('not_received', 'Not Received'),
          ('draft', 'Quotation'),
          ('sent', 'Sent'),
          ('sale', 'In Progress'),
          ('completed', 'Completed'),
          ('done', 'Locked'),
          ('cancel', 'Cancelled')]
# LIMIT_REQUEST_NUMBER = 4
LIMIT_REQUEST_NUMBER = 100


def encode_orderline(data, k='orderline'):
    res = {}
    for i in range(len(data)):
        for lk, lv in data[i].iteritems():
            line_k = '{}[{}][{}]'.format(k, i, lk)
            res.update({line_k: lv})
    return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # @api.multi
    # @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.payment_ids', 'invoice_ids.payment_ids.state')
    # def _compute_payment_fully_paid(self):
    #     prec = self.env['decimal.precision'].precision_get('Product Price')
    #     for order in self:
    #
    #         # Compute Payments
    #         payments = self.env['account.payment']
    #         for invoice in order.invoice_ids:
    #             if not invoice.payment_ids:
    #                 continue
    #             payments |= invoice.payment_ids
    #         order.account_payment_ids = payments.ids
    #
    #         # Compute fully paid
    #         paid_amount = 0.0
    #         for invoice in order.invoice_ids.filtered(lambda r: r.state == 'paid'):
    #             paid_amount += invoice.amount_total
    #
    #         if order.amount_total:
    #             if float_compare(
    #                 paid_amount, order.amount_total,
    #                     precision_digits=prec) >= 0:
    #                 order.fully_paid = True
    #         else:
    #             if order.invoice_ids and all(invoice.state == 'paid' for
    #                                          invoice in order.invoice_ids):
    #                 order.fully_paid = True
    #
    # @api.multi
    # @api.depends('invoice_ids', 'invoice_ids.state', 'invoice_ids.payment_ids', 'invoice_ids.payment_ids.state')
    # def _compute_invisible_match_payment(self):
    #     for order in self.mappped:
    #         if any(inv.type == "out_invoice" and inv.state not in ('cancel', 'draft') for inv in order.invoice_ids):
    #             order.invisible_match_payment = True
    #         else:
    #             order.invisible_match_payment = False

    coupon = fields.Char('Coupon')
    account_payment_ids = fields.Many2many(
        comodel_name='account.payment',
        column1='sale_order_id',
        column2='payment_id',
        string='Payments',
        compute='_compute_payment_fully_paid',
        readonly=True, store=True)
    fully_paid = fields.Boolean('Fully Paid ?', readonly=True,)
    # compute='_compute_payment_fully_paid', store=True)
    type = fields.Selection(
        [('normal', 'Normal'), ('renewed', 'Renewed')],
        string='Type', default='normal', readonly=True)
    state = fields.Selection(STATES, default='draft')
    partner_id = fields.Many2one(
        states={'not_received': [('readonly', False)],
                'draft': [('readonly', False)],
                'sent': [('readonly', False)]})
    invisible_match_payment = fields.Boolean(
        'Invisible Match Payment', readonly=True,)
    # compute='_compute_invisible_match_payment', store=True)

    @api.multi
    def filter_by_state(self, _state):
        recs = self.filtered(lambda r: r.state == _state)
        return recs

    @api.multi
    def button_got_it(self):
        recs = self.filter_by_state('not_received')
        if recs:
            recs.write({'state': 'draft',
                        'user_id': self.env.uid})

    @api.multi
    def button_completed(self):
        """
            TO DO:
            - Check all related invoices must be paid
            - Change state from In Progress to Completed
        """
        recs = self.filter_by_state('sale')
        for order in recs:
            if any(line.service_status in ('cancel', 'draft')
                   for line in order.order_line) or not order.fully_paid:
                raise Warning(
                    _("Your order cannot be modified before service activation requests are sent"))
        if recs:
            recs.write({'state': 'completed'})

    @api.multi
    def action_done(self):
        """
            TO DO:
            - all sale order lines' status must be different from
            Refused + Draft
            - Change state from Completed to Done
        """
        recs = self.filter_by_state('completed')
        for order in recs:
            if any(line.service_status in ('cancel', 'draft')
                   for line in order.order_line):
                raise Warning(
                    _('In order to done this sales order, all sales order'
                      ' lines must be different from Refused, and Draft.!'))
        return super(SaleOrder, recs).action_done()

    @api.multi
    def create_invoice_and_reupdate_account_journal(self):
        self.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'cancel')).unlink()
        invoice_id = self.with_context(force_company=self.partner_id.company_id.id).action_invoice_create()
        invoice_obj = self.env['account.invoice'].browse(invoice_id[0])
        if self.env.user.company_id <> self.partner_id.company_id:
            domain = [
                ('type', '=', 'sale'),
                ('company_id', '=', self.partner_id.company_id.id),
            ]
            journal_id = self.env['account.journal'].search(domain, limit=1)
            invoice_obj.write({
                'journal_id': journal_id.id,
                'account_id': self.partner_id.property_account_receivable_id and self.partner_id.with_context(
                    force_company=self.partner_id.company_id.id).property_account_receivable_id.id
            })
            if invoice_obj.tax_line_ids:
                for line in invoice_obj.tax_line_ids:
                    tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                          ('amount', '=', line.tax_id.amount),
                                                          ('type_tax_use', '=', 'sale'),
                                                          ('company_id', '=', self.partner_id.company_id.id)],
                                                         limit=1)
                    line.write({
                        'account_id': tax.account_id.id
                    })
        return invoice_id


    @api.multi
    def get_line_values(self, line):
        complete_name = line.product_category_id.complete_name and \
                        line.product_category_id.complete_name.replace(
                            " / ", "/").encode("utf-8") or ''
        line_data = {
            'oderlineid': line.id,
            'register_type': line.register_type,
            'product_category_code': line.product_category_id.code,
            'categ_name': complete_name,
            'product_code': line.product_id.default_code and
                            line.product_id.default_code.encode("utf-8") or '',
            'product_name': line.product_id.name and
                            line.product_id.name.encode("utf-8") or '',
            'qty': int(line.time),
            'uom': line.product_uom.name.encode("utf-8"),
            'parent_product_code': line.parent_product_id and
                                   line.parent_product_id.default_code or '',
            'parent_product_name': line.parent_product_id and
                                   line.parent_product_id.name or '',
            'discount': line.discount,
        }
        return line_data

    @api.multi
    def update_price(self):
        """
            TO DO:
            - Call Mat Bao API to get services prices
        """
        for order in self:
            data = {'name': order.name,
                    'coupon': order.coupon
                    }
            order_lines = []
            count = 0
            index = 0
            for line in order.order_line.filtered(lambda l: l.register_type <> 'upgrade'):
                # complete_name = line.product_category_id.complete_name and \
                #     line.product_category_id.complete_name.replace(
                #         " / ", "/").encode("utf-8") or ''
                # line_data = {
                #     'oderlineid': line.id,
                #     'register_type': line.register_type,
                #     'product_category_code': line.product_category_id.code,
                #     'categ_name': complete_name,
                #     'product_code': line.product_id.default_code and
                #     line.product_id.default_code.encode("utf-8") or '',
                #     'product_name': line.product_id.name and
                #     line.product_id.name.encode("utf-8") or '',
                #     'qty': int(line.time),
                #     'uom': line.product_uom.name.encode("utf-8"),
                #     'parent_product_code': line.parent_product_id and
                #     line.parent_product_id.default_code or '',
                #     'parent_product_name': line.parent_product_id and
                #     line.parent_product_id.name or '',
                #     'discount': line.discount,
                #              }
                line_data = self.get_line_values(line)
                if count >= LIMIT_REQUEST_NUMBER:
                    order_lines.append([line_data])
                    count = 0
                    index += 1
                else:
                    if order_lines:
                        order_lines[index].append(line_data)
                    else:
                        order_lines.append([line_data])
                    count += 1
            for order_line in order_lines:
                lines = encode_orderline(order_line)
                request_data = data.copy()
                request_data.update(lines)
                url_values = urllib.urlencode(request_data)
                url = self.env['ir.values'].get_default(
                    'sale.config.settings', 'url')
                if not url:
                    raise Warning(_(
                        "Please set the API URL at menu Sale --> Configuration"
                        " --> Settings --> URL"))
                # # Get Method
                # full_url = url + '/?' + url_values
                # res_data = urllib2.urlopen(full_url)
                # res_data = res_data.read()

                # Post Method
                # Case when 1
                # url = 'http://172.26.1.208:1239/api/values'
                req = urllib2.Request(url, url_values)
                response = urllib2.urlopen(req)
                res_data = response.read()
                # Case when 2
                # r = requests.post(url, request_data)
                ##################

                res_data = json.loads(res_data)
                if res_data['code'] == '0':
                    raise Warning(_(res_data['msg']))

                so_lines = res_data['OrderLine']
                for res in so_lines:
                    if res['oderlineid'] not in order.order_line.filtered(lambda l: l.register_type <> 'upgrade').ids:
                        continue
                    line = self.env['sale.order.line'].browse(res['oderlineid'])
                    line.register_untaxed_price = res['reg_price_wot']
                    line.register_taxed_price = res['reg_price_wt']
                    line.register_taxed_amount = res['reg_tax_amount']
                    line.renew_untaxed_price = res['ren_price_wot']
                    line.renew_taxed_price = res['ren_price_wt']
                    line.renew_taxed_amount = res['ren_tax_amount']
                    line.price_total = res['sub_total']
                    tax = self.env['account.tax'].search(
                        [('type_tax_use', '=', 'sale'),
                         ('amount', '=', res['tax']),
                         ('company_id', '=', order.company_id.id)], limit=1)
                    line.tax_id = tax
            order.order_line.filtered(lambda l: l.register_type <> 'upgrade').write({'price_updated': True})

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        result = super(SaleOrder, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type != 'form':
            return result

        doc = etree.XML(result['arch'])

        except_fields = ['attachments', 'date_order', 'note', 'contract_note', 'tracking_number', 'vendor', 'payment_method_contract', 'req_inv_date']
        except_specail_fields = ['partner_id']

        button_add_service = str(self.env.ref(
            'matbao_module.action_service_order_lines_wizard').id)
        button_add_addon = str(self.env.ref(
            'matbao_module.action_addon_order_lines_wizard').id)
        invisible_buttons = [button_add_service, button_add_addon]

        check_state = doc.xpath("//field[@name='state']")
        if check_state:
            args = ('state', 'in', ('sale', 'completed', 'done', 'cancel', 'not_received'))
            args_specail = ('state', 'in', ('sale', 'paid', 'completed', 'done', 'cancel', 'not_received'))
            fields_to_readonly = doc.xpath("//field")
            for node in fields_to_readonly:
                if node.get('name') == 'state' or \
                        node.get('name') in except_fields:
                    continue
                if node.get('modifiers'):
                    modif = {}
                    try:
                        modif = node.get('modifiers')
                        modif = modif.replace('true', 'True')
                        modif = modif.replace('false', 'False')
                        modif = safe_eval(modif)
                    except:
                        modif = {}
                    if modif.get('readonly') is True:
                        continue
                attrs = {}
                if node.get('attrs'):
                    attrs = safe_eval(node.get('attrs'))
                if 'readonly' in attrs and \
                        isinstance(attrs['readonly'], (list, tuple)):
                    attrs['readonly'] = [
                         '|', args, '&'] + attrs['readonly']
                else:
                    if node.get('name') in except_specail_fields:
                        attrs.update({'readonly': [args_specail]})
                    else:
                        attrs.update({'readonly': [args]})
                node.set('attrs', str(attrs))
                setup_modifiers(node)

            buttons_to_readonly = doc.xpath("//button")
            buttons_to_readonly = [button for button in buttons_to_readonly
                                   if button.get('name') in invisible_buttons]
            for node in buttons_to_readonly:
                attrs = {}
                if node.get('attrs'):
                    attrs = safe_eval(node.get('attrs'))
                if 'invisible' in attrs and \
                        isinstance(attrs['invisible'], (list, tuple)):
                    attrs['invisible'] = [
                            '|', args, '&'] + attrs['invisible']
                else:
                    attrs.update({'invisible': [args]})
                node.set('attrs', str(attrs))
                setup_modifiers(node)
        result['arch'] = etree.tostring(doc)
        return result

    def _prepare_invoice_line_vals(self, register_type, price_unit, taxes_amount=0, tax_ids=[(6, 0, [])], time=1):
        vals = {
                'time': time,
                'register_type': register_type,
                'price_unit': price_unit,
                'taxes_amount': taxes_amount,
                'invoice_line_tax_ids': tax_ids
                }
        return vals

    def _create_invoice_lines(self, invoice_line, vals, is_copy):
        if is_copy:
            invoice_line.copy(vals)
        else:
            invoice_line.write(vals)
        return True

    @api.multi
    def check_promotion_discount_for(self,vals,order_line,field_name):
        return vals

    @api.multi
    def support_action_invoice_create(self,invoice_ids):
        # """
        #     TO DO:
        #     - register_type = 'register' and Time > 1: 2 invoice lines
        #     - register_type = 'register' and Time = 1: only 1 invoice line
        #     - Two prices for one sales order line Taxed price and
        #         Untaxed price: 2 invoice lines
        #     - Register Type is Renew/Transfer,
        #         Time is equal or larger than 1: only one
        # """
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        invoice_line_old= []
        for invoice_line in invoice.invoice_line_ids:
            order_line = invoice_line.sale_line_ids
            is_copy = False
            cac =False
            vals_list=[]

            if order_line.register_taxed_price:
                # Register Taxed price
                cac = True
                vals = self._prepare_invoice_line_vals(
                    'register',
                    order_line.register_taxed_price,
                    taxes_amount=order_line.register_taxed_amount,
                    tax_ids=[(6, 0, order_line.tax_id and
                              order_line.tax_id.ids or [])])
                vals = self.check_promotion_discount_for(vals, order_line, 'register_taxed_price')
                vals.update({
                    'sale_line_ids': [(6, 0, [order_line.id])]
                })
                vals_list.append(vals)

            if order_line.register_untaxed_price:
                # Register Un-taxed price
                cac = True
                vals = self._prepare_invoice_line_vals(
                    'register',
                    order_line.register_untaxed_price)
                vals.update({
                    'discount_amount':0,
                    'sale_line_ids': [(6, 0, [order_line.id])]
                })
                vals_list.append(vals)
            #snow check
            # Renews /Transfers
            register_type = order_line.register_type == 'register' and \
                            'renew' or order_line.register_type
            if order_line.renew_taxed_price:
                # Renew /Transfer Taxed price
                cac = True
                vals = self._prepare_invoice_line_vals(
                    register_type,
                    order_line.renew_taxed_price + order_line.up_price, #+ order_line.refund_amount,
                    taxes_amount=order_line.renew_taxed_amount,
                    tax_ids=[(6, 0, order_line.tax_id and
                              order_line.tax_id.ids or [])],
                    time=(register_type == 'register' and 1 or order_line.time))
                vals = self.check_promotion_discount_for(vals, order_line, 'renew_taxed_price')
                vals.update({
                    'sale_line_ids': [(6, 0, [order_line.id])]
                })
                vals_list.append(vals)

            if order_line.renew_untaxed_price:
                # Renew /Transfer Taxed price
                cac = True
                vals = self._prepare_invoice_line_vals(
                    register_type,
                    order_line.renew_untaxed_price, time=(register_type == 'register' and 1 or order_line.time))
                vals.update({
                    'discount_amount': 0,
                    'sale_line_ids': [(6, 0, [order_line.id])]
                })
                vals_list.append(vals)

            if cac == False:
                vals = self._prepare_invoice_line_vals(
                    register_type,
                    order_line.price_subtotal_no_discount, time=(register_type == 'register' and 1 or order_line.time), tax_ids=[(6, 0, order_line.tax_id and
                              order_line.tax_id.ids or [])])
                vals = self.check_promotion_discount_for(vals, order_line, 'renew_taxed_price')
                vals.update({
                    'sale_line_ids': [(6, 0, [order_line.id])]
                })
                vals_list.append(vals)
            createdata={
                'invoice_line':invoice_line,
                'vals_list':vals_list,
            }
            invoice_line_old.append(createdata)

           # invoice_line.unlink()
        for i in invoice_line_old:
            Fist= False
            for create_i in i.get('vals_list'):
                Fist= self._create_invoice_lines(i.get('invoice_line'), create_i, Fist)

        invoice.compute_taxes()
        return invoice_ids

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super(SaleOrder, self).action_invoice_create()
        self.support_action_invoice_create(invoice_ids)
        return invoice_ids

    @api.multi
    def action_confirm(self):
        for order in self:
            # if order.partner_id.state == 'draft' and self.env.user.id <> SUPERUSER_ID:
            #     raise Warning(_("Please submit customer to operation!"))
            if any(line.price_updated is False for line in order.order_line):
                raise Warning(_(
                    "Please update price before confirming the sales order!"))
        return super(SaleOrder, self).action_confirm()
