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

from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
# from ..sale.sale_order_line import REGISTER_TYPE
import re
from odoo.exceptions import UserError
import logging as _logger
import json
import random
import string

REGISTER_TYPE = ["register",
                 "renew",
                 "transfer",
                 "upgrade"]


class ExternalSO(models.AbstractModel):
    _description = 'External SO API'
    _name = 'external.so'

    @api.multi
    def _validate_email(self, email_list):
        """
            TO DO:
            - Validate the format of emails
        """
        if any(re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email) == None for email in email_list):
            return False
        return True

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    def _create_customer(self, vals):
        """
            TO DO:
            - Check and create customer
        """
        # Check type of data
        if type(vals) is not dict:
            return {'msg': "Invalid CustomerEntity"}

        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        msg = ""
        customer_vals = {'customer': True}

        if vals.get('ref'):
            ref = vals.get('ref')
            customer = ResPartner.search([('ref', '=', ref)], limit=1)
            if customer:
                return {'customer': customer, 'msg': msg}
        else:
            ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
        name = self._convert_str(vals.get('name'))
        if not name:
            return {'msg': "Customer name could not be empty"}

        customer_vals.update({'name': name, 'ref': ref})
        list_fields = ['street', 'email', 'mobile', 'website', 'vat',
                       'indentify_number', 'function', 'phone', 'fax',
                       'sub_email_1', 'sub_email_2', 'main_account',
                       'promotion_account', 'representative', 'company_id']
        for field in list_fields:
            if not vals.get(field):
                continue
            if field in ['email', 'sub_email_1', 'sub_email_2']:
                if not self._validate_email([vals[field]]):
                    return {'msg': 'Invalid email {} : {} .'.
                        format(field, vals[field])}
            customer_vals.update({field: vals[field]})
        # Get state id
        if customer_vals.get('state_code'):
            state_id = ResCountyState.search(
                [('code', '=', customer_vals['state_code'])], limit=1)
            if state_id:
                customer_vals.update({'state_id': state_id.id})
            else:
                return {'msg': 'State Code {} is not found'.
                    format(customer_vals['state_code'])}
        try:
            if vals.get('date_of_birth'):
                date_of_birth = datetime.strptime(
                    str(vals['date_of_birth']), DF)
                customer_vals.update({'date_of_birth': date_of_birth})
            if vals.get('date_of_founding'):
                date_of_founding = datetime.strptime(
                    str(vals['date_of_founding']),
                    DF)
                customer_vals.update({'date_of_founding': date_of_founding})
        except ValueError:
            return {
                'code': 0, 'msg':
                    'Invalid date_of_birth or date_of_founding yyyy-mm-dd',
                'data': {}}

        # Get Country id
        # country_code = self._convert_str(customer_vals.get('country_code'))
        if vals.get('country_code'):
            country_id = ResCountry.search([('code', '=', vals.get('country_code'))], limit=1)
            if country_id:
                customer_vals.update({'country_id': country_id.id})
            else:
                return {'msg': 'Country Code {} is not found'.
                    format(vals.get('country_code'))}
        # Get company type
        if vals.get('company_type'):
            if vals['company_type'] not in \
                    ['person', 'company', 'contact', 'agency']:
                return {
                    'msg': ("Company type must be in "
                            "['person', 'company', 'contact', 'agency']")
                }
            customer_vals.update({'company_type': vals['company_type']})

        # Check gender value
        if vals.get('gender'):
            if vals['gender'] not in ['male', 'female']:
                return {
                    'msg': ("Gender must be in "
                            "['male', 'female']")
                }
            customer_vals.update({'gender': vals['gender']})

        # Check company
        if not vals.get('company_id'):
            return {
                'msg': "Company ID is not found."
            }
        customer_vals.update({'company_id': vals['company_id']})

        # Check source
        if vals.get('source'):
            source_id = self.env['res.partner.source'].search(
                [('code', '=', vals['source'])], limit=1)
            if not source_id:
                return {
                    'msg': ("Customer source '%s' is not found.  " %
                            (vals['source']))
                }
            customer_vals.update({'source_id': source_id.id})
        # Check exits customer
        # customer = ResPartner.search([('ref', '=', ref)], limit=1)
        # if not customer:
        customer = ResPartner.create(customer_vals)
        return {'customer': customer, 'msg': msg}

    def create_order_lines(self, vals):
        """
            TO DO:
            - Checking Order line vals
        """
        # Check type of data
        if type(vals) is not list:
            return {'msg': "Invalid OrderLineEntity"}

        ProductProduct = self.env['product.product']
        ProductCategory = self.env['product.category']
        ProductUom = self.env['product.uom']
        AccountTax = self.env['account.tax']

        error_msg = ''
        order_lines = []
        line_num = 1

        mbn_product_parent_id = {}

        required_arguments = [
            'register_type', 'categ_code', 'product_code', 'product_name',
            'qty', 'uom', 'reg_price_wot', 'reg_price_wt', 'reg_tax_amount',
            'ren_price_wot', 'ren_price_wt', 'ren_tax_amount', 'tax',
            'sub_total', 'company_id', 'template', 'reseller']
        non_required_arguments = ['parent_product_code', 'parent_product_name', 'license', 'price_updated',
                                  'dns', 'price', 'vps_code', 'os_template',
                                  'up_price', 'refund_amount', 'promotion_back_amount', 'refund_remain_time',
                                  'up_price']

        for line in vals:
            if type(line) is not dict:
                return {
                    'msg': "Invalid OrderLineEntity"}
            argument_error = ''
            line_vals = {}
            parent_product = False

            # Check required arguments
            for argument in required_arguments:
                if argument in line:
                    line_vals[argument] = line[argument]
                    continue
                argument_error += "'%s', " % (argument)

            if argument_error:
                error_msg += ("### The required arguments: %s of"
                              " order line at line %s are not found! ") % (
                                 argument_error, line_num)
                return {'msg': error_msg}

            # Get non required arguments
            for argument in non_required_arguments:
                if line.get(argument):
                    line_vals[argument] = line.get(argument)
            # Check Register type
            if line_vals['register_type'] not in REGISTER_TYPE:
                error_msg += ("### Please check 'register_type' of"
                              " order line at line %s ") % line_num

            # Check Product Category
            if not self._convert_str(line_vals['categ_code']):
                error_msg += "### Can't find product category at line %s " % \
                             (line_num)
            product_categ = ProductCategory.search(
                [('code', '=', line_vals['categ_code'])])
            if not product_categ:
                error_msg += "### Can't find product category at line %s " % \
                             (line_num)
            if not line_vals['company_id']:
                error_msg += "### Company ID at line %s is not found! " % line_num

            # Check Product Uom
            product_uom = self._convert_str(line_vals['uom'])
            if not product_uom:
                error_msg += (
                                 "### Product Uom '%s' at line %s is not found! ") % \
                             (product_uom, line_num)
            else:
                product_uom = ProductUom.search(
                    [('name', '=', product_uom)], limit=1)
                if not product_uom:
                    error_msg += (
                                     "### Product Uom '%s' at line %s is not found! ") % \
                                 (product_uom, line_num)

            product_ids = ProductProduct
            # Check Product Code
            product_code = self._convert_str(line_vals['product_code'])
            if product_code:
                product_ids = ProductProduct.search(
                    [('default_code', '=', line_vals['product_code'])],
                    limit=1)
            else:
                product_code = self.env['ir.sequence'].next_by_code('product.product')

            # check tax
            tax_id = AccountTax.with_context(force_company=line_vals['company_id']).search([
                ('amount', '=', float(line_vals['tax'])), ('type_tax_use', '=', 'sale'),
                ('company_id', '=', line_vals['company_id'])], limit=1)
            # if not tax_id:
            #     error_msg += "### Can't find Tax at line %s " % (line_num)

            product_name = self._convert_str(line['product_name'])
            if not product_name:
                error_msg += "### Invalid product name at line %s " % (
                    line_num)

            # Check parent product
            if line_vals.get('parent_product_code', False):
                parent_product = ProductProduct.search([
                    ('default_code', '=',
                     line_vals.get('parent_product_code'))], limit=1)

                if not parent_product:
                    error_msg += ("### Can't find parent product with code"
                                  " '%s' at line %s ") % \
                                 (line_vals.get('parent_product_code'), line_num)
            # Check template
            # if line_vals.get('template', False):

            # Create new product
            if not product_ids and not error_msg:
                new_product_vals = {
                    'default_code': product_code,
                    'name': product_name,
                    'uom_id': product_uom.id,
                    'uom_po_id': product_uom.id,
                    'categ_id': product_categ.id,
                    'minimum_register_time':
                        product_categ.minimum_register_time,
                    'billing_cycle': product_categ.billing_cycle,
                    'type': 'service'
                }
                product_ids = ProductProduct.create(new_product_vals)

                if line.get('mbn_parent_id') == 0:
                    mbn_product_parent_id.update({
                        line.get('mbn_id'): product_ids
                    })

                if line.get('mbn_parent_id') and line.get('mbn_id'):
                    if line.get('mbn_parent_id') == 0:
                        pass

                    else:

                        parent_product = mbn_product_parent_id.get(line.get('mbn_parent_id'))

            # Create oder lines
            if product_ids and not error_msg:
                new_line_vals = {
                    'register_type': line_vals['register_type'],
                    'product_id': product_ids.id,
                    'parent_product_id': parent_product and parent_product.id or False,
                    'product_category_id': product_categ.id,
                    'time': line_vals['qty'],
                    'original_time': line_vals['qty'],
                    'tax_id': tax_id and [(6, 0, [tax_id.id])] or False,
                    'register_untaxed_price': line_vals['reg_price_wot'],
                    'register_taxed_price': line_vals['reg_price_wt'],
                    'renew_untaxed_price': line_vals['ren_price_wot'],
                    'renew_taxed_price': line_vals['ren_price_wt'],
                    'register_taxed_amount': line_vals['reg_tax_amount'],
                    'renew_taxed_amount': line_vals['ren_tax_amount'],
                    'fix_subtotal': line_vals['sub_total'],
                    'company_id': line_vals['company_id'],
                    'reseller': line_vals['reseller'] or '',
                    'template': line_vals['template'] or '',
                    'product_uom': product_uom.id,
                }

                if 'license' in line_vals:
                    new_line_vals.update({'license': line_vals['license'] or ''})
                if 'dns' in line_vals:
                    new_line_vals.update({'dns': line_vals['dns'] or ''})
                if 'price' in line_vals:
                    new_line_vals.update({'price': line_vals['price'] or 0})
                if 'vps_code' in line_vals:
                    new_line_vals.update({'vps_code': line_vals['vps_code'] or False})
                if 'os_template' in line_vals:
                    new_line_vals.update({'os_template': line_vals['os_template'] or False})
                if 'up_price' in line_vals:
                    new_line_vals.update({'up_price': line_vals['up_price'] or 0})
                if 'refund_amount' in line_vals:
                    new_line_vals.update({'refund_amount': line_vals['refund_amount'] or 0})
                if 'promotion_back_amount' in line_vals:
                    new_line_vals.update({'promotion_back_amount': line_vals['promotion_back_amount'] or 0})
                if 'price_updated' in line_vals:
                    new_line_vals.update({'price_updated': line_vals['price_updated'] or False})
                if 'refund_remain_time' in line_vals:
                    new_line_vals.update({'refund_remain_time': line_vals['refund_remain_time'] or 0})

                order_lines.append((0, 0, new_line_vals))
            line_num += 1
        return {'line_ids': order_lines, 'msg': error_msg, 'data': {}}

    @api.model
    def create_so(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[],
                  mobile='', payment_method='', money_transfer=0, source='',overdue = False):
        """
        TO DO:
            - Create New Sale Order and Customer in Odoo
        """
        # Objects
        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']
        # variables
        error_msg = ''
        order_type = order_type
        customer_vals = customer
        team_id = False

        if not name:
            return {'code': 0, 'msg': 'Order name could not be empty',
                    'data': {}}
        else:
            order = SaleOrder.search([('name', '=', name)], limit=1)
            if order:
                return {'code': 0, 'msg': 'Order name already exits',
                        'data': {}}
        if not date_order:
            return {'code': 0, 'msg': 'Order Date could not be empty',
                    'data': {}}
        if not company_id:
            return {'code': 0, 'msg': 'Company ID could not be empty',
                    'data': {}}
        if source:
            source_id = self.env['utm.source'].search([('name', '=', source)])
        else:
            source_id = False
        if not order_type or order_type not in ['normal', 'renewed', 'mbn', 'id', 'chili']:
            return {'code': 0,
                    'msg': 'Order Type must be `normal`, `renewed`, `mbn`, `chili` or `id`',
                    'data': {}}
        if not customer:
            return {'code': 0, 'msg': 'Customer info could not be empty',
                    'data': {}}
        if not status or status not in ('draft', 'not_received', 'sale', 'paid', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                             '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'code': 0, 'msg': 'Order detail could not be empty',
                    'data': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + \
                         timedelta(hours=-7)
        except ValueError:
            return {'code': 0, 'msg': 'Invalid order date yyyy-mm-dd h:m:s',
                    'data': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'code': 0,
                        'msg': 'Saleteam {} is not found'.format(saleteam_code
                                                                 ),
                        'data': {}}
        try:
            # Prepare Order lines:
            order_lines = self.create_order_lines(lines)
            if order_lines['msg']:
                error_msg += order_lines['msg']

            # Check Customer exits or create a new customer
            customer_result = self._create_customer(customer_vals)
            if customer_result.get('msg'):
                self._cr.rollback()
                return {'code': 0, 'msg': customer_result['msg'], 'data': {}}
            customer = customer_result['customer']

            if error_msg:
                self._cr.rollback()
                return {'code': 0, 'msg': error_msg, 'data': {}}

            so_vals = {'partner_id': customer.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       # 'state': order_type == 'normal' and 'draft' or 'not_received',
                       'state': status,
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id,
                       'source_id': source_id and source_id.id or False,
                       'order_line': order_lines['line_ids'],
                       'payment_method_so': payment_method,
                       'employee_mobile': mobile,
                       'money_transfer': money_transfer or 0,
                       }
            so = SaleOrder.with_context(force_company=company_id).create(so_vals)

            so.write({
                'original_subtotal': so.amount_untaxed,
                'original_total': so.amount_total,
                'overdue': overdue,
            })
            if so.state not in ('not_received', 'draft', 'cancel'):
                so.order_line.write({'price_updated': True})
            return {'code': 1, 'msg': "Create Order Successful!"}
        except ValueError:
            self._cr.rollback()
            return {'code': 0, 'msg': 'Unknow Error!', 'data': {}}

    @api.model
    def create_so_fix(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=[],
                      mobile='', source=''):
        """
        TO DO:
            - Create New Sale Order and Customer in Odoo
        """
        # Objects
        CrmTeam = self.env['crm.team']
        SaleOrder = self.env['sale.order']

        # variables
        error_msg = ''
        order_type = order_type
        customer_vals = customer
        team_id = False

        if not name:
            return {'code': 0, 'msg': 'Order name could not be empty',
                    'data': {}}
        else:
            order = SaleOrder.search([('name', '=', name)], limit=1)
            if order:
                return {'code': 0, 'msg': 'Order name already exits',
                        'data': {}}
        if not date_order:
            return {'code': 0, 'msg': 'Order Date could not be empty',
                    'data': {}}
        if not company_id:
            return {'code': 0, 'msg': 'Company ID could not be empty',
                    'data': {}}
        if source:
            source_id = self.env['utm.source'].search([('name', '=', source)])
        else:
            source_id = False
        if not order_type or order_type not in ['normal', 'renewed', 'mbn', 'id', 'chili']:
            return {'code': 0,
                    'msg': 'Order Type must be `normal`, `renewed`, `mbn`, `chili` or `id`',
                    'data': {}}
        if not customer:
            return {'code': 0, 'msg': 'Customer info could not be empty',
                    'data': {}}
        if not status or status not in ('draft', 'not_received', 'sale', 'sale', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                             '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'code': 0, 'msg': 'Order detail could not be empty',
                    'data': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + \
                         timedelta(hours=-7)
        except ValueError:
            return {'code': 0, 'msg': 'Invalid order date yyyy-mm-dd h:m:s',
                    'data': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'code': 0,
                        'msg': 'Saleteam {} is not found'.format(saleteam_code),
                        'data': {}}
        try:
            # Prepare Order lines:
            order_lines = self.create_order_lines(lines)
            if order_lines['msg']:
                error_msg += order_lines['msg']

            # Check Customer exits or create a new customer
            customer_result = self._create_customer(customer_vals)
            if customer_result.get('msg'):
                return {'code': 0, 'msg': customer_result['msg'], 'data': {}}
            customer = customer_result['customer']

            if error_msg:
                return {'code': 0, 'msg': error_msg, 'data': {}}

            so_vals = {'partner_id': customer.id,
                       'date_order': date_order,
                       'user_id': False,
                       'team_id': team_id and team_id.id or False,
                       # 'state': order_type == 'normal' and 'draft' or 'not_received',
                       'state': status,
                       'type': order_type,
                       'coupon': coupon,
                       'name': name,
                       'company_id': company_id,
                       'source_id': source_id and source_id.id or False,
                       'order_line': order_lines['line_ids'],
                       'employee_mobile': mobile
                       }
            order_id = SaleOrder.create(so_vals)
            order_id.write({
                'original_subtotal': order_id.amount_untaxed,
                'original_total': order_id.amount_total,
            })
            if order_id.state not in ('not_received', 'draft', 'cancel'):
                order_id.order_line.write({'price_updated': True})
            return {'code': 1, 'msg': "Create Order Successful!", 'data': order_id}
        except Exception as e:
            _logger.error("Can't Create S: %s" % (e.message or repr(e)))
            return {'code': 0, 'msg': 'Can`t Create SO: %s' % (e.message or repr(e)), 'data': {}}

    @api.model
    def update_so(self, name, vals={}):
        res = {'code': 0, 'msg': ''}
        SaleOrder = self.env['sale.order']
        CrmTeam = self.env['crm.team']
        sale_order = SaleOrder.search([('name', '=', name)], limit=1)
        if not sale_order:
            res['msg'] = 'SALE ORDER `{}` is not found'.format(name)
            return res
        if 'saleteam_code' in vals:
            team = CrmTeam.search([('code', '=', vals['saleteam_code'])],
                                  limit=1)
            if not team:
                res['msg'] = '''TEAM with CODE `{}` is not found'''. \
                    format(vals['saleteam_code'])
                return res
            sale_order.team_id = team
            res['code'] = 1
            return res
        else:
            res['msg'] = 'Vals has some invalid key(s)'
            return res

    @api.model
    def get_not_receive_so(self, date_from=False, date_to=False,
                           limit=None, order='date_order'):
        """
            TO DO:
            - [API] MB call Odoo to get the list of "Not Received" orders
        """
        res = {'code': 0, 'msg': '', 'data': []}
        data = []
        SaleOrder = self.env['sale.order']
        error_msg = ''
        args = [('state', '=', 'not_received')]

        if date_from:
            try:
                system_date_from = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_from))
                args += [('date_order', '>=', system_date_from[0])]
            except ValueError:
                error_msg += 'Wrong DATE FROM format, '
        if date_to:
            try:
                system_date_to = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_to))
                args += [('date_order', '<=', system_date_to[0])]
            except ValueError:
                error_msg += 'Wrong DATE TO format, '
        try:
            if not isinstance(limit, int) or int(limit) < 1:
                limit = None
        except ValueError:
            limit = None
            error_msg += 'Invalid limit'

        if error_msg:
            res.update({'code': 0, 'msg': error_msg, 'data': data})
            return res

        try:
            so_recs = SaleOrder.search(args=args, limit=limit, order=order)
        except UserError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except ValueError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except:
            error_msg += 'Unknow Error, '
            res['msg'] = error_msg
            return res
        for so in so_recs:
            data.append(so.name)
        res.update({'code': 1, 'msg': error_msg, 'data': data})
        return res

    @api.model
    def get_so_renewed_and_update_price(self):
        res = {'code': 0, 'msg': ''}
        orders = self.env['sale.order'].search([('type', '=', 'renewed'), ('fully_paid', '=', False)])
        for order in orders:
            # if order.date_order and (datetime.now().date() - datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()).days in (0,3,5,7,15,20,30):
            if any(not line.price_updated for line in order.order_line):
                try:
                    order.update_price()
                except:
                    res['msg'] = "Can't update price SO %s" % order.name
                    return res
        res.update({'code': 1, 'msg': "'Update price SO renewed successfully!'"})
        return res

    @api.model
    def get_so_renewed_and_send_email(self):
        res = {'code': 0, 'msg': '', 'data': []}
        orders = self.env['sale.order'].search([('type', '=', 'renewed'), ('fully_paid', '=', False)])
        data = []
        try:
            for order in orders:
                # if order.date_order and (datetime.now().date() - datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()).days in (0,3,5,7,15,20,30):
                # if any(not line.price_updated for line in order.order_line):
                #     order.update_price()
                data_append = ['name: ' + '\"' + (order.partner_id.name or '') + '\"',
                               'code: ' + '\"' + (order.partner_id.ref or '') + '\"',
                               'email: ' + '\"' + (order.partner_id.email or '') + '\"',
                               'company_id: ' + '\"' + str(order.company_id.id) + '\"']
                so_line_append = {}
                for line in order.order_line:
                    service = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                    so_line_append['product'] = '\"' + str(line.product_id.name) + '\"'
                    so_line_append['end_date'] = '\"' + (service and service.end_date or '') + '\"'
                    so_line_append['price_subtotal'] = line.price_subtotal or 0
                    so_line_append['price_tax'] = line.price_tax or 0
                    so_line_append['price_total'] = line.price_total or 0
                    data_append.append([so_line_append])
                data.append(data_append)
            res.update({'code': 1, 'msg': "'Get SO renewed successfully!'", 'data': data})
        except:
            res['msg'] = "Can't get SO"
        return res

    @api.model
    def cron_so_renewed_fix(self):
        cron = self.env['ir.cron'].search([('model', '=', 'sale.service'), ('function', '=', 'renew_sales_orders')],
                                          limit=1)
        if not cron:
            return True
        cron.method_direct_trigger()
        return {'code': 1, 'msg': 'Successfully'}

    @api.model
    def cron_so_renewed(self, days=30):
        res = {'"code"': 0, '"msg"': '""'}
        SaleService = self.env['sale.service']
        if not days or type(days) is not int or days < 1:
            res.update({'"msg"': '"Days could be not empty and must be integer (larger 0)"'})
            return res
        try:
            SaleService.renew_sales_orders_by_days(days=days)
        except Exception as e:
            _logger.error("Error: %s" % (e.message or repr(e)))
            return {'code': 0, 'msg': 'Can not pour renewal order.'}
        return {'code': 1, 'msg': 'Successfully'}

    @api.model
    def get_so_customer(self, user_code, service='', so_code='', limit=100, offset=0, order=None, sort='asc',
                        columns=['id', 'name', 'date_order', 'coupon', 'amount_total', 'state', 'order_line'],
                        filter=''):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        # ProductProduct = self.env['product.product']
        data = []
        # Check data
        if not user_code:
            res.update({'"msg"': '"Username could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', user_code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Username not found."'})
            return res
        args = [('partner_id', '=', partner_id.id)]
        if so_code:
            args.append(('name', '=', so_code))
        if service:
            # service_ids = ProductProduct.search([('name', 'ilike', service)])
            # if service_ids:
            args.append(('product_id.name', 'ilike', service))
        if filter:
            if filter not in ('draft', 'sale', 'completed', 'done', 'cancel'):
                res.update({'"msg"': '"Filter must be in `draft`, `sale`, `completed`, `done` or `cancel`"'})
                return res
            args.append(('state', '=', filter))
        order_fix = order
        if order:
            if sort:
                if sort not in ('asc', 'desc'):
                    res.update({'"msg"': '"Sort must be `asc` or `desc`"'})
                    return res
                order_fix += ' ' + sort
        if columns:
            for col in columns:
                if not col in SaleOrder._fields:
                    res.update({'"msg"': '"Column {%s} not exists."' % col})
                    return res
        sos = SaleOrder.search_read(domain=args, fields=columns, limit=limit, offset=offset, order=order_fix)
        for so in sos:
            # _logger.info("+++++++++++++ %s ++++++++++++++", so['id'])
            # order_id = SaleOrder.browse(so['id'])

            # if not order_id.order_line or (not order_id.fully_paid and any(l.register_type == 'upgrade' for l in order_id.order_line)):
            #     # _logger.info("================ %s ==================", order_id.id)
            #     # sos.remove(so)
            #     continue
            # for key, value in so.iteritems():
            for key, value in so.items():
                if not value:
                    del so[key]
                    so.update({'\"' + key + '\"': '""'})
                elif key == 'order_line':
                    del so[key]
                    order_line = []
                    for line in value:
                        so_line = SaleOrderLine.browse(line)
                        order_line.append({
                            '\"' + 'register_type' + '\"': '\"' + (so_line.register_type or '') + '\"',
                            '\"' + 'product_id' + '\"': so_line.product_id and str(so_line.product_id.id) or '""',
                            '\"' + 'product_code' + '\"': '\"' + (
                                        so_line.product_id and so_line.product_id.default_code or '') + '\"',
                            '\"' + 'product' + '\"': '\"' + (
                                        so_line.product_id and so_line.product_id.name or '') + '\"',
                            '\"' + 'product_category_id' + '\"': so_line.product_category_id and so_line.product_category_id.id or '""',
                            '\"' + 'product_category_code' + '\"': '\"' + (
                                        so_line.product_category_id and so_line.product_category_id.code or '') + '\"',
                            '\"' + 'parent_product_id' + '\"': so_line.parent_product_id and so_line.parent_product_id.id or '""',
                            '\"' + 'parent_product_code' + '\"': '\"' + (
                                        so_line.parent_product_id and so_line.parent_product_id.default_code or '') + '\"',
                            '\"' + 'time' + '\"': so_line.time or 0,
                            '\"' + 'register_untaxed_price' + '\"': so_line.register_untaxed_price or 0,
                            '\"' + 'register_taxed_price' + '\"': so_line.register_taxed_price or 0,
                            '\"' + 'renew_untaxed_price' + '\"': so_line.renew_untaxed_price or 0,
                            '\"' + 'renew_taxed_price' + '\"': so_line.renew_taxed_price or 0,
                            '\"' + 'price_subtotal' + '\"': so_line.price_subtotal or 0,
                            '\"' + 'price_tax' + '\"': so_line.price_tax or 0,
                            '\"' + 'price_total' + '\"': so_line.price_total or 0,
                            '\"' + 'template' + '\"': '\"' + (so_line.template or '') + '\"',
                            '\"' + 'reseller' + '\"': '\"' + (so_line.reseller or '') + '\"',
                        })
                    so.update({'\"' + key + '\"': order_line})
                elif type(key) is object:
                    del so[key]
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    so.update({
                        '\"' + key + '\"': tuple(lst)
                    })
                elif type(value) in (unicode, str):
                    del so[key]
                    so.update({'\"' + key + '\"': '\"' + value + '\"'})
                elif type(value) in (int, float):
                    del so[key]
                    so.update({'\"' + key + '\"': value})
                # else:
                #     so.update({'\"' + key + '\"': '\"' + str(value) + '\"'})
            employee = SaleOrder.browse(so['"id"']).user_id and SaleOrder.browse(so['"id"']).user_id.mapped(
                'employee_ids') or False
            company_phone = SaleOrder.browse(so['"id"']) and SaleOrder.browse(so['"id"']).company_id.phone or ''
            employee_phone = employee and employee[0].work_phone or ''
            employee_phone = employee_phone and (
                        company_phone and (company_phone + ' - ' + employee_phone) or employee_phone) or ''
            so['"staff_name"'] = '\"' + (employee and employee[0].name or '') + '\"'
            so['"staff_email"'] = '\"' + (employee and employee[0].work_email or '') + '\"'
            so['"staff_phone"'] = '\"' + employee_phone + '\"'
            so['"staff_mobile"'] = '\"' + (employee and employee[0].mobile_phone or '') + '\"'
            data.append(so)
        # data = sos and sos or data
        # for so in so_ids:

        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_so_detail(self, so_id, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        data = []
        # Check SO
        if not so_id or (type(so_id) not in (int, str)):
            res.update({'"msg"': '"SO id could be not empty and must be integer"'})
            return res
        if type(so_id) is int:
            so = SaleOrder.browse(so_id)
        else:
            so = SaleOrder.search([('name', '=', so_id)], limit=1)
        if not so:
            res.update({'"msg"': '"SO not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if so.partner_id.ref <> cus_code:
            res.update({'"msg"': '"SO not belong customer %s."' % cus_code})
            return res
        employee = so.user_id and so.user_id.mapped('employee_ids') or False
        company_phone = so.company_id.phone or ''
        employee_phone = employee and employee[0].work_phone or ''
        employee_phone = employee_phone and (
                    company_phone and (company_phone + ' - ' + employee_phone) or employee_phone) or ''
        so_dict = {
            '"name"': '\"' + so.name + '\"',
            '"id"': '\"' + str(so.id) + '\"',
            '"partner_id"': so.partner_id and so.partner_id.id or '""',
            '"partner_code"': '\"' + (so.partner_id and so.partner_id.ref or '') + '\"',
            '"date_order"': '\"' + (so.date_order or '') + '\"',
            '"validity_date"': '\"' + (so.validity_date or '') + '\"',
            '"coupon"': '\"' + (so.coupon or '') + '\"',
            '"user_id"': so.user_id and so.user_id.id or '""',
            '"team_id"': so.team_id and so.team_id.id or '""',
            '"team_code"': '\"' + (so.team_id and so.team_id.code or '') + '\"',
            '"fully_paid"': '\"' + (so.fully_paid and 'True' or 'False') + '\"',
            '"type"': '\"' + (so.type or '') + '\"',
            '"is_lock"': '\"' + (so.is_lock and 'True' or 'False') + '\"',
            '"company_id"': so.company_id and so.company_id.id or '""',
            '"amount_untaxed"': so.amount_untaxed or 0,
            '"amount_tax"': so.amount_tax or 0,
            '"amount_total"': so.amount_total or 0,
            '"invoice"': so.invoice_ids and so.invoice_ids.ids or '"False"',
            '"state"': '\"' + (so.state or 'draft') + '\"',
            '"staff_name"': '\"' + (employee and employee[0].name or '') + '\"',
            '"staff_email"': '\"' + (employee and employee[0].work_email or '') + '\"',
            '"staff_phone"': '\"' + employee_phone + '\"',
            '"staff_mobile"': '\"' + (employee and employee[0].mobile_phone or '') + '\"',
            '"used_promotion_account"': self.env['customer.promotion.history'].search_count(
                [('order_id', '=', so.id)]) > 0 and 1 or 0
        }
        order_line = []
        for line in so.order_line:
            so_line = {}
            so_line.update({
                '"register_type"': '\"' + (line.register_type or '') + '\"',
                '"product_id"': line.product_id and line.product_id.id or '""',
                '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                '"product_category_code"': '\"' + (
                            line.product_category_id and line.product_category_id.code or '') + '\"',
                '"product_category"': '\"' + (
                            line.product_category_id and line.product_category_id.display_name or '') + '\"',
                '"parent_product_id"': line.parent_product_id and line.parent_product_id.id or '""',
                '"parent_product_code"': '\"' + (
                            line.parent_product_id and line.parent_product_id.default_code or '') + '\"',
                '"parent_product"': '\"' + (line.parent_product_id and line.parent_product_id.name or '') + '\"',
                '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                '"time"': line.time or 0,
                '"register_untaxed_price"': line.register_untaxed_price or 0,
                '"register_taxed_price"': line.register_taxed_price or 0,
                '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                '"renew_taxed_price"': line.renew_taxed_price or 0,
                '"price_subtotal"': line.price_subtotal or 0,
                '"price_tax"': line.price_tax or 0,
                '"price_total"': line.price_total or 0,
                '"template"': '\"' + (line.template or '') + '\"',
                '"reseller"': '\"' + (line.reseller or '') + '\"',
                '"service_status"': '\"' + (line.service_status or '') + '\"',
                '"is_addons"': '\"' + (
                            line.product_category_id and line.product_category_id.is_addons and 'True' or 'False') + '\"',
                '"end_date"': '\"' + (line.end_date or '') + '\"',
                '"id"': line.id,
            })
            if 'vps_code' in SaleOrderLine._fields:
                so_line.update({'"vps_code"': '\"' + (line.vps_code or '') + '\"'})
            if 'os_template' in SaleOrderLine._fields:
                so_line.update({'"os_template"': '\"' + (line.os_template or '') + '\"'})
            order_line.append(so_line)
        so_dict.update({
            '"order_line"': order_line
        })
        data.append(so_dict)
        res.update({'"code"': 1, '"msg"': '"Get SO %s Successfully"' % so.name, '"data"': data})
        return res

    @api.model
    def get_so_detail_api(self, so_id, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        data = []
        # Check SO
        if not so_id or (type(so_id) not in (int, str)):
            res.update({'"msg"': '"SO id could be not empty and must be integer"'})
            return res
        if type(so_id) is int:
            so = SaleOrder.browse(so_id)
        else:
            so = SaleOrder.search([('name', '=', so_id)], limit=1)
        if not so:
            res.update({'"msg"': '"SO not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if so.partner_id.ref <> cus_code:
            res.update({'"msg"': '"SO not belong customer %s."' % cus_code})
            return res
        so_dict = {
            '"id"': so.id,
            '"name"': '\"' + so.name + '\"',
            '"partner_id"': so.partner_id and so.partner_id.id or '""',
            '"partner_code"': '\"' + (so.partner_id and so.partner_id.ref or '') + '\"',
            '"date_order"': '\"' + (so.date_order or '') + '\"',
            '"validity_date"': '\"' + (so.validity_date or '') + '\"',
            '"coupon"': '\"' + (so.coupon or '') + '\"',
            '"user_id"': so.user_id and so.user_id.id or '""',
            '"team_id"': so.team_id and so.team_id.id or '""',
            '"team_code"': '\"' + (so.team_id and so.team_id.code or '') + '\"',
            '"fully_paid"': '\"' + (so.fully_paid and 'True' or 'False') + '\"',
            '"type"': '\"' + (so.type or '') + '\"',
            '"is_lock"': '\"' + (so.is_lock and 'True' or 'False') + '\"',
            '"company_id"': so.company_id and so.company_id.id or '""',
            '"amount_untaxed"': so.amount_untaxed or 0,
            '"amount_tax"': so.amount_tax or 0,
            '"amount_total"': so.amount_total or 0,
            '"invoice"': so.invoice_ids and so.invoice_ids.ids or '"False"',
            '"state"': '\"' + (so.state or 'draft') + '\"',
            '"staff_name"': '""',
            '"staff_email"': '""',
            '"staff_phone"': '""',
            '"staff_mobile"': '""',
            '"used_promotion_account"': self.env['customer.promotion.history'].search_count(
                [('order_id', '=', so.id)]) > 0 and 1 or 0
        }
        order_line = []
        for line in so.order_line:
            so_line = {}
            so_line.update({
                '"register_type"': '\"' + (line.register_type or '') + '\"',
                '"product_id"': line.product_id and line.product_id.id or '""',
                '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                '"product_category_code"': '\"' + (
                            line.product_category_id and line.product_category_id.code or '') + '\"',
                '"product_category"': '\"' + (
                            line.product_category_id and line.product_category_id.display_name or '') + '\"',
                '"parent_product_id"': line.parent_product_id and line.parent_product_id.id or '""',
                '"parent_product_code"': '\"' + (
                            line.parent_product_id and line.parent_product_id.default_code or '') + '\"',
                '"parent_product"': '\"' + (line.parent_product_id and line.parent_product_id.name or '') + '\"',
                '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                '"time"': line.time or 0,
                '"reg_price_wot"': line.register_untaxed_price or 0,
                '"reg_price_wt"': line.register_taxed_price or 0,
                '"en_price_wot"': line.renew_untaxed_price or 0,
                '"reg_tax_amount"': line.renew_taxed_price or 0,
                '"sub_total"': line.price_subtotal or 0,
                '"price_tax"': line.price_tax or 0,
                '"price_total"': line.price_total or 0,
                '"template"': '\"' + (line.template or '') + '\"',
                '"reseller"': '\"' + (line.reseller or '') + '\"',
                '"service_status"': '\"' + (line.service_status or '') + '\"',
                '"is_addons"': '\"' + (
                            line.product_category_id and line.product_category_id.is_addons and 'True' or 'False') + '\"',
                '"end_date"': '\"' + (line.end_date or '') + '\"',
                '"id"': line.id,
            })
            if 'vps_code' in SaleOrderLine._fields:
                so_line.update({'"vps_code"': '\"' + (line.vps_code or '') + '\"'})
            if 'os_template' in SaleOrderLine._fields:
                so_line.update({'"os_template"': '\"' + (line.os_template or '') + '\"'})
            order_line.append(so_line)
        so_dict.update({
            '"order_line"': order_line
        })
        data.append(so_dict)
        res.update({'"code"': 1, '"msg"': '"Get SO %s Successfully"' % so.name, '"data"': data})
        return res

    @api.model
    def get_so_detail_mbn(self, so_id):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleOrder = self.env['sale.order']
        data = []
        # Check SO
        if not so_id or (type(so_id) not in (int, str)):
            res.update({'"msg"': '"SO id could be not empty and must be integer"'})
            return res
        if type(so_id) is int:
            so = SaleOrder.browse(so_id)
        else:
            so = SaleOrder.search([('name', '=', so_id)], limit=1)
        if not so:
            res.update({'"msg"': '"SO not found."'})
            return res
        employee = so.user_id and so.user_id.mapped('employee_ids') or False
        company_phone = so.company_id.phone or ''
        employee_phone = employee and employee[0].work_phone or ''
        employee_phone = employee_phone and (
                    company_phone and (company_phone + ' - ' + employee_phone) or employee_phone) or ''
        so_dict = {
            '"id"': so.id,
            '"name"': '\"' + so.name + '\"',
            '"partner_id"': so.partner_id and so.partner_id.id or '""',
            '"partner_code"': '\"' + (so.partner_id and so.partner_id.ref or '') + '\"',
            '"date_order"': '\"' + (so.date_order or '') + '\"',
            '"validity_date"': '\"' + (so.validity_date or '') + '\"',
            '"coupon"': '\"' + (so.coupon or '') + '\"',
            '"user_id"': so.user_id and so.user_id.id or '""',
            '"team_id"': so.team_id and so.team_id.id or '""',
            '"team_code"': '\"' + (so.team_id and so.team_id.code or '') + '\"',
            '"fully_paid"': '\"' + (so.fully_paid and 'True' or 'False') + '\"',
            '"type"': '\"' + (so.type or '') + '\"',
            '"is_lock"': '\"' + (so.is_lock and 'True' or 'False') + '\"',
            '"company_id"': so.company_id and so.company_id.id or '""',
            '"amount_untaxed"': so.amount_untaxed or 0,
            '"amount_tax"': so.amount_tax or 0,
            # '"promotion_amount_tmp"': so.promotion_amount_tmp or 0,
            '"amount_total"': so.amount_total or 0,
            '"invoice"': so.invoice_ids and so.invoice_ids.ids or [],
            '"state"': '\"' + (so.state or 'draft') + '\"',
            '"staff_name"': '\"' + (employee and employee[0].name or '') + '\"',
            '"staff_email"': '\"' + (employee and employee[0].work_email or '') + '\"',
            '"staff_phone"': '\"' + employee_phone + '\"',
            '"staff_mobile"': '\"' + (employee and employee[0].mobile_phone or '') + '\"',
            '"payment_method_so"': '\"' + (so.payment_method_so or '') + '\"',
            '"money_transfer"': so.money_transfer or 0,
            '"employee_mobile"': '"%s"' % (so.employee_mobile or ''),
            '"used_promotion_account"': self.env['customer.promotion.history'].search_count(
                [('order_id', '=', so.id)]) > 0 and 1 or 0,
        }
        order_line = []
        for line in so.order_line:
            refund_amount = 0
            promotion_back_amount = 0

            if line.register_type == 'upgrade':
                sale_service_obj = self.env['sale.service']
                sale_service = sale_service_obj.search([('product_id', '=', line.product_id.id)])
                old_sale_order_line_data = self.sudo().env['sale.order.line'].search(
                    [('order_partner_id', '=', sale_service.customer_id.id),
                     ('company_id', '=', sale_service.customer_id.company_id.id),
                     ('product_id', '=', sale_service.product_id.id),
                     ('service_status', '=', 'done'),
                     ('fully_paid', '=', True),
                     ], order='create_date DESC', limit=1)
                refund_amount, messages, promotion_back_amount = sale_service_obj.caculate_refund_amount_promotion_back_amount(
                    sale_service, old_sale_order_line_data, line.price_subtotal + line.refund_amount)
                # line.refund_amount=refund_amount
                # line.promotion_back_amount=promotion_back_amount
                # line.order_id.update_price_by_odoo()

            so_line = {}
            so_line.update({
                '"register_type"': '\"' + (line.register_type or '') + '\"',
                '"product_id"': line.product_id and line.product_id.id or '""',
                '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                '"maximum_register_time"': line.product_category_id and line.product_category_id.maximum_register_time or 0,
                '"product_category_code"': '\"' + (
                            line.product_category_id and line.product_category_id.code or '') + '\"',
                '"product_category"': '\"' + (
                            line.product_category_id and line.product_category_id.display_name or '') + '\"',
                '"parent_product_id"': line.parent_product_id and line.parent_product_id.id or 0,
                '"parent_product_code"': '\"' + (
                            line.parent_product_id and line.parent_product_id.default_code or '') + '\"',
                '"parent_product"': '\"' + (line.parent_product_id and line.parent_product_id.name or '') + '\"',
                '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                '"up_price"': line.up_price or 0,
                '"refund_amount"': refund_amount,
                '"promotion_back_amount"': promotion_back_amount,
                '"time"': line.time or 0,
                '"register_untaxed_price"': line.register_untaxed_price or 0,
                '"register_taxed_price"': line.register_taxed_price or 0,
                '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                '"renew_taxed_price"': line.renew_taxed_price or 0,
                '"price_subtotal"': line.price_subtotal or 0,
                '"price_tax"': line.price_tax or 0,
                '"price_total"': line.price_total or 0,
                '"template"': '\"' + (line.template or '') + '\"',
                '"reseller"': '\"' + (line.reseller or '') + '\"',
                '"is_addons"': '\"' + (line.product_category_id and line.product_category_id.is_addons
                                       and 'True' or 'False') + '\"',
                '"os_template"': '\"' + (line.os_template or '') + '\"',
                '"id"': line.id,
                '"promotion_discount"': line.promotion_discount or 0,
                '"price_subtotal_no_discount"': line.price_subtotal_no_discount or 0,
                '"original_time"': line.original_time or 0,
                '"license"': line.license or 0,
            })
            order_line.append(so_line)
        so_dict.update({
            '"order_line"': order_line
        })
        data.append(so_dict)
        res.update({'"code"': 1, '"msg"': '"Get SO %s Successfully"' % so.name, '"data"': data})
        return res

    @api.model
    def get_so_renewed(self):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleOrder = self.env['sale.order']
        data = []
        # Check data
        # if not date:
        #     res.update({'"msg"': '"Create Date could be not empty"'})
        #     return res
        # try:
        #     create_date = datetime.strptime(str(date), DF)
        # except ValueError:
        #     return {'code': 0, 'msg': 'Invalid date yyyy-mm-dd',
        #             'data': {}}
        order_ids = SaleOrder.search([('type', '=', 'renewed'), ('fully_paid', '=', False)])
        for order in order_ids:
            if order.date_order and (
                    datetime.now().date() - datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').date()).days in (
            0, 3, 5, 7, 9, 15):
                item = {}
                item.update({
                    '"id"': order.id,
                    '"name"': '\"' + (order.name or '') + '\"',
                    '"partner_id"': order.partner_id and order.partner_id.id or '""',
                    '"partner_code"': '\"' + (order.partner_id and order.partner_id.ref or '') + '\"',
                    '"partner"': '\"' + (order.partner_id and order.partner_id.name or '') + '\"',
                    '"date_order"': '\"' + (order.date_order or '') + '\"',
                    '"coupon"': '\"' + (order.coupon or '') + '\"',
                    '"company_id"': order.company_id.id or 0,
                    '"amount_total"': order.amount_total or 0,
                    '"state"': '\"' + (order.state or '') + '\"',
                    '"contract_status"': '\"' + (order.contract_status or '') + '\"',
                    '"vat_status"': '\"' + (order.inv_status or '') + '\"'
                })
                order_line = []
                for line in order.order_line:
                    order_line.append({
                        '\"' + 'register_type' + '\"': '\"' + (line.register_type or '') + '\"',
                        '\"' + 'product_id' + '\"': line.product_id and line.product_id.id or '""',
                        '\"' + 'product_code' + '\"': '\"' + (
                                    line.product_id and line.product_id.default_code or '') + '\"',
                        '\"' + 'product' + '\"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                        '\"' + 'product_category_id' + '\"': line.product_category_id and line.product_category_id.id or '""',
                        '\"' + 'product_category_code' + '\"': '\"' + (
                                    line.product_category_id and line.product_category_id.code or '') + '\"',
                        '\"' + 'product_category' + '\"': '\"' + (
                                    line.product_category_id and line.product_category_id.display_name or '') + '\"',
                        '\"' + 'parent_product_id' + '\"': line.parent_product_id and line.parent_product_id.id or '""',
                        '\"' + 'parent_product_code' + '\"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.default_code or '') + '\"',
                        '\"' + 'parent_product' + '\"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.name or '') + '\"',
                        '\"' + 'time' + '\"': line.time or 0,
                        '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                        '\"' + 'register_untaxed_price' + '\"': line.register_untaxed_price or 0,
                        '\"' + 'register_taxed_price' + '\"': line.register_taxed_price or 0,
                        '\"' + 'renew_untaxed_price' + '\"': line.renew_untaxed_price or 0,
                        '\"' + 'renew_taxed_price' + '\"': line.renew_taxed_price or 0,
                        '\"' + 'price_subtotal' + '\"': line.price_subtotal or 0,
                        '\"' + 'price_tax' + '\"': line.price_tax or 0,
                        '\"' + 'price_total' + '\"': line.price_total or 0,
                        '\"' + 'template' + '\"': '\"' + (line.template or '') + '\"',
                        '\"' + 'reseller' + '\"': '\"' + (line.reseller or '') + '\"',
                    })
                item.update({'"order_line"': order_line})
                data.append(item)
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    def get_ref_partner(self):
        IrSequence = self.env['ir.sequence']
        name = IrSequence.next_by_code('id.sale.order')
        if self.env['sale.order'].search_count([('name', '=', name)]) > 0:
            return self.get_ref_partner()
        return name

    @api.model
    def create_so_and_invoice(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id,
                              lines=[], source='', ):

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
            try:
                invoice_id = order.with_context(force_company=customer_id.company_id.id).action_invoice_create()
                invoice_obj = self.env['account.invoice'].browse(invoice_id[0])
                if self.env.user.company_id <> order.partner_id.company_id:
                    domain = [
                        ('type', '=', 'sale'),
                        ('company_id', '=', order.partner_id.company_id.id),
                    ]
                    journal_id = self.env['account.journal'].search(domain, limit=1)
                    invoice_obj.write({
                        'journal_id': journal_id.id,
                        'account_id': order.partner_id.property_account_receivable_id and order.partner_id.with_context(
                            force_company=order.partner_id.company_id.id).property_account_receivable_id.id
                    })
                    if invoice_obj.tax_line_ids:
                        for line in invoice_obj.tax_line_ids:
                            tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                                  ('amount', '=', line.tax_id.amount),
                                                                  ('type_tax_use', '=', 'sale'),
                                                                  ('company_id', '=', order.partner_id.company_id.id)],
                                                                 limit=1)
                            line.write({
                                'account_id': tax.account_id.id
                            })
            except:
                return {'"code"': 0, '"msg"': '"Can`t create Invoice for SO %s"' % order.name}
            return {'"code"': 1, '"msg"': '"Create Order %s and Invoice Successful!"' % order.name,
                    '"invoice_id"': invoice_id[0]}
        except ValueError:
            return {'"code"': 0, '"msg"': '"Unknow Error!"', '"data"': {}}

    @api.model
    def create_so_and_noinvoice(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id,
                                lines=[], source=''):
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

            return {'"code"': 1, '"msg"': '"Create Order %s and Invoice Successful!"' % order.name}
        except ValueError:
            return {'"code"': 0, '"msg"': '"Unknow Error!"', '"data"': {}}

    @api.model
    def receive_money_and_subtract_money_idpage(self, invoice_id, cus_code, payment_amount, payment_journal,
                                                payment_date, memo, payment_method_so='', transaction_id='',
                                                team_code=''):
        CrmTeam = self.env['crm.team']
        res = {'"code"': 0, '"msg"': '""'}
        if not cus_code:
            res['"msg"'] = '"Customer Code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', cus_code)], limit=1)
        if not customer_id:
            res['"msg"'] = "Customer not exists."
            return res
        invoice = self.env['account.invoice'].browse(invoice_id)
        order_id = invoice.mapped('invoice_line_ids').mapped('sale_line_ids').mapped('order_id')
        # Update team for SO and Invoice: 19/7/2018
        if order_id and not order_id.team_id and not order_id.user_id and team_code:
            team_id = CrmTeam.search([('code', '=', team_code)], limit=1)
            if not team_id:
                self._cr.rollback()
                return {'"code': 0,
                        '"msg"': '"Saleteam {} is not found"'.format(team_code),
                        '"data"': {}}
            order_id.team_id = team_id.id
            invoice.team_id = team_id.id
        # ---------------- end 19/7/2018 ----------------- #
        if payment_amount > 0:
            memo = order_id and (order_id[0].name + ' - ' + (memo or '')) or (memo or '')
            receive_money = self.env['external.receive.money'].with_context(no_add_funds=True).receive_money(cus_code,
                                                                                                             payment_amount,
                                                                                                             payment_journal,
                                                                                                             payment_date,
                                                                                                             memo,
                                                                                                             transaction_id)
            if type(receive_money) is not dict or receive_money.get('"code"') <> 1:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Can not receive money for customer %s: %s"' % (cus_code, receive_money)}
        # Validate Invoice
        if not invoice:
            res['"msg"'] = '"Invoice not exists."'
            self._cr.rollback()
            return res
        if invoice.state == 'paid':
            res['"msg"'] = '"Invoice had paid."'
            self._cr.rollback()
            return res
        if invoice.state == 'draft':
            # try:
            invoice.with_context(force_company=invoice.company_id.id).action_invoice_open()
        # except Exception as e:
        #     res['"msg"'] = '"Can`t validate Invoice: %s"' % (e.message or repr(e))
        #     self._cr.rollback()
        # return res
        if invoice.state == 'open':
            if not invoice.outstanding_credits_debits_widget:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"%s: No have payment to add funds!!!"' % invoice.number}
            try:
                if invoice.outstanding_credits_debits_widget:
                    outstanding = json.loads(invoice.outstanding_credits_debits_widget)
                    # _logger.info('Check money ------------444444444444444444444444----------- %s' % invoice.outstanding_credits_debits_widget)
                    if outstanding:
                        for move in outstanding.get('content'):
                            if invoice.state == 'paid':
                                break
                            invoice.assign_outstanding_credit(move.get('id'))
                        _logger.info('------------Successful-----------')
                        if invoice.state <> 'paid':
                            self._cr.rollback()
                            return {'"code"': 0, '"msg"': '"Invoice have not yet been paid: %s"' % invoice.residual}
                        try:
                            if order_id and 'payment_method_so' in order_id.fields_get() and payment_method_so:
                                order_id.payment_method_so = payment_method_so
                        except Exception as e:
                            _logger.info('"Can not update payment method: %s"' % (e.message or repr(e)))
                            pass
                else:
                    self._cr.rollback()
                    return {'"code"': 0, '"msg"': '"No money!"'}
            except Exception as e:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Subtract Money Fail! %s"' % (e.message or repr(e))}
        # if invoice.state == 'paid':
        #     order_ids = invoice.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
        #     for order in order_ids:
        #         try:
        #             self.env['external.active.service'].active_service(order.name)
        #         except Exception as e:
        #             self._cr.rollback()
        #             return {'"code"': 0, '"msg"': '"Can`t active service in SO %s!: %s"' % (order.name, (e.message or repr(e)))}
        return {'"code"': 1, '"msg"': '"Payment successfully!"'}

    @api.model
    def create_invoice(self, so_id, customer_code):
        # Objects
        SaleOrder = self.env['sale.order']
        if not so_id:
            return {'"code"': 0, '"msg"': '"Order ID could not be empty"'}
        if not customer_code:
            return {'"code"': 0, '"msg"': '"Customer Code could not be empty"'}
        order = SaleOrder.browse(so_id)
        if not order or order.partner_id.ref <> customer_code:
            return {'"code"': 0,
                    '"msg"': '"Order name not exists or Order does not belong to the customer %s"' % customer_code}
        try:
            _logger.info('confirm SO %s ------------------------------' % order.name)
            if order.state == 'not_received':
                order.write({'state': 'draft'})
            if order.state == 'draft':
                if not order.order_line:
                    return {'"code"': 0, '"msg"': '"Sale Order: %s no have SO lines. Pls check again!!!"' % so_id}
                if order.order_line.filtered(lambda line: not line.price_updated):
                    order.update_price()
                    # order.order_line.filtered(lambda line: not line.price_updated).write({'price_updated': True})
                order.action_confirm()
            # else:
            if not order.invoice_ids:
                try:
                    invoice = order.with_context(force_company=order.partner_id.company_id.id).action_invoice_create()
                except Exception as e:
                    return {'"code"': 0,
                            '"msg"': '"Can`t create Invoice for SO %s: %s"' % (so_id, e.message or repr(e))}
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
                            tax = self.env['account.tax'].search(
                                [('amount_type', '=', line.tax_id.amount_type), ('amount', '=', line.tax_id.amount),
                                 ('type_tax_use', '=', 'sale'), ('company_id', '=', order.partner_id.company_id.id)],
                                limit=1)
                            line.write({
                                'account_id': tax.account_id.id
                            })
            else:
                invoice_id = order.invoice_ids[0]
            return {'"invoice_id"': invoice_id.id, '"msg"': '"Successfully"', '"code"': 1}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % e.message or repr(e)}

    @api.model
    def get_so_renewed_by_days_new(self, days=3, date='order_id.date_order', company_id=False):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        if date and date not in ('order_id.date_order', 'order_id.create_date'):
            return {'"code"': 0, '"msg"': '"Parameter Date just in `order_id.date_order` or `order_id.create_date`"'}
        date_condition_start = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d') + ' 00:00:00'
        date_condition_end = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d') + ' 23:59:59'
        # SaleOrder = self.env['sale.order']
        args = [('register_type', '=', 'renew'),
                ('order_id.state', 'in', ('not_received', 'draft', 'sale')),
                (date, '>=', date_condition_start),
                (date, '<=', date_condition_end), ]
        if company_id:
            args.append(('order_id.company_id', '=', company_id))
        else:
            args.append(('order_id.company_id', '!=', 4))
        if date == 'order_id.create_date':
            args += [('order_id.partner_id.company_type', '!=', 'agency'), ('order_id.type', '=', 'renewed'),
                     ('order_id.user_id', '=', False)]
            # args += [('order_id.type', '=', 'renewed'), ('order_id.team_id', '=', False)]
        SaleOrderLine = self.env['sale.order.line']
        # orders = SaleOrder.search([('type', '=', 'renewed'),
        #                            ('state', 'in', ('not_received', 'draft', 'sale')),
        #                            ('date_order', '>=', date_condition_start),
        #                            ('date_order', '<=', date_condition_end),
        #                            ('company_id', '=', company_id)])
        orders = SaleOrderLine.search(args).mapped('order_id')
        data = []
        try:
            for order in orders:
                so = {
                    '"id"': order.id,
                    '"name"': '\"' + order.name + '\"',
                    # '"customer_type"': '\"' + (order.partner_id.company_type or '') + '\"',
                    '"partner_id"': order.partner_id and order.partner_id.id or '""',
                    '"partner_code"': '\"' + (order.partner_id and order.partner_id.ref or '') + '\"',
                    '"partner_name"': '\"' + (order.partner_id and order.partner_id.name or '') + '\"',
                    '"partner_phone"': '\"' + (order.partner_id and order.partner_id.phone or '') + '\"',
                    '"partner_mobile"': '\"' + (order.partner_id and order.partner_id.mobile or '') + '\"',
                    '"partner_email"': '\"' + (order.partner_id and order.partner_id.email or '') + '\"',
                    '"no_sms"': order.partner_id and order.partner_id.no_sms and '"True"' or '"False"',
                    '"no_auto_call"': order.partner_id and order.partner_id.no_auto_call and '"True"' or '"False"',
                    '"partner_mst_cmnd"': '\"' + (
                                order.partner_id and order.partner_id.company_type == 'person' and order.partner_id.indentify_number or (
                                    order.partner_id.vat or '')) + '\"',
                    '"partner_address"': '\"' + (order.partner_id and order.partner_id.street or '' + (
                                order.partner_id.state_id and (', ' + order.partner_id.state_id.name) or '') + (
                                                             order.partner_id.country_id and (
                                                                 ', ' + order.partner_id.country_id.name) or '')) + '\"',
                    '"date_order"': '\"' + (order.date_order or '') + '\"',
                    '"create_date"': '\"' + (order.create_date or '') + '\"',
                    '"validity_date"': '\"' + (order.validity_date or '') + '\"',
                    '"coupon"': '\"' + (order.coupon or '') + '\"',
                    '"user_id"': order.user_id and order.user_id.id or '""',
                    '"team_id"': order.team_id and order.team_id.id or '""',
                    '"team_code"': '\"' + (order.team_id and order.team_id.code or '') + '\"',
                    '"fully_paid"': '\"' + (order.fully_paid and 'True' or 'False') + '\"',
                    '"type"': '\"' + (order.type or '') + '\"',
                    '"is_lock"': '\"' + (order.is_lock and 'True' or 'False') + '\"',

                    '"company_id"': order.company_id and order.company_id.id or '""',
                    '"amount_untaxed"': order.amount_untaxed or 0,
                    '"amount_tax"': order.amount_tax or 0,
                    '"amount_total"': order.amount_total or 0,

                    '"invoice"': order.invoice_ids and order.invoice_ids.ids or '"False"',
                    '"state"': '\"' + (order.state or 'draft') + '\"'
                }
                order_line = []
                for line in order.order_line:
                    so_line = {}
                    service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)], limit=1)
                    service_type = ''
                    parent_categ = self.env['external.create.service'].get_parent_product_category(
                        line.product_category_id)
                    if line.product_category_id.code[:1] == '.':
                        if '.vn' in line.product_category_id.code:
                            service_type = 'DMVN'
                        else:
                            service_type = 'DMQT'
                    else:
                        if parent_categ.code == 'CHILI':
                            service_type = 'CHILI'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTWIN':
                            service_type = 'HOSTWIN'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTLINUX':
                            service_type = 'HOSTLINUX'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTWP':
                            service_type = 'HOSTWP'
                        elif parent_categ.code == 'EMAIL':
                            service_type = 'EMAIL'
                        elif parent_categ.code == 'CLOUDSERVER':
                            service_type = 'CLOUDSERVER'
                        elif parent_categ.code == 'MICROSOFT':
                            service_type = 'MICROSOFT'
                    so_line.update({
                        '"register_type"': '\"' + (line.register_type or '') + '\"',

                        '"product_id"': line.product_id and line.product_id.id or '""',

                        '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',

                        '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',

                        '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',

                        '"product_category_code"': '\"' + (
                                    line.product_category_id and line.product_category_id.code or '') + '\"',

                        '"product_category"': '\"' + (
                                    line.product_category_id and line.product_category_id.display_name or '') + '\"',

                        '"parent_product_id"': line.parent_product_id and line.parent_product_id.id or '""',

                        '"parent_product_code"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.default_code or '') + '\"',

                        '"parent_product"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.name or '') + '\"',
                        '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                        '"time"': line.time or 0,
                        '"register_untaxed_price"': line.register_untaxed_price or 0,
                        '"register_taxed_price"': line.register_taxed_price or 0,
                        '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                        '"renew_taxed_price"': line.renew_taxed_price or 0,
                        '"price_subtotal"': line.price_subtotal or 0,
                        '"price_tax"': line.price_tax or 0,
                        '"price_total"': line.price_total or 0,
                        '"template"': '\"' + (line.template or '') + '\"',
                        '"reseller"': '\"' + (line.reseller or '') + '\"',
                        '"end_date"': '\"' + (line.end_date or '') + '\"',
                        '"start_date"': '\"' + (service_id and service_id.start_date or '') + '\"',

                        '"service_type"': '\"' + service_type + '\"',
                    })
                    order_line.append(so_line)
                so.update({'"order_line"': order_line})
                data.append(so)
            res.update({'"code"': 1, '"msg"': '"Get SO Successfully"', '"data"': data})
        except Exception as e:
            _logger.error("Get SO error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Get SO error: %s"' % (e.message or repr(e))}
        return res

    @api.model
    def get_so_renewed_by_days(self, days=3, date='order_id.date_order', company_id=False):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        if date and date not in ('order_id.date_order', 'order_id.create_date'):
            return {'"code"': 0, '"msg"': '"Parameter Date just in `order_id.date_order` or `order_id.create_date`"'}
        date_condition_start = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d') + ' 00:00:00'
        date_condition_end = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d') + ' 23:59:59'
        # SaleOrder = self.env['sale.order']
        args = [('register_type', '=', 'renew'),
                ('order_id.state', 'in', ('not_received', 'draft', 'sale')),
                (date, '>=', date_condition_start),
                (date, '<=', date_condition_end), ]
        if company_id:
            args.append(('order_id.company_id', '=', company_id))
        else:
            args.append(('order_id.company_id', '!=', 4))
        if date == 'order_id.create_date':
            args += [('order_id.partner_id.company_type', '!=', 'agency'), ('order_id.type', '=', 'renewed'),
                     ('order_id.user_id', '=', False)]
            # args += [('order_id.type', '=', 'renewed'), ('order_id.team_id', '=', False)]
        SaleOrderLine = self.env['sale.order.line']
        orders = SaleOrderLine.search(args).mapped('order_id')
        data = []
        try:
            for order in orders:
                so = {
                    '"id"': order.id,
                    '"name"': '\"' + order.name + '\"',
                    # '"customer_type"': '\"' + (order.partner_id.company_type or '') + '\"',
                    '"partner_id"': order.partner_id and order.partner_id.id or '""',
                    '"partner_code"': '\"' + (order.partner_id and order.partner_id.ref or '') + '\"',
                    '"partner_name"': '\"' + (order.partner_id and order.partner_id.name or '') + '\"',
                    '"partner_phone"': '\"' + (order.partner_id and order.partner_id.phone or '') + '\"',
                    '"partner_mobile"': '\"' + (order.partner_id and order.partner_id.mobile or '') + '\"',
                    '"partner_email"': '\"' + (order.partner_id and order.partner_id.email or '') + '\"',
                    '"sub_email"': '\"' + (order.partner_id and order.partner_id.sub_email_1 or '') + '\"',
                    '"no_sms"': order.partner_id and order.partner_id.no_sms and '"True"' or '"False"',
                    '"no_auto_call"': order.partner_id and order.partner_id.no_auto_call and '"True"' or '"False"',
                    '"partner_mst_cmnd"': '\"' + (
                                order.partner_id and order.partner_id.company_type == 'person' and order.partner_id.indentify_number or (
                                    order.partner_id.vat or '')) + '\"',
                    '"partner_address"': '\"' + (order.partner_id and order.partner_id.street or '' + (
                                order.partner_id.state_id and (', ' + order.partner_id.state_id.name) or '') + (
                                                             order.partner_id.country_id and (
                                                                 ', ' + order.partner_id.country_id.name) or '')) + '\"',
                    '"date_order"': '\"' + (order.date_order or '') + '\"',
                    '"create_date"': '\"' + (order.create_date or '') + '\"',
                    '"validity_date"': '\"' + (order.validity_date or '') + '\"',
                    '"coupon"': '\"' + (order.coupon or '') + '\"',
                    '"user_id"': order.user_id and order.user_id.id or '""',
                    '"team_id"': order.team_id and order.team_id.id or '""',
                    '"team_code"': '\"' + (order.team_id and order.team_id.code or '') + '\"',
                    '"fully_paid"': '\"' + (order.fully_paid and 'True' or 'False') + '\"',
                    '"type"': '\"' + (order.type or '') + '\"',
                    '"is_lock"': '\"' + (order.is_lock and 'True' or 'False') + '\"',
                    '"company_id"': order.company_id and order.company_id.id or '""',
                    '"amount_untaxed"': order.amount_untaxed or 0,
                    '"amount_tax"': order.amount_tax or 0,
                    '"amount_total"': order.amount_total or 0,
                    '"invoice"': order.invoice_ids and order.invoice_ids.ids or '"False"',
                    '"state"': '\"' + (order.state or 'draft') + '\"'
                }
                order_line = []
                for line in order.order_line:
                    so_line = {}
                    service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)], limit=1)
                    service_type = ''
                    parent_categ = self.env['external.create.service'].get_parent_product_category(
                        line.product_category_id)
                    if line.product_category_id.code[:1] == '.':
                        if '.vn' in line.product_category_id.code:
                            service_type = 'DMVN'
                        else:
                            service_type = 'DMQT'
                    else:
                        if parent_categ.code == 'CHILI':
                            service_type = 'CHILI'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTWIN':
                            service_type = 'HOSTWIN'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTLINUX':
                            service_type = 'HOSTLINUX'
                        elif line.product_category_id.parent_id and \
                                line.product_category_id.parent_id.code == 'HOSTWP':
                            service_type = 'HOSTWP'
                        elif parent_categ.code == 'EMAIL':
                            service_type = 'EMAIL'
                        elif parent_categ.code == 'CLOUDSERVER':
                            service_type = 'CLOUDSERVER'
                        elif parent_categ.code == 'MICROSOFT':
                            service_type = 'MICROSOFT'
                    so_line.update({
                        '"register_type"': '\"' + (line.register_type or '') + '\"',
                        '"product_id"': line.product_id and line.product_id.id or '""',
                        '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                        '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                        '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                        '"can_be_renew"': line.product_category_id and line.product_category_id.can_be_renew and '"True"' or '"False"',
                        '"product_category_code"': '\"' + (
                                    line.product_category_id and line.product_category_id.code or '') + '\"',
                        '"product_category"': '\"' + (
                                    line.product_category_id and line.product_category_id.display_name or '') + '\"',
                        '"parent_product_id"': line.parent_product_id and line.parent_product_id.id or '""',
                        '"parent_product_code"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.default_code or '') + '\"',
                        '"parent_product"': '\"' + (
                                    line.parent_product_id and line.parent_product_id.name or '') + '\"',
                        '"product_uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                        '"time"': line.time or 0,
                        '"register_untaxed_price"': line.register_untaxed_price or 0,
                        '"register_taxed_price"': line.register_taxed_price or 0,
                        '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                        '"renew_taxed_price"': line.renew_taxed_price or 0,
                        '"price_subtotal"': line.price_subtotal or 0,
                        '"price_tax"': line.price_tax or 0,
                        '"price_total"': line.price_total or 0,
                        '"template"': '\"' + (line.template or '') + '\"',
                        '"reseller"': '\"' + (line.reseller or '') + '\"',
                        '"end_date"': '\"' + (line.end_date or '') + '\"',
                        '"start_date"': '\"' + (service_id and service_id.start_date or '') + '\"',
                        '"is_stop"': service_id and service_id.is_stop and '"True"' or '"False"',
                        '"service_type"': '\"' + service_type + '\"',
                    })
                    order_line.append(so_line)
                so.update({'"order_line"': order_line})
                data.append(so)
            res.update({'"code"': 1, '"msg"': '"Get SO Successfully"', '"data"': data})
        except Exception as e:
            _logger.error("Get SO error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Get SO error: %s"' % (e.message or repr(e))}
        return res

    @api.model
    def add_log_internal(self, so, content):
        res = {'"code"': 0, '"msg"': '""'}
        SaleOrder = self.env['sale.order']
        if not so:
            return {'"code"': 0, '"msg"': '"Order Name could not be empty"'}
        order_id = SaleOrder.search([('name', '=', so)], limit=1)
        if not order_id:
            return {'"code"': 0, '"msg"': '"SALE ORDER %s is not found"' % so}
        if not content:
            return {'"code"': 0, '"msg"': '"Content could not be empty"'}
        try:
            order_id.message_post(body=content, subtype="mail.mt_note")
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t add log for SO %s: %s"' % (so, e.message or repr(e))}
        return {'"code"': 1, '"msg"': '"Successfully!!!"'}

    @api.model
    def get_so_to_call_msg_by_days(self, days=3):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        SaleOrder = self.env['sale.order']
        # date_condition = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d')
        # SaleOrderLine = self.env['sale.order.line']
        # orders = SaleOrderLine.search([('register_type', '=', 'renew'),
        #                                ('order_id.state', 'not in', ('cancel', 'paid')),
        #                                ('order_id.fully_paid', '=', False),
        #                                ('end_date', '=', date_condition)]).mapped('order_id')
        cr = self.env.cr
        cr.execute("""SELECT so.id
                      FROM sale_order so
                            JOIN sale_order_line sol ON sol.order_id = so.id
                            JOIN product_product pp ON pp.id = sol.product_id
                            JOIN sale_service ss ON ss.product_id = pp.id
                      WHERE so.state NOT IN ('cancel', 'paid') AND COALESCE(so.fully_paid, FALSE) = FALSE AND ss.end_date - NOW()::DATE = %s
					  GROUP BY so.id""",
                   (days,))
        orders = cr.dictfetchall()
        data = []
        try:
            for order in orders:
                order_id = SaleOrder.browse(order['id'])
                employee = order_id.user_id and order_id.user_id.mapped('employee_ids') or False
                so = {
                    '"name"': '\"' + order_id.name + '\"',
                    '"partner_id"': order_id.partner_id and order_id.partner_id.id or '""',
                    '"partner_code"': '\"' + (order_id.partner_id and order_id.partner_id.ref or '') + '\"',
                    '"partner_name"': '\"' + (order_id.partner_id and order_id.partner_id.name or '') + '\"',
                    '"partner_phone"': '\"' + (order_id.partner_id and order_id.partner_id.phone or '') + '\"',
                    '"partner_mobile"': '\"' + (order_id.partner_id and order_id.partner_id.mobile or '') + '\"',
                    '"partner_email"': '\"' + (order_id.partner_id and order_id.partner_id.email or '') + '\"',
                    '"company_id"': order_id.company_id and order_id.company_id.id or '""',
                    '"state"': '\"' + (order_id.state or 'draft') + '\"',
                    '"staff_name"': '\"' + (employee and employee[0].name or '') + '\"',
                    '"staff_email"': '\"' + (employee and employee[0].work_email or '') + '\"',
                    '"staff_mobile"': '\"' + (employee and employee[0].mobile_phone or '') + '\"',
                }
                order_line = []
                line_ids = order_id.order_line.filtered(lambda l: l.end_date and (
                            datetime.strptime(l.end_date, '%Y-%m-%d').date() - datetime.now().date()).days == days)
                for line in line_ids:
                    so_line = {}
                    so_line.update({
                        '"register_type"': '\"' + (line.register_type or '') + '\"',
                        '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                        '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                        '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                        '"product_category_code"': '\"' + (
                                    line.product_category_id and line.product_category_id.code or '') + '\"',
                        '"product_category"': '\"' + (
                                    line.product_category_id and line.product_category_id.display_name or '') + '\"',
                        '"end_date"': '\"' + (line.end_date or '') + '\"',
                    })
                    order_line.append(so_line)
                so.update({'"order_line"': order_line})
                data.append(so)
            res.update({'"code"': 1, '"msg"': '"Get SO Successfully"', '"data"': data})
        except Exception as e:
            _logger.error("Get SO error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Get SO error: %s"' % (e.message or repr(e))}
        return res

    @api.model
    def update_order_line_from_payment(self, order_name, team_code='', lines=[], update_price=0, split=0,
                                       used_promotion=0):
        _logger.info("update_order_line_from_payment")
        SaleOrder = self.env['sale.order']
        CRMTeam = self.env['crm.team']
        if not order_name:
            return {'"code"': 0, '"msg"': '"Order Name could not be empty"'}
        order_id = SaleOrder.search([('name', '=', order_name)], limit=1)
        if not order_id:
            return {'"code"': 0, '"msg"': '"Order not exists"'}
        if len(order_id) > 1:
            return {'"code"': 0, '"msg"': '"Many Orders."'}
        if order_id.state == 'completed':
            return {'"code"': 2, '"msg"': '"Order have activated"', 'data': order_id}
        if order_id.state not in ('not_received', 'draft', 'sale'):
            return {'"msg"': '"Order must be in Not Assign or Quotation or Processing"', '"code"': 0, 'data': order_id}
        if not lines:
            return {'"code"': 0, '"msg"': '"Order detail could not be empty"'}
        if 1 == 1:
            error_msg = ''
            # Prepare Order lines:
            # _logger.info("33333333333333333333")
            # if lines:
            order_lines = self.with_context(force_company=order_id.partner_id.company_id.id).create_order_lines(lines)

            if order_lines['msg']:
                error_msg += order_lines['msg']
            if error_msg:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Create Order Line error: %s"' % error_msg, '"data"': {}}
            # else:
            #     order_lines = {'line_ids': [(5,)]}
            if order_id.state == 'cancel':
                order_id.action_draft()
                online_team = CRMTeam.search([('code', 'in', ('OnlineHCM_Ocean', 'OnlineHN_Ocean')),
                                              ('company_id', '=', order_id.company_id.id)], limit=1)
                order_id.write({
                    'user_id': False,
                    'team_id': online_team and online_team.id or False
                })
            if order_id.state == 'sale' and not order_id.fully_paid:
                order_id.action_cancel()
                order_id.action_draft()
                if order_id.state <> 'draft':
                    self._cr.rollback()
                    return {'"code"': 0, '"msg"': '"Can`t set to draft SO."'}
            order_id.order_line = [(6, 0, [])]
            if order_id.order_line:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Can`t delete old SO line."'}
            if not order_id.team_id or not order_id.user_id and order_id.partner_id.company_type != 'agency':
                if not order_name:
                    self._cr.rollback()
                    return {'"code"': 0, '"msg"': '"Team could not be empty"'}
                team_id = CRMTeam.search([('code', '=', team_code)])
                if not team_id or len(team_id) > 1:
                    self._cr.rollback()
                    return {'"code"': 0, '"msg"': '"Team not exists or many teams."'}
                order_id.team_id = team_id.id
            order_id.write({
                'order_line': order_lines['line_ids']
            })
            if update_price:
                order_id.update_price_by_odoo()
            if used_promotion:
                order_id.use_promotion_account()
            if not split:
                return {'"msg"': '"Update Order Successfully"', '"code"': 1, 'data': order_id}
            else:
                return {'"msg"': '"Update Order Successfully"', '"code"': 1}

    def update_original_fields(self, so):
        so.original_subtotal = so.amount_untaxed
        so.original_total = so.amount_total

    @api.model
    def add_new_line(self, name, vals={}):
        order_id = self.env['sale.order'].search([('name', '=', name)])
        if not order_id:
            return {'"code"': 0, '"msg"': '"Order not found"'}
        if len(order_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s order"' % len(order_id)}
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        order_lines = self.create_order_lines(vals)
        if order_lines['msg']:
            return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
        cur_lines = order_id.order_line
        order_id.write({'order_line': order_lines['line_ids']})
        line_id = order_id.order_line - cur_lines
        # order_id.order_line.write({'price_updated': True})
        order_id.update_price_by_odoo()
        try:
            # if 1==1:
            order_id.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'cancel')).unlink()
            invoice_id = order_id.with_context(force_company=order_id.partner_id.company_id.id).action_invoice_create()
            invoice_obj = self.env['account.invoice'].browse(invoice_id[0])
            if self.env.user.company_id <> order_id.partner_id.company_id:
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', order_id.partner_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                invoice_obj.write({
                    'journal_id': journal_id.id,
                    'account_id': order_id.partner_id.property_account_receivable_id and order_id.partner_id.with_context(
                        force_company=order_id.partner_id.company_id.id).property_account_receivable_id.id
                })
                if invoice_obj.tax_line_ids:
                    for line in invoice_obj.tax_line_ids:
                        tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                              ('amount', '=', line.tax_id.amount),
                                                              ('type_tax_use', '=', 'sale'),
                                                              ('company_id', '=', order_id.partner_id.company_id.id)],
                                                             limit=1)
                        line.write({
                            'account_id': tax.account_id.id
                        })

            self.update_original_fields(order_id)
            return {'"code"': 1, '"msg"': '"Update successfully"', '"id"': line_id.id}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def add_new_line_new(self, name, vals={}):
        order_id = self.env['sale.order'].search([('name', '=', name)])
        if not order_id:
            return {'"code"': 0, '"msg"': '"Order not found"'}
        if len(order_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s order"' % len(order_id)}
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        order_lines = self.create_order_lines(vals)
        if order_lines['msg']:
            return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
        cur_lines = order_id.order_line
        order_id.write({'order_line': order_lines['line_ids']})
        line_id = order_id.order_line - cur_lines
        # order_id.order_line.write({'price_updated': True})
        order_id.update_price_by_odoo()
        self.update_original_fields(order_id)
        return {'"code"': 1, '"msg"': '"Update successfully"', '"id"': line_id.id}

    @api.model
    def add_new_line_api(self, name, vals={}):
        order_id = self.env['sale.order'].search([('name', '=', name)])
        if not order_id:
            return {'"code"': 0, '"msg"': '"Order not found"'}
        if len(order_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s order"' % len(order_id)}
        order_lines = self.create_order_lines(vals)
        if order_lines['msg']:
            return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
        order_id.write({'order_line': order_lines['line_ids']})
        # order_id.order_line.write({'price_updated': True})
        order_id.update_price_by_odoo()
        return {'"code"': 1, '"msg"': '"Update successfully"'}

    @api.model
    def update_line_new(self, id, vals={}):
        line_id = self.env['sale.order.line'].browse(id)
        order_id = line_id.order_id
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        try:
            # Get order line
            order_lines = self.create_order_lines(vals)
            if order_lines['msg']:
                return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
            # Update line
            line_id.write(list(order_lines['line_ids'][0])[2])
            order_id.update_price_by_odoo()
            return {'"code"': 1, '"msg"': '"Updated successfully"'}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def update_line(self, id, vals={}):
        line_id = self.env['sale.order.line'].browse(id)
        order_id = line_id.order_id
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        try:
            # Get order line
            order_lines = self.create_order_lines(vals)
            if order_lines['msg']:
                return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
            # Update line
            line_id.write(list(order_lines['line_ids'][0])[2])
            order_id.update_price_by_odoo()
            order_id.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'cancel')).unlink()
            invoice_id = order_id.with_context(force_company=order_id.partner_id.company_id.id).action_invoice_create()
            invoice_obj = self.env['account.invoice'].browse(invoice_id[0])
            if self.env.user.company_id <> order_id.partner_id.company_id:
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', order_id.partner_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                invoice_obj.write({
                    'journal_id': journal_id.id,
                    'account_id': order_id.partner_id.property_account_receivable_id and order_id.partner_id.with_context(
                        force_company=order_id.partner_id.company_id.id).property_account_receivable_id.id
                })
                if invoice_obj.tax_line_ids:
                    for line in invoice_obj.tax_line_ids:
                        tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                              ('amount', '=', line.tax_id.amount),
                                                              ('type_tax_use', '=', 'sale'),
                                                              ('company_id', '=', order_id.partner_id.company_id.id)],
                                                             limit=1)
                        line.write({
                            'account_id': tax.account_id.id
                        })
            return {'"code"': 1, '"msg"': '"Updated successfully"'}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def update_line_api(self, id, vals={}):
        line_id = self.env['sale.order.line'].browse(id)
        order_id = line_id.order_id
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        try:
            # Get order line
            order_lines = self.create_order_lines(vals)
            if order_lines['msg']:
                return {'"code"': 0, '"msg"': '"%s"' % order_lines['msg']}
            # Update line
            line_id.write(list(order_lines['line_ids'][0])[2])
            order_id.update_price_by_odoo()
            return {'"code"': 1, '"msg"': '"Updated successfully"'}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def delete_line(self, id):
        _logger.info("1111111111111111111111111111111")
        line_id = self.env['sale.order.line'].browse(id)
        order_id = line_id.order_id
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        if order_id.state == 'sale':
            order_id.action_cancel()
            order_id.action_draft()
        try:
            line_id.unlink()
            order_id.update_price_by_odoo()
            order_id.invoice_ids.filtered(lambda inv: inv.state in ('draft', 'cancel')).unlink()
            order_id.state = 'sale'
            if not order_id.order_line:
                return {'"code"': 1, '"msg"': '"Deleted successfully. Order no line, can`t create invoice"'}
            invoice_id = order_id.with_context(force_company=order_id.partner_id.company_id.id).action_invoice_create()
            invoice_obj = self.env['account.invoice'].browse(invoice_id[0])
            if self.env.user.company_id <> order_id.partner_id.company_id:
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', order_id.partner_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                invoice_obj.write({
                    'journal_id': journal_id.id,
                    'account_id': order_id.partner_id.property_account_receivable_id and order_id.partner_id.with_context(
                        force_company=order_id.partner_id.company_id.id).property_account_receivable_id.id
                })
                if invoice_obj.tax_line_ids:
                    for line in invoice_obj.tax_line_ids:
                        tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                              ('amount', '=', line.tax_id.amount),
                                                              ('type_tax_use', '=', 'sale'),
                                                              ('company_id', '=', order_id.partner_id.company_id.id)],
                                                             limit=1)
                        line.write({
                            'account_id': tax.account_id.id
                        })
            return {'"code"': 1, '"msg"': '"Deleted successfully"'}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def delete_line_api(self, id):
        _logger.info("1111111111111111111111111111111")
        line_id = self.env['sale.order.line'].browse(id)
        order_id = line_id.order_id
        if order_id.invoice_ids.filtered(lambda inv: inv.state in ('open', 'paid')):
            return {'"code"': 0, '"msg"': '"Invoice have validated or paid, can not update line."'}
        if order_id.state == 'sale':
            order_id.action_cancel()
            order_id.action_draft()
        try:
            line_id.unlink()
            order_id.update_price_by_odoo()
            order_id.state = 'sale'
            if not order_id.order_line:
                return {'"code"': 1, '"msg"': '"Deleted successfully. Order no line, can`t create invoice"'}
            return {'"code"': 1, '"msg"': '"Deleted successfully"'}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

