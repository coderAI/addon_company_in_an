# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
import logging
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
from datetime import datetime
import json
NAME='Tên miền'

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def productemplate_link(self):


        form_view_id = self.env['ir.model.data'].xmlid_to_res_id('product.product_template_only_form_view')
        return {
            'name': _('product template'),
            'view_mode': 'form',
            'view_id': form_view_id,
            "res_model": "product.template",
            "context": {"create": False, },
            'type': 'ir.actions.act_window',
            'res_id': self.product_tmpl_id.id
        }


    @api.model
    def check_domain_sale(self,domain):
        data='false'
        res={'"code"': 200, '"messages"': '"Successfully"'}

        product_category_obj = self.env['product.category']
        sale_serviec_obj = self.env['sale.service']
        product_category_data = product_category_obj.sudo().search([('name', '=', NAME)], limit=1)
        if product_category_data.id:
            product_category_list=[]
            product_category_list_first = product_category_obj.sudo().search([('parent_id', '=', product_category_data.id)]).ids
            product_category_list_second = product_category_obj.sudo().search([('parent_id','in', product_category_list_first)]).ids
            product_category_list.extend(product_category_list_first)
            product_category_list.extend(product_category_list_second)
            product_category_list.append(product_category_data.id)
            product_data = self.sudo().search([('name', '=', domain),('categ_id','in',product_category_list)], limit=1)
            if product_data.id:
                sale_serviec_list = sale_serviec_obj.search([('product_id', '=', product_data.id)], limit=1)
                if sale_serviec_list.id:
                    data = 'true'
        res.update({'"data"':data})
        return res

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def get_product_category_info(self, product_code=None):
        code = 200
        messages = 'Successfully'

        res = {'code': code, 'messages': messages, 'data':self.sudo().search([('code', '=', product_code)],limit=1).ids}
        return json.dumps(res)

    @api.model
    def get_all_rec_info(self,context = ''):
        code = 200
        messages = 'Successfully'

        data = self.sudo().search([]).read()
        res = {'code': code, 'messages': messages, 'data':data}
        return json.dumps(res)


    @api.model
    def get_product_upgrade(self, product_code=None):
        data={}
        list_data=[]
        if product_code:
            product_data = self.sudo().search([('code','=',product_code)])
            for i in product_data.mb_product_category_ids:
                line={
                        'name':i.name,
                        'erm_code':i.erm_code,
                        'code':i.code,
                        'sold':i.sold,
                        'setup_price_mb':i.setup_price_mb,
                        'renew_price_mb':i.renew_price_mb,
                        'transfer_price_mb':i.transfer_price_mb,
                        'promotion_register_price':i.promotion_register_price,
                        'promotion_renew_price':i.promotion_renew_price,
                        'default_tax':i.default_tax,
                      }

                list_data.append(line)
        return {'"code"': 200, '"msg"': '"Successfully"', '"data"': json.dumps(list_data)}



class SaleOrder(models.Model):
    _inherit = 'sale.order.line'


    @api.model
    def create_sol_new(self, so_id=0, values=[]):
        code = 200
        messages = 'Successfully'
        so = self.env['sale.order'].search([('id','=',so_id)],limit=1)
        wizard_obj=so.env['service.addon.order.lines.wizard']
        line_wizard_obj=so.env['order.lines.wizard']
        wizard = wizard_obj.with_context(active_id=so.id).create({})
        for value in values:
            value.update({'parent_id':wizard.id})
            line_wizard_obj.create(value)
        wizard.with_context(active_model='sale.order',active_id=so.id,sale_order_id= so.id).write_service_orders()

        res = {'code': code, 'messages': messages, 'data': so.order_line.ids}
        return json.dumps(res)

    @api.model
    def delete_sol_new(self, sol_id):
        code = 200
        messages = 'Successfully'
        self.search([('id','=',sol_id)],limit=1).unlink()
        res = {'code': code, 'messages': messages}
        return json.dumps(res)

    @api.model
    def edit_sol_new(self, sol_id,values):
        code = 200
        messages = 'Successfully'
        sol = self.search([('id','=',sol_id)],limit=1)
        sol.write(values)
        res = {'code': code, 'messages': messages}
        return json.dumps(res)

class ExternalSO(models.AbstractModel):

    _inherit = 'external.so'

    @api.model
    def create_so_and_invoice_new(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[], source='',):

        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']
        ResPartner = self.env['res.partner']
        # variables
        error_msg = ''
        order_type = order_type
        team_id = False

        if not name:
            return {'"code"': 0, '"msg"': '"Order name could not be empty"',
                    '"data"': {}}
        else:
            if name.upper() == 'ID':
                # name = self.env['ir.sequence'].next_by_code('id.sale.order') or '/'
                name = self.get_ref_partner()
            else:
                order = SaleOrder.search([('name', '=', name)], limit=1)
                if order:
                    return {'"code"': 0, '"msg"': '"Order name already exits"',
                            '"data"': {}}

        if not date_order:
            return {'"code"': 0, '"msg"': '"Order Date could not be empty"',
                    'data': {}}
        if not company_id:
            return {'"code"': 0, '"msg"': '"Company ID could not be empty"',
                    '"data"': {}}
        if source:
            source_id = self.env['utm.source'].search([('name', '=', source)])
        else:
            source_id = False
        if not order_type or order_type not in ['normal', 'renewed', 'mbn', 'id', 'chili']:
            return {'"code"': 0,
                    '"msg"': '"Order Type must be `normal`, `renewed`, `mbn`, `chili` or `id`"',
                    '"data"': {}}
        if not customer:
            return {'"code"': 0, '"msg"': '"Customer info could not be empty"',
                    '"data"': {}}
        customer_id = ResPartner.search([('ref', '=', customer)], limit=1)
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not exists."', 'data': {}}

        if not status or status not in ('draft', 'not_received', 'sale', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                             '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'"code"': 0, '"msg"': '"Order detail could not be empty"',
                    '"data"': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + timedelta(hours=-7)
        except ValueError:
            return {'"code"': 0, '"msg"': '"Invalid order date yyyy-mm-dd h:m:s"',
                    '"data"': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'"code': 0,
                        '"msg"': '"Saleteam {} is not found"'.format(saleteam_code),
                        '"data"': {}}
        try:
            # Prepare Order lines:
            order_lines = self.with_context(force_company=customer_id.company_id.id).create_order_lines(lines)
            if order_lines['msg']:
                error_msg += order_lines['msg']

            if error_msg:
                return {'"code"': 0, '"msg"': error_msg, '"data"': {}}

            so_vals = {'partner_id': customer_id.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       'state': status or 'sale',
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id and company_id == customer_id.company_id.id and company_id or customer_id.company_id.id,
                       'source_id': source_id and source_id.id or False,
                       'order_line': order_lines['line_ids']
                       }
            order = SaleOrder.with_context(force_company=customer_id.company_id.id).create(so_vals)

            order.write({
                'original_subtotal': order.amount_untaxed,
                'original_total': order.amount_total,
            })
            if customer_id.company_type != 'agency':
                order.update_price_by_odoo()
            return {'"code"': 1, '"msg"': '"Create Order %s and Invoice Successful!"' % order.name, '"invoice_id"': ''}
        except ValueError:
            return {'"code"': 0, '"msg"': '"Unknow Error!"', '"data"': {}}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def cancel_so_agency(self, so_ids=[]):
        code = 200
        logging.info(so_ids)
        messages = 'Successfully'
        user_cancel_so = 1
        date_cancel_so = datetime.now()
        for so_id in so_ids:
            order_id = self.browse(so_id)
            order_id.date_cancel_so=date_cancel_so
            order_id.user_cancel_so=user_cancel_so
            order_id.action_cancel()
        res = {'code': code, 'messages': messages}
        return json.dumps(res)


    @api.model
    def apply_coupon_text(self, so_id,coupon_text=''):
        code = 200
        messages = 'Successfully'
        so = self.browse(so_id)
        so.coupon = coupon_text
        res = {'code': code, 'messages': messages}
        return json.dumps(res)

    @api.model
    def update_price_by_odoo_api_call(self, so_id):
        code = 200
        messages = 'Successfully'
        self.browse(so_id).update_price_by_odoo()
        res = {'code': code, 'messages': messages}
        return json.dumps(res)


    def convert_order_lines_new(self, vals):

        ProductProduct = self.env['product.product']
        ProductCategory = self.env['product.category']
        AccountTax = self.env['account.tax']

        order_lines = []
        for line in vals:
            parent_product = False
            product_categ = ProductCategory.search(
                [('code', '=', line.get('categ_code'))],limit = 1)
            if line.get('product_code'):
                product_ids = ProductProduct.search([('default_code', '=', line.get('product_code'))], limit=1)
            else:
                product_code = self.env['ir.sequence'].next_by_code('product.product')
                product_name = self.env['external.so']._convert_str(line.get('product_name'))
                new_product_vals = {
                    'default_code': product_code,
                    'name': product_name,
                    'uom_id': line.get('product_uom'),
                    'uom_po_id': line.get('product_uom'),
                    'categ_id': product_categ.id,
                    'minimum_register_time':
                        product_categ.minimum_register_time,
                    'billing_cycle': product_categ.billing_cycle,
                    'type': 'service'
                }
                product_ids = ProductProduct.create(new_product_vals)
            tax_id = AccountTax.with_context(force_company=line.get('company_id')).search([
                ('amount', '=', float(line.get('tax'))), ('type_tax_use', '=', 'sale'), ('company_id', '=', line.get('company_id'))], limit=1)

            if line.get('parent_product_code', False):
                parent_product = ProductProduct.search([
                    ('default_code', '=',
                     line.get('parent_product_code'))], limit=1).id

            line.update({
                'price_updated': False,
                'product_id': product_ids.id,
                'parent_product_id': parent_product,
                'product_category_id': product_categ.id,
                'tax_id': tax_id and [(6, 0, [tax_id.id])] or False,
                })
            order_lines.append((0, 0, line))

        return order_lines




    @api.model
    def create_sale_order_new(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[], source='',):

        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']
        ResPartner = self.env['res.partner']
        code = 200
        messages = 'Successfully'
        data=[]
        order_type = order_type
        team_id = False
        if name.upper() == 'ID':
            name = self.env['external.so'].get_ref_partner()

        if source:
            source_id = self.env['utm.source'].search([('name', '=', source)],limit =1)
        else:
            source_id = False


        customer_id = ResPartner.search([('ref', '=', customer)], limit=1)

        try:
            date_order = datetime.strptime(date_order, DTF) + timedelta(hours=-7)
        except ValueError:
            messages = "Invalid order date yyyy-mm-dd h:m:s"
            code=403


        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                messages = "Saleteam is not found"
                code = 403


        if code == 200:
            so_vals = {'partner_id': customer_id.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       'state': status or 'sale',
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id and company_id == customer_id.company_id.id and company_id or customer_id.company_id.id,
                       'source_id': source_id and source_id.id or False,
                       'order_line': self.convert_order_lines_new(lines)
                       }
            order = SaleOrder.with_context(force_company=customer_id.company_id.id).create(so_vals)

            order.update_price_by_odoo()
        res = {'code': code, 'messages': messages, 'data': order.name}
        return json.dumps(res)









    @api.model
    def add_sale_order_line_new(self, so_id, vals={}):
        code = 200
        messages = 'Successfully'
        data=[]
        order_id = self.browse(so_id)
        if order_id:
            if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
                messages= "Invoice have validated or paid, can not update line."
                code = 403
            order_lines = self.convert_order_lines_new(vals)
            order_id.write({'order_line': order_lines})
            data = order_id.order_line.ids
            order_id.update_price_by_odoo()
            self.env['external.so'].update_original_fields(order_id)
        res = {'code': code, 'messages': messages, 'data':data}
        return json.dumps(res)


    @api.model
    def check_cannot_renew_product(self, so_id):
        code = 200
        messages = 'Successfully'
        data=''
        pp_obj = self.env['product.product']
        ss_obj = self.env['sale.service']

        for i_so in self.browse(so_id):
            if data == True:
                break
            for i_soline in i_so.order_line:
                if i_soline.product_id:
                    if i_soline.product_id.categ_id.can_be_renew:
                        for i_ss in ss_obj.search([('product_id','=',i_soline.product_id.id)]):
                            if i_ss.is_stop:
                                if i_ss.is_stop ==True:
                                    data = i_soline.product_id.default_code
                    else:
                        data = i_soline.product_id.default_code
        res = {'code': code, 'messages': messages, 'data':data}
        return json.dumps(res)


    @api.model
    def get_so_info(self, so_id):
        code = 200
        messages = 'Successfully'
        data=[]
        for i_so in self.browse(so_id):
            so={}
            line=[]
            for i_soline in i_so.order_line:
                line.append(i_soline.read()[0])
            so.update(i_so.read()[0])
            so.update({'order_line_info':line})
            data.append(so)

        res = {'code': code, 'messages': messages, 'data':data}
        return json.dumps(res)


    @api.model
    def check_export_by_so(self, so_id):
        code = 200

        messages = 'Successfully'
        data=False
        for i_so in self.browse(so_id):
            if i_so.temp_approve:
                data = True
            else:
                for inv in i_so.invoice_ids.filtered(lambda inv: inv.state != 'cancel'):
                    for inv_line in inv.invoice_line_ids:
                        if inv_line.export_id:
                            data = True

        res = {'code': code, 'messages': messages, 'data':data}
        return json.dumps(res)



    @api.model
    def create_invoice_to_ready_payment(self, so_id):
        code = 200
        messages = 'Successfully'
        SaleOrder = self.env['sale.order']
        mb_coupon_obj = self.env['mb.coupon']
        order = SaleOrder.browse(so_id)
        logging.info(order.coupon)
        condition_messages , condition_code = mb_coupon_obj.check_coupon_action(order.coupon,order.partner_id.ref)
        if condition_code != 200:
            res = {'code': 301, 'messages': condition_messages, 'data': ''}
            return json.dumps(res)
        order.update_price_by_odoo()
        invoice_id = False
        check_export_invoice = False
        for inv in order.invoice_ids.filtered(lambda inv: inv.state != 'cancel'):
            for inv_line in inv.invoice_line_ids:
                if inv_line.export_id:
                    if order.amount_total != inv.amount_total:
                        check_export_invoice = True
                    else:
                        check_export_invoice = True
                        invoice_id = inv.id
        if check_export_invoice:
            if invoice_id == False:
                messages = 'can not create invoice'
                code = 403
                invoice_id = ''
        else:
            order.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'cancel')).unlink()
            order.update_price_by_odoo()
            if order.state != 'sale':
                order.action_confirm()
            invoice = order.with_context(force_company=order.partner_id.company_id.id).action_invoice_create()
            invoice_id = self.env['account.invoice'].browse(invoice)
            if self.env.user.company_id <> order.partner_id.company_id:
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', order.partner_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                invoice_id.write({
                    'journal_id': journal_id.id,
                    'account_id': order.partner_id.property_account_receivable_id and order.partner_id.with_context(
                        force_company=order.partner_id.company_id.id).property_account_receivable_id.id
                })
                if invoice_id.tax_line_ids:
                    for line in invoice_id.tax_line_ids:
                        tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                              ('amount', '=', line.tax_id.amount),
                                                              ('type_tax_use', '=', 'sale'), (
                                                                  'company_id', '=',
                                                                  order.partner_id.company_id.id)], limit=1)
                        line.write({
                            'account_id': tax.account_id.id
                        })

        res = {'code': code, 'messages': messages, 'data': invoice}
        return json.dumps(res)


    @api.multi
    def check_valid_promotion_check(self):
        coupon_id = self.env['mb.coupon'].search([('name', '=', self.coupon.strip())])
        promotion_group = ''
        mes = ''
        if not coupon_id:
            mes += ' not coupon'
            mes = True
        if not coupon_id.promotion_id.is_promotion_account_amount and \
                not coupon_id.promotion_id.is_promotion_account_percent:
            mes += ' not is_promotion_account_percent'
            mes = True
        match, promotion_group, count = False, [], 0
        count_order = self.env['sale.order'].sudo().search_count([('fully_paid', '=', True),
                                                                  ('coupon', '=', self.coupon.strip())])
        if count_order > coupon_id.max_used_time:
            mes += ' coupon max_used_time not correct'
            mes = True
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > coupon_id.expired_date:
            mes += 'coupon expired_date not correct'
            mes = True
        promotion_id = coupon_id.promotion_id
        if promotion_id.status <> 'run':
            mes += ' promotion_id status not correct'
            mes = True
        if promotion_id.date_from > datetime.now().strftime('%Y-%m-%d %H:%M:%S') or \
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S') > promotion_id.date_to:
            mes += 'promotion_id date_from or date_to not correct'
            mes = True
        # Check A Customer only used once
        if promotion_id.only_used_once:
            order_ids = self.search_count([('partner_id', '=', self.partner_id.id),
                                           ('coupon', '=', self.coupon.strip()),
                                           ('fully_paid', '=', True),
                                           ('state', 'not in', ('cancel',))])
            if order_ids >= 1:
                mes += ' 2 sale ussing this coupon'
                mes = True
        # Check Total Product Discount
        if promotion_id.is_total_product_discount and len(promotion_id.total_product_discount) > 0:
            for item in promotion_id.total_product_discount:
                category_ids = self.env['product.category'].search([('id', 'child_of', item.product_category_id.id)])
                domain = [('product_category_id', 'in', category_ids.ids),
                          ('order_id.fully_paid', '=', True),
                          ('order_id.coupon', 'in', promotion_id.coupon_ids.mapped('name'))]
                if promotion_id.is_register_type and promotion_id.register_type:
                    domain.append(('register_type', 'in', promotion_id.register_type.mapped('code')))
                order_line_ids = self.env['sale.order.line'].search_count(domain)
                order_count_service = self.order_line.filtered(
                    lambda l: l.product_category_id in category_ids)
                if promotion_id.is_register_type and promotion_id.register_type:
                    order_count_service = order_count_service.filtered(
                        lambda l: l.register_type in promotion_id.register_type.mapped('code'))
                if order_line_ids + len(order_count_service) > item.total:
                    mes += ' Fail when Check Total Product Discount'
                    mes = True
        pass_line = []
        order_line_temp = self.order_line
        if promotion_id.type == 'and':
            for line in self.order_line:
                if line in pass_line:
                    continue
                temp = []
                match = False
                # Danh dau da duyet qua trong cac dieu kien, True neu thoa dieu kien truoc, False neu chua duyet dieu kien hoac khong thoa dieu kien
                flag = False
                # Check condition Total Amount Sale Order
                if promotion_id.is_amount_order and promotion_id.period_total_amount_order > 0:
                    if self.amount_untaxed < promotion_id.period_total_amount_order:
                        mes += ' amount_untaxed < period_total_amount_order'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Order Type
                if promotion_id.is_order_type and promotion_id.order_type:
                    if self.type not in [t.code for t in promotion_id.order_type]:
                        mes += ' Sale order type not in promotion_id.order_type'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Customer Type
                if promotion_id.is_customer_type and promotion_id.customer_type:
                    if self.partner_id.company_type not in [t.code for t in promotion_id.customer_type]:
                        mes += ' Fail Check Customer Type'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Customer in List
                if promotion_id.is_list_customer and promotion_id.customer_ids:
                    if self.partner_id not in promotion_id.customer_ids:
                        mes += ' Fail Check Customer in List'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Customer Email
                if promotion_id.is_customer_email and promotion_id.customer_email:
                    if self.partner_id.email not in promotion_id.customer_email.mapped('email'):
                        mes += ' Fail Check Customer Email'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Customer Level
                if promotion_id.is_customer_level and promotion_id.customer_level:
                    if self.partner_id.level not in [t.code for t in promotion_id.customer_level]:
                        mes += ' Fail Check Customer Level'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Register Type
                if promotion_id.is_register_type and promotion_id.register_type:
                    if line.register_type not in [t.code for t in promotion_id.register_type]:
                        continue
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Count Product
                if promotion_id.is_count_product and promotion_id.count_product:
                    if promotion_id.is_register_type and promotion_id.register_type:
                        if promotion_id.product_category_type and promotion_id.promotion_product_category:
                            count_line = self.order_line.filtered(
                                lambda l: l.product_category_id in self.get_product_category(
                                    promotion_id.promotion_product_category) and l.register_type in
                                                                                 [t.code for t in
                                                                                  promotion_id.register_type])
                            if len(count_line) < promotion_id.count_product:
                                mes += ' Fail Check Count all Product'
                                mes = True
                        if promotion_id.register_time_type and promotion_id.promotion_register_time:
                            count_line = 0
                            for li in promotion_id.promotion_register_time:
                                count_line += len(self.order_line.filtered(
                                    lambda l: l.product_category_id in self.get_product_category(li.product_category_id)
                                              and l.time >= li.month_from))
                            if count_line < promotion_id.count_product:
                                mes += ' Fail Check Count register_time Product'
                                mes = True
                        if promotion_id.is_amount_product and promotion_id.promotion_amount_product:
                            count_line = 0
                            for li in promotion_id.promotion_amount_product:
                                count_line += len(self.order_line.filtered(
                                    lambda l: l.product_category_id in self.get_product_category(li.product_category_id)
                                              and l.price_subtotal >= li.amount))
                            if count_line < promotion_id.count_product:
                                mes += ' Fail Check Count promotion_amount_product Product'
                                mes = True
                    if promotion_id.is_register_type and promotion_id.register_type and len(self.order_line.filtered(
                            lambda l: l.register_type in promotion_id.register_type.mapped(
                                'code'))) < promotion_id.count_product:
                        mes += ' Fail Check Count register_type Product'
                        mes = True
                    if len(self.order_line) < promotion_id.count_product:
                        mes += ' Fail len(order_line) < promotion_id.count_product'
                        mes = True
                    if line not in pass_line:
                        match = True
                        temp.append(line)
                # Check Product Category
                if promotion_id.product_category_type and promotion_id.promotion_product_category:
                    product_category_ids = self.get_product_category(promotion_id.promotion_product_category)
                    if line.product_category_id not in product_category_ids:
                        continue
                    if line not in temp:
                        temp.append(line)
                    match = True
                    flag = True
                    if promotion_id.product_category_type == 'and':
                        match, temp = self.check_product_category(promotion_id, temp, self.order_line.filtered(
                            lambda l: l not in pass_line))
                    if not match:
                        break
                # Check Register Time
                if promotion_id.register_time_type and promotion_id.promotion_register_time:
                    if line not in temp:
                        temp.append(line)
                    match, temp = self.check_register_time(promotion_id, temp,
                                                           self.order_line.filtered(lambda l: l not in pass_line), flag)
                    if not match:
                        continue
                    flag = True
                # Check Amount Product
                if promotion_id.is_amount_product and promotion_id.promotion_amount_product:
                    if line not in temp:
                        temp.append(line)
                    match, temp = self.check_amount_product(promotion_id, temp,
                                                            self.order_line.filtered(lambda l: l not in pass_line),
                                                            flag)
                    if not match:
                        continue
                if match:
                    promotion_group.append(temp)
                    for item in temp:
                        order_line_temp -= item
                        if item not in pass_line:
                            pass_line.append(item)
        else:
            for line in self.order_line:
                if line in pass_line:
                    continue
                temp = [line]
                # Check condition Total Amount Sale Order
                if promotion_id.is_amount_order and promotion_id.period_total_amount_order > 0:
                    if self.amount_untaxed >= promotion_id.period_total_amount_order:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Customer Type
                if promotion_id.is_customer_type and promotion_id.customer_type:
                    if self.partner_id.company_type in [t.code for t in promotion_id.customer_type]:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Order Type
                if promotion_id.is_order_type and promotion_id.order_type:
                    if self.type in [t.code for t in promotion_id.order_type]:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check List Customer
                if promotion_id.is_list_customer and promotion_id.customer_ids:
                    if self.partner_id in promotion_id.customer_ids:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Customer Email
                if promotion_id.is_customer_email and promotion_id.customer_email:
                    if self.partner_id.email in promotion_id.customer_email.mapped('email'):
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Customer Level
                if promotion_id.is_customer_level and promotion_id.customer_level:
                    if self.partner_id.level in [t.code for t in promotion_id.customer_level]:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Register Type
                if promotion_id.is_register_type and promotion_id.register_type:
                    if line.register_type in [t.code for t in promotion_id.register_type]:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Count Product
                if promotion_id.is_count_product and promotion_id.count_product:
                    if promotion_id.is_register_type and promotion_id.register_type and len(self.order_line.filtered(
                            lambda l: l.register_type in promotion_id.register_type.mapped(
                                'code'))) >= promotion_id.count_product:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                    if len(self.order_line) >= promotion_id.count_product:
                        promotion_group.append(temp)
                        for item in temp:
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check condition Product Category
                if promotion_id.product_category_type and promotion_id.promotion_product_category:
                    if line.product_category_id in self.get_product_category(promotion_id.promotion_product_category):
                        if promotion_id.product_category_type == 'or':
                            match = True
                            promotion_group.append(temp)
                            for item in temp:
                                order_line_temp -= item
                                if item not in pass_line:
                                    pass_line.append(item)
                            continue
                        if promotion_id.product_category_type == 'and':
                            match, temp = self.check_product_category(promotion_id, temp, self.order_line.filtered(
                                lambda l: l not in pass_line))
                            if match:
                                promotion_group.append(temp)
                                for item in temp:
                                    order_line_temp -= item
                                    if item not in pass_line:
                                        pass_line.append(item)
                                continue
                # Check condition Register Time
                if promotion_id.register_time_type and promotion_id.promotion_register_time:
                    match, temp = self.check_register_time(promotion_id, temp,
                                                           self.order_line.filtered(lambda l: l not in pass_line))
                    if match:
                        promotion_group.append(temp)
                        for item in temp:
                            order_line_temp -= item
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
                # Check Amount Product Category
                if promotion_id.is_amount_product and promotion_id.promotion_amount_product:
                    match, temp = self.check_amount_product(promotion_id, temp, self.order_line.filtered(
                        lambda l: l not in pass_line))
                    if match:
                        promotion_group.append(temp)
                        for item in temp:
                            order_line_temp -= item
                            if item not in pass_line:
                                pass_line.append(item)
                        continue
        if promotion_id.promotion_limit and len(promotion_group) > 1:
            promotion_group = [promotion_group[0]]


        res = str(promotion_group)+ ' '+ mes
        return str(res)







    @api.model
    def api_check_valid_promotion(self, so_id):
        code = 200
        messages = 'Successfully'
        check = self.browse(so_id).check_valid_promotion_check()
        logging.info(check)
        res = {'code': code, 'messages': messages, 'data': check}
        return json.dumps(res)




    @api.model
    def get_reseller_data(self,mb_customer):
        code=200
        messages='Successfully'
        sql=''' SELECT sol."id" as id,ss."reference" as reference, ss."name" as product_name, rs."name" as reseller_name, rs."code" as reseller_code,  so.contract_id, contract."state" as contract_state,contract."name" as contract_name, contract."reason" as reason, contract."inactive_upload" as inactive_upload  
							 FROM sale_order_line sol							 
							 INNER JOIN sale_order so on so.id=sol.order_id
							 INNER JOIN res_partner res_p on so.partner_id = res_p.id
							 INNER JOIN product_product product on sol.product_id = product.id
							 INNER JOIN sale_service ss on product.id= ss.product_id      
                                LEFT JOIN mb_sale_contract contract ON so.contract_id = contract.id
								LEFT JOIN reseller_customer rs ON ss.reseller_id = rs.id
								    WHERE
								    ss.status = 'active'
                                    and res_p.ref = '%(mb_ref)s'
                                    and sol.register_type = 'register'
                                    and sol.category_code like '%(persen)s.vn'
                                    and sol.customer_type = 'agency'
                                                                    and sol.service_status = 'done' '''\
                                %{
                                    'mb_ref':str(mb_customer),
                                    'persen':'%'
                                    }
        self._cr.execute(sql)
        data = self._cr.dictfetchall()
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)


    # @api.multi
    # def use_promotion_account(self):
    #     discount = 0
    #     promotion_account_compute = self.partner_id.promotion_account_compute
    #     # convert money > 1000
    #     # check và sử dung tiền khuyến mãi
    #     if promotion_account_compute >= 0:
    #         if promotion_account_compute >= self.amount_total:
    #             tmp_promotion_account_compute= promotion_account_compute
    #         else:tmp_promotion_account_compute = int(promotion_account_compute / 1000) * 1000
    #     else:
    #         tmp_promotion_account_compute = 0
    #     if self.partner_id.promotion_account_compute <= 0 or self.partner_id.company_type == 'agency':
    #         raise Warning(_("Promotion Account <= 0 or Customer is an Agency"))
    #     if self.fully_paid or self.temp_approve:
    #         raise Warning(_("Order had paid or temple approved, can't remove promotion discount"))
    #
    #     for line in self.order_line:
    #         if line.renew_taxed_price == 0:
    #             continue
    #         if line.product_category_id and (not line.product_category_id.parent_id or
    #                 line.product_category_id.parent_id.code not in ('TMVN', 'TMTV')) and \
    #                 tmp_promotion_account_compute > discount:
    #             if line.renew_taxed_price - line.discount_renew_taxed_price - line.promotion_receivable_amount >= tmp_promotion_account_compute - discount:
    #                 cur_dis = tmp_promotion_account_compute - discount
    #                 discount += cur_dis
    #                 line.write({
    #                     'promotion_receivable_amount': line.promotion_receivable_amount + cur_dis,
    #                     'promotion_discount': line.promotion_discount + cur_dis
    #                 })
    #             else:
    #                 discount += line.renew_taxed_price - line.discount_renew_taxed_price
    #                 line.write({
    #                     'promotion_receivable_amount': line.promotion_receivable_amount + discount,
    #                     'promotion_discount': line.promotion_discount + discount
    #                 })
    #     if discount:
    #         self.env['customer.promotion.history'].create({
    #             'partner_id': self.partner_id.id,
    #             'order_id': self.id,
    #             'total': discount * -1,
    #             'date': datetime.now().date()
    #         })
    #    {
    #
    #         'qty': 1
    #         'license': 0,
    #         'product_id': 0,
    #         'register_type': 'renew',
    #     }

    @api.model
    def create_so_new(self,valus):
        code = 200
        messages = 'Successfully'
        data ={}
        so = self.create(valus)
        if so:
            replace_name = str(so.name).replace('SO', 'ID')
            so.name=replace_name
            data={
                    'id':so.id,
                    'name':replace_name
                  }
        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)

