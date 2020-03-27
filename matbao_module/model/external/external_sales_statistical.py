# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from datetime import datetime
from calendar import monthrange
import logging

class ExternalActiveService(models.AbstractModel):
    _description = 'Sales Statistical API'
    _name = 'external.statistical'

    @api.model
    def sales_statistical(self, team_code, month, year):
        res = {'"code"': 0, '"msg"': '""', '"data"': 0}
        AccountInvoice = self.env['account.invoice']
        SaleOrder = self.env['sale.order']
        if not team_code:
            res['"msg"'] = "Team Code could not be empty"
            return res
        team_id = self.env['crm.team'].search([('code', '=ilike', team_code)])
        if not team_id:
            res['"msg"'] = "Sale Team not exists"
            return res
        if not month or type(month) is not int:
            res['"msg"'] = 'Month could be not empty and must be integer'
            return res
        if not year or type(year) is not int:
            res['"msg"'] = 'Year could be not empty and must be integer'
            return res
        # invoice_ids = AccountInvoice.with_context(force_company=team_id.company_id.id).search([('team_id', '=', team_id.id), ('state', '=', 'paid'), ('type', '=', 'out_invoice'),
        #                                                                                        ('date_invoice', '>=', str(year)+'-'+str(month)+'-1'),
        #                                                                                        ('date_invoice', '<=', str(year)+'-'+str(month)+'-'+str(list(monthrange(year, month))[1]))])
        # refund_invoice_ids = AccountInvoice.with_context(force_company=team_id.company_id.id).search([('team_id', '=', team_id.id), ('state', '=', 'paid'), ('type', '=', 'out_refund'),
        #                                                                                        ('date_invoice', '>=', str(year)+'-'+str(month)+'-1'),
        #                                                                                        ('date_invoice', '<=', str(year)+'-'+str(month)+'-'+str(list(monthrange(year, month))[1]))])
        # # total = invoice_ids and sum(inv.amount_total for inv in invoice_ids.filtered(lambda i: i.date_invoice and
        # #                                                                                        datetime.strptime(i.date_invoice, '%Y-%m-%d').month == month and \
        # #                                                                                        datetime.strptime(i.date_invoice, '%Y-%m-%d').year == year)) or 0
        # total = invoice_ids and sum(inv.amount_total for inv in invoice_ids) or 0
        # # total_refund = refund_invoice_ids and sum(inv.amount_total for inv in refund_invoice_ids.filtered(lambda i: i.date_invoice and
        # #                                                                                        datetime.strptime(i.date_invoice, '%Y-%m-%d').month == month and \
        # #                                                                                        datetime.strptime(i.date_invoice, '%Y-%m-%d').year == year)) or 0
        # total_refund = refund_invoice_ids and sum(inv.amount_total for inv in refund_invoice_ids) or 0
        order_ids = SaleOrder.search([('team_id', '=', team_id.id), ('fully_paid', '=', True),
                                      ('date_order', '>=', str(year) + '-' + str(month) + '-1' + ' 00:00:00'),
                                      ('date_order', '<=', str(year)+'-'+str(month)+'-'+str(list(monthrange(year, month))[1]) + ' 23:59:59')])
        total = order_ids and sum(line.price_subtotal - line.up_price for line in order_ids.mapped('order_line')) or 0
        return {'"code"': 1,
                '"msg"': '"Successfully"',
                '"data"': total}

    @api.model
    def sales_statistical_detail(self, team_code, month, year, st_type='cs', limit=10):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        SaleOrder = self.env['sale.order']
        if not team_code:
            cr = self._cr
            cr.execute("""SELECT so.user_id, COALESCE(SUM(sol.price_subtotal - sol.up_price), 0) total
                          FROM sale_order_line sol
                            JOIN sale_order so ON so.id = sol.order_id
                            JOIN crm_team ct on ct.id = so.team_id
                            JOIN product_category pc ON pc.id = sol.product_category_id
                          WHERE so.user_id IS NOT NULL
                              AND ct.type = %s
                              AND so.fully_paid = TRUE
                              AND (so.date_order + '7 hour'::INTERVAL) BETWEEN %s AND %s
                          GROUP BY so.user_id
                          ORDER BY SUM(sol.price_subtotal - sol.up_price) DESC
                          LIMIT %s""",
                      (st_type, str(year) + '-' + str(month) + '-1' + ' 00:00:00',
                       str(year) + '-' + str(month) + '-' + str(list(monthrange(year, month))[1]) + ' 23:59:59', limit))
            rsl = cr.dictfetchall()
            data = []
            for item in rsl:
                data.append({
                    '"salesperson"': '"%s"' % self.env['res.users'].browse(item['user_id']).name,
                    '"total"': item['total']
                })
            return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}
        team_id = self.env['crm.team'].search([('code', '=ilike', team_code)])
        if not team_id:
            res['"msg"'] = "Sale Team not exists"
            return res
        if not month or type(month) is not int:
            res['"msg"'] = 'Month could be not empty and must be integer'
            return res
        if not year or type(year) is not int:
            res['"msg"'] = 'Year could be not empty and must be integer'
            return res
        data = []
        for member in team_id.member_ids:
            order_ids = SaleOrder.search([('team_id', '=', team_id.id),
                                          ('fully_paid', '=', True),
                                          ('user_id', '=', member.id),
                                          ('date_order', '>=', str(year) + '-' + str(month) + '-1' + ' 00:00:00'),
                                          ('date_order', '<=', str(year) + '-' + str(month) + '-' +
                                           str(list(monthrange(year, month))[1]) + ' 23:59:59')])
            total = order_ids and sum(line.price_subtotal - line.up_price for line in order_ids.mapped('order_line')) or 0
            data.append({
                '"salesperson"': '"%s"' % member.name,
                '"total"': total
            })
        cr = self._cr
        cr.execute("""SELECT so.user_id, COALESCE(SUM(sol.price_subtotal - sol.up_price), 0) AS total
                      FROM sale_order so
                          JOIN sale_order_line sol on sol.order_id = so.id
                          JOIN crm_team ct ON ct.id = so.team_id
                          JOIN res_users ru ON ru.id = so.user_id
                      WHERE so.user_id NOT IN %s
                          AND ct.id = %s
                          AND so.fully_paid = TRUE
                          AND (so.date_order + '7 hour'::INTERVAL) >= %s
                          AND (so.date_order + '7 hour'::INTERVAL) <= %s
                      GROUP BY so.user_id""",
                   (tuple(team_id.member_ids and team_id.member_ids.ids or []), team_id.id,
                    str(year) + '-' + str(month) + '-1' + ' 00:00:00',
                    str(year) + '-' + str(month) + '-' + str(list(monthrange(year, month))[1]) + ' 23:59:59'))
        other_order_ids = cr.dictfetchall()
        for order in other_order_ids:
            data.append({
                '"salesperson"': '"%s"' % self.env['res.users'].sudo().browse(order.get('user_id')).name,
                '"total"': order.get('total'),
            })
        return {'"code"': 1,
                '"msg"': '"Successfully"',
                '"data"': data}

    @api.model
    def service_statistical(self, team_code, month, year, categ_code, salesperson=''):
        res = {'"code"': 0, '"msg"': '""', '"data"': 0}
        # AccountInvoice = self.env['account.invoice']
        SaleOrder = self.env['sale.order']
        ProductCategory = self.env['product.category']
        ResUsers = self.env['res.users']
        # ProductProduct = self.env['product.product']
        # Check parameter
        args = [('fully_paid', '=', True)]
        if not team_code:
            res['"msg"'] = '"Team Code could not be empty"'
            return res
        team_id = self.env['crm.team'].search([('code', '=ilike', team_code)])
        if not team_id:
            res['"msg"'] = '"Sale Team not exists"'
            return res
        args += [('team_id', '=', team_id.id)]
        if not month or type(month) is not int:
            res['"msg"'] = '"Month could be not empty and must be integer"'
            return res
        if not year or type(year) is not int:
            res['"msg"'] = '"Year could be not empty and must be integer"'
            return res
        args += [('date_order', '>=', str(year) + '-' + str(month) + '-1' + ' 00:00:00'),
                  ('date_order', '<=', str(year) + '-' + str(month) + '-' + str(list(monthrange(year, month))[1]) + ' 23:59:59')]
        if not categ_code:
            res['"msg"'] = '"Category Code could be not empty"'
            return res
        categ_id = ProductCategory.search([('code', '=', categ_code)], limit=1)
        if not categ_id:
            res['"msg"'] = '"Product Category not exists"'
            return res
        if salesperson:
            user_id = ResUsers.search([('login', '=', salesperson)], limit=1)
            if not user_id:
                res['"msg"'] = '"SalesPerson not exists"'
                return res
            args += [('user_id', '=', user_id.id)]

        # invoice_ids = AccountInvoice.with_context(force_company=team_id.company_id.id).search([('team_id', '=', team_id.id), ('state', '=', 'paid'), ('type', '=', 'out_invoice'),
        #                                                                                        ('date_invoice', '>=', str(year)+'-'+str(month)+'-1'),
        #                                                                                        ('date_invoice', '<=', str(year)+'-'+str(month)+'-'+str(list(monthrange(year, month))[1]))])
        # refund_invoice_ids = AccountInvoice.with_context(force_company=team_id.company_id.id).search([('team_id', '=', team_id.id), ('state', '=', 'paid'), ('type', '=', 'out_refund'),
        #                                                                                        ('date_invoice', '>=', str(year)+'-'+str(month)+'-1'),
        #                                                                                        ('date_invoice', '<=', str(year)+'-'+str(month)+'-'+str(list(monthrange(year, month))[1]))])
        # # product_ids = invoice_ids and invoice_ids.filtered(lambda i: i.date_invoice and datetime.strptime(i.date_invoice, '%Y-%m-%d').month == month and \
        # #                                                                   datetime.strptime(i.date_invoice, '%Y-%m-%d').year == year).mapped('invoice_line_ids').mapped('product_id') or False
        # product_ids = invoice_ids and invoice_ids.mapped('invoice_line_ids').mapped('product_id') or False
        # # refund_product_ids = refund_invoice_ids and refund_invoice_ids.filtered(lambda i: i.date_invoice and datetime.strptime(i.date_invoice, '%Y-%m-%d').month == month and \
        # #                                                                                        datetime.strptime(i.date_invoice, '%Y-%m-%d').year == year).mapped('invoice_line_ids').mapped('product_id') or False
        # refund_product_ids = refund_invoice_ids and refund_invoice_ids.mapped('invoice_line_ids').mapped('product_id') or False
        # product_ids = product_ids and ProductProduct.search([('id', 'in', product_ids.ids), ('categ_id', 'child_of', categ_id.id)])
        # refund_product_ids = refund_product_ids and ProductProduct.search([('id', 'in', refund_product_ids.ids), ('categ_id', 'child_of', categ_id.id)])
        # product_count = product_ids and len(product_ids) or 0
        # refund_product_count = refund_product_ids and len(refund_product_ids) or 0
        category_ids = ProductCategory.search([('id', 'child_of', categ_id.id),
                                               ('is_addons', '=', False)])
        order_ids = SaleOrder.search(args)
        product_ids = order_ids and order_ids.mapped('order_line').filtered(lambda line: line.product_category_id in category_ids).mapped('product_id') or False
        product_count = product_ids and len(product_ids) or 0
        return {'"code"': 1,
                '"msg"': '"Successfully"',
                '"data"': product_count}

    @api.model
    def service_statistical_top(self, month, year, categ_code, st_type='cs', limit=10):
        res = {'"code"': 0, '"msg"': '""', '"data"': 0}
        ProductCategory = self.env['product.category']
        # Check parameter
        if not month or type(month) is not int:
            res['"msg"'] = '"Month could be not empty and must be integer"'
            return res
        if not year or type(year) is not int:
            res['"msg"'] = '"Year could be not empty and must be integer"'
            return res
        if categ_code:
            categ_id = ProductCategory.search([('code', '=', categ_code)])
        else:
            categ_id = ProductCategory.search([])
        if not categ_id:
            res['"msg"'] = '"Product Category not exists"'
            return res
        category_ids = ProductCategory.search([('id', 'child_of', categ_id.ids),
                                               ('is_addons', '=', False)])
        cr = self._cr
        cr.execute("""SELECT so.user_id, COUNT(*) total
                      FROM sale_order_line sol
                        JOIN sale_order so ON so.id = sol.order_id
                        JOIN crm_team ct ON ct.id = so.team_id
                        JOIN product_category pc ON pc.id = sol.product_category_id
                      WHERE ct.type = %%s
                          AND so.user_id IS NOT NULL
                          AND so.fully_paid = TRUE
                          AND (so.date_order + '7 hour'::INTERVAL) BETWEEN %%s AND %%s
                          %s
                      GROUP BY so.user_id
                      ORDER BY COUNT(*) DESC
                      LIMIT %%s""" %
                   (len(category_ids) > 1 and """AND sol.product_category_id IN %s""" or """AND sol.product_category_id = %s"""),
                   (st_type, str(year) + '-' + str(month) + '-1' + ' 00:00:00',
                    str(year) + '-' + str(month) + '-' + str(list(monthrange(year, month))[1]) + ' 23:59:59',
                    len(category_ids) > 1 and tuple(category_ids.ids) or (category_ids and category_ids.id or False),
                    limit))
        rsl = cr.dictfetchall()
        data = []
        for item in rsl:
            data.append({
                '"salesperson"': '"%s"' % self.env['res.users'].browse(item['user_id']).name,
                '"total"': item['total']
            })
        return {'"code"': 1,
                '"msg"': '"Successfully"',
                '"data"': data}

