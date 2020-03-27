# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
# from ..sale.sale_order_line import REGISTER_TYPE
import re
from odoo.exceptions import UserError

REGISTER_TYPE = [("register", "Setup"),
                 ("renew", "Renew"),
                 ("transfer", "Transfer"),
                 ("upgrade", "Upgrade")]

class ExternalCreateSO(models.AbstractModel):
    _description = 'Create SO API'
    _name = 'external.create.so'

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    def create_order_lines(self, vals):
        """
            TO DO:
            - Checking Order line vals
        """
        # Check type of data
        if type(vals) is not list:
            return {'"msg"': '"Invalid OrderLineEntity"'}

        ProductProduct = self.env['product.product']
        ProductCategory = self.env['product.category']
        ProductUom = self.env['product.uom']
        AccountTax = self.env['account.tax']
        ResCompany = self.env['res.company']

        error_msg = ''
        order_lines = []
        line_num = 1

        required_arguments = ['register_type', 'categ_code', 'product_code', 'product_name', 'qty', 'uom', 'reg_price_wot', 'reg_price_wt', 'reg_tax_amount',
                              'ren_price_wot', 'ren_price_wt', 'ren_tax_amount', 'tax', 'sub_total', 'company_id', 'template', 'reseller']
        non_required_arguments = ['parent_product_code', 'parent_product_name']

        for line in vals:
            if type(line) is not dict:
                return {
                    '"msg"': '"Invalid OrderLineEntity"'}
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
                error_msg += ('"### The required arguments: %s of"'
                              '" order line at line %s are not found! "') % (
                                   argument_error, line_num)
                return {'"msg"': error_msg}

            # Get non required arguments
            for argument in non_required_arguments:
                if line.get(argument):
                    line_vals[argument] = line.get(argument)

            # Check Register type
            if line_vals['register_type'] not in \
                    [re_type[0] for re_type in REGISTER_TYPE]:
                error_msg += ('"### Please check `register_type` of"'
                              '" order line at line %s "') % (line_num)

            # Check Product Category
            if not self._convert_str(line_vals['categ_code']):
                error_msg += '"### Can`t find product category at line %s "' % \
                    (line_num)
            product_categ = ProductCategory.search(
                [('code', '=', line_vals['categ_code'])])
            if not product_categ:
                error_msg += '"### Can`t find product category at line %s "' % \
                    (line_num)

            # Check Product Uom
            product_uom = self._convert_str(line_vals['uom'])
            if not product_uom:
                error_msg += (
                        '"### Product Uom `%s` at line %s is not found! "') % \
                        (product_uom, line_num)
            else:
                product_uom = ProductUom.search(
                    [('name', '=', product_uom)], limit=1)
                if not product_uom:
                    error_msg += (
                        '"### Product Uom `%s` at line %s is not found! "') % \
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
            # Check Company
            if line_vals['company_id']:
                company = ResCompany.browse(line_vals['company_id'])
                if not company:
                    error_msg += '"### Can`t find Company at line %s "' % line_num
            else:
                error_msg += '"### Company at line %s is not found"' % line_num

            # check tax
            tax_id = AccountTax.with_context(force_company=line_vals['company_id']).search([
                ('amount', '=', float(line_vals['tax'])), ('type_tax_use', '=', 'sale'), ('company_id', '=', line_vals['company_id'])], limit=1)
            if not tax_id:
                error_msg += '"### Can`t find Tax at line %s "' % (line_num)

            product_name = self._convert_str(line['product_name'])
            if not product_name:
                error_msg += '"### Invalid product name at line %s "' % (
                    line_num)

            # Check parent product
            if line_vals.get('parent_product_code', False):
                parent_product = ProductProduct.search([
                    ('default_code', '=',
                     line_vals.get('parent_product_code'))], limit=1)

                if not parent_product:
                    error_msg += (''"### Can't find parent product with code"''
                                  '" `%s` at line %s "') % \
                        (line_vals.get('parent_product_code'), line_num)

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
                product_ids = ProductProduct.sudo().create(new_product_vals)

            # Create oder lines
            if product_ids and not error_msg:
                new_line_vals = {
                    'register_type': line_vals['register_type'],
                    'product_id': product_ids.id,
                    'parent_product_id': parent_product and
                    parent_product.id or False,
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
                    'template': line_vals['template'],
                    'reseller': line_vals['reseller'],
                    'company_id': line_vals['company_id']
                    }
                # order_line = SaleOrderLine.create(new_line_vals)
                order_lines.append((0, 0, new_line_vals))
            line_num += 1
        return {'line_ids': order_lines, '"msg"': error_msg, '"data"': {}}

    @api.model
    def create_so(self, name, coupon, date_order, saleteam_code, order_type, customer_code, company_id, status, lines=[], source=''):
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
        # customer_vals = customer
        team_id = False

        if not name:
            # name = self.env['ir.sequence'].next_by_code('sale.order')
            return {'"code"': 0, '"msg"': '"Order name could not be empty"',
                    '"data"': {}}
        else:
            order = SaleOrder.search([('name', '=', name)], limit=1)
            if order:
                return {'"code"': 0, '"msg"': '"Order name already exits"',
                        '"data"': {}}
        if not date_order:
            return {'"code"': 0, '"msg"': '"Order Date could not be empty"',
                    '"data"': {}}
        if not order_type or order_type not in ['normal', 'renewed', 'mbn', 'id', 'chili']:
            return {'"code"': 0,
                    '"msg"': '"Order Type must be `normal`, `renewed`, `mbn`, `chili` or `id`"',
                    '"data"': {}}
        if not customer_code:
            return {'code': 0, '"msg"': '"Customer Code info could not be empty"',
                    '"data"': {}}
        if not company_id:
            return {'code': 0, '"msg"': '"Company ID could not be empty"',
                    '"data"': {}}
        else:
            if not self.env['res.company'].browse(company_id):
                return {'code': 0, '"msg"': '"Company ID %s not exist"' % company_id,
                        '"data"': {}}
        if source:
            source_id = self.env['utm.source'].search([('name', '=', source)])
        else:
            source_id = False
        if not status or status not in ('draft', 'not_received', 'sale', 'paid', 'completed', 'done', 'cancel'):
            return {'"code"': 0,
                    '"msg"': '"Status info could not be empty. "'
                           '\n"Status must be `not_received`(Not Received), `draft`(Quotation), `sale`(In Progress), `completed`(Wait Contract), `done`(Completed) or `cancel`(Cancelled)"',
                    '"data"': {}}
        if not lines:
            return {'"code"': 0, '"msg"': '"Order detail could not be empty"',
                    '"data"': {}}
        # Check date_order
        try:
            date_order = datetime.strptime(date_order, DTF) + \
                timedelta(hours=-7)
        except ValueError:
            return {'"code"': 0, '"msg"': '"Invalid order date yyyy-mm-dd h:m:s"',
                    '"data"': {}}

        # check sale team code
        if saleteam_code:
            team_id = CrmTeam.search([('code', '=', saleteam_code)], limit=1)
            if not team_id:
                return {'"code"': 0,
                        '"msg"': '"Saleteam {} is not found"'.format(saleteam_code
                                                                 ),
                        '"data"': {}}
        try:

            # Prepare Order lines:
            order_lines = self.create_order_lines(lines)
            if order_lines['"msg"']:
                error_msg += order_lines['"msg"']

            # Check Customer exits
            customer = self.env['res.partner'].search([('ref', '=', customer_code)])
            if not customer:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Customer not exists"'}

            if error_msg:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': error_msg, '"data"': {}}

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
                       'order_line': order_lines['line_ids']
                       }
            so_id = SaleOrder.with_context(force_company=company_id).create(so_vals)
            so_id.write({
                'original_subtotal': so_id.amount_untaxed,
                'original_total': so_id.amount_total,
            })
            return {'"code"': 1, '"msg"': '"Create Order %s Successful!"' % so_id.name, '"data"': {}}
        except ValueError:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Unknow Error!"', '"data"': {}}