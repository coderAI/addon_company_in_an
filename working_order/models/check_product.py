# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class check_product(models.Model):
    _name = 'check.product'
    _description = 'Check Product'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    sale_order_line_ids = fields.One2many('sale.order.line', 'check_product_id')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    maximum_sale_order_line = fields.Integer('Limit Sale Order Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def btn_map_sale_order_line(self):
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_obj = self.env['sale.order']
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        sale_order_line = sale_order_line_obj.search([('order_id.state', 'in', ['paid','done','sale']),
                                                      ('check_maped', '=', False)],
                                                     order="id asc")
        sale_order = sale_order_obj.search([('state', 'in', ['paid','done','sale']),
                                            ],
                                           order="order_date asc")
        # tổng số lượng product cần cho đợt checking này
        if sale_order_line:
            sql = '''select product_id as product_id, sum(product_uom_qty) as total from sale_order_line 
                     where id in %s   group by product_id''' % (str(tuple(sale_order_line.ids)))
            self._cr.execute(sql)
            product_sol_checking = self._cr.dictfetchall()

            # tổng số lượng product của những sale order line đang ở in product
            sql = '''select product_id as product_id, sum(product_uom_qty) as total from sale_order_line 
                     where state = 'in product'   group by product_id '''
            self._cr.execute(sql)
            product_sol_state_in_product = self._cr.dictfetchall()
            convet_sol_state_data = {}
            for row in product_sol_state_in_product:
                convet_sol_state_data.update({row.get('product_id'): row.get('total')})

            back_list_product = []
            wite_list_product = []
            convet_checking_list = {}
            convet_second_checking_list = {}
            for row in product_sol_checking:
                sol_in_product = 0
                if convet_sol_state_data.get(int(row.get('product_id'))):
                    sol_in_product = convet_sol_state_data.get(int(row.get('product_id')))
                virtual_available = int(product_obj.browse(int(row.get('product_id'))).virtual_available) - sol_in_product
                if virtual_available >= int(row.get('total')):
                    wite_list_product.append(int(row.get('product_id')))
                    convet_checking_list.update({row.get('product_id'): int(virtual_available)})
                else:
                    back_list_product.append(int(row.get('product_id')))
                    convet_second_checking_list.update({int(row.get('product_id')): int(virtual_available)})
            so_id_checking = False
            for checking_so in sale_order:
                so_id_skip = True
                # check danh sách đen toàn bộ sol lần 1
                for sol in checking_so.order_line:
                    if sol.product_id.id in back_list_product:
                        so_id_skip = False
                        break
                # nếu toàn bộ sol không nằm trong danh sách đen trực tiếp cập nhật luôn so state
                if so_id_skip:
                    checking_so.state = 'product hold'
                else:
                    so_pass_second_check = True
                    for sol in checking_so.order_line:
                        sol_checking_list = {}
                        if sol.product_id.id in back_list_product:
                            # nếu số lượng đang có không đủ cung cấp cho 1
                            # trong các sol line lập tức dừng check cập nhật trạng thái so
                            if sol.product_uom_qty > convet_second_checking_list.get(sol.product_id.id):
                                checking_so.state = 'in product'
                                so_pass_second_check = False
                                break
                            else:
                                sol_checking_list.update({sol.product_id.id: sol.product_uom_qty})
                    # mấy thằng nằm trong back list nhưng được cái số hưởng vì mua sơm nên vẫng đủ cung cấp
                    if so_pass_second_check:
                        checking_so.state = 'product hold'
                        # cấp nhật lại tổng số lượng đem check của backlist
                        for item_sale in sol_checking_list:
                            total_product_check = convet_second_checking_list.get(item_sale) - sol_checking_list.get(
                                item_sale)
                            convet_second_checking_list.update({item_sale: total_product_check})