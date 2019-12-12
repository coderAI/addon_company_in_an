# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class check_product(models.Model):
    _name = 'check.product'
    _description = 'Check Product'


    def _default_sale_order_ids(self):
        sale_order_data = self.env['sale.order'].sudo().search([('state','in',['sale','paid','done','product hold'])],order="order_date asc")
        return sale_order_data.ids

    name = fields.Char('Name', default=lambda self: _('New'))
    active = fields.Boolean('Active', default=True)
    sale_order_ids = fields.Many2many('sale.order', column1 = 'check_product_id',
    column2 = 'sale_order_id', string = 'Sale order', default=_default_sale_order_ids)

    sale_order_line_ids = fields.One2many('sale.order.line', 'check_product_id')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    maximum_sale_order_line = fields.Integer('Limit Sale Order Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('work.order') or _('New')
        result = super(check_product, self).create(vals)
        return result


    @api.multi
    def btn_map_sale_order_line(self):
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_obj = self.env['sale.order']
        quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        sale_order_line = []
        for so in self.sale_order_ids:
            sale_order_line+=so.order_line.ids
            # sale_order_line_obj.search([('order_id.state', 'in', ['paid','done','sale']),
            #                                           ('check_maped', '=', False)],
            #                                          order="id asc")
        sale_order = self.sale_order_ids
        for cp in self:
            # tổng số lượng product cần cho đợt checking này
            if sale_order_line:
                sql = '''select product_id as product_id, sum(product_uom_qty) as total from sale_order_line 
                         where id in %s   group by product_id''' % (str(tuple(sale_order_line)))
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
                _logger.info("----------convet_sol_state_data-----------")
                _logger.info(convet_sol_state_data)
                _logger.info("---------------------")
                back_list_product = []
                wite_list_product = []
                convet_checking_list = {}
                convet_second_checking_list = {}
                for row in product_sol_checking:
                    sol_in_product = 0
                    if convet_sol_state_data.get(int(row.get('product_id'))):
                        sol_in_product = convet_sol_state_data.get(int(row.get('product_id')))

                    virtual_available = int(product_obj.browse(int(row.get('product_id'))).qty_available) - sol_in_product
                    _logger.info("----------virtual_available-----------")
                    _logger.info(virtual_available)
                    _logger.info(sol_in_product)
                    _logger.info(int(product_obj.browse(int(row.get('product_id'))).virtual_available))
                    _logger.info(int(product_obj.browse(int(row.get('product_id'))).qty_available))
                    _logger.info("---------------------")
                    if virtual_available >= int(row.get('total')):
                        wite_list_product.append(int(row.get('product_id')))
                        convet_checking_list.update({row.get('product_id'): int(virtual_available)})
                    else:
                        back_list_product.append(int(row.get('product_id')))
                        convet_second_checking_list.update({int(row.get('product_id')): int(virtual_available)})
                _logger.info("----------convet_second_checking_list-----------")
                _logger.info(convet_second_checking_list)
                _logger.info("---------------------")
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
                        _logger.info("----------vào----------")
                        checking_so.state = 'in product'
                    else:
                        _logger.info("----------back_list_product-----------")
                        _logger.info(back_list_product)
                        _logger.info("---------------------")
                        so_pass_second_check = True
                        for sol in checking_so.order_line:
                            _logger.info("----------sol-----------")
                            _logger.info(sol.product_id.id)
                            _logger.info(sol.product_uom_qty)
                            _logger.info("---------------------")
                            sol_checking_list = {}
                            if sol.product_id.id in back_list_product:
                                # nếu số lượng đang có không đủ cung cấp cho 1
                                # trong các sol line lập tức dừng check cập nhật trạng thái so
                                _logger.info(sol.product_uom_qty)
                                _logger.info(convet_second_checking_list.get(sol.product_id.id))
                                if sol.product_uom_qty > convet_second_checking_list.get(sol.product_id.id):
                                    checking_so.state = 'product hold'
                                    so_pass_second_check = False
                                    break
                                else:
                                    sol_checking_list.update({sol.product_id.id: sol.product_uom_qty})
                        # mấy thằng nằm trong back list nhưng được cái số hưởng vì mua sơm nên vẫng đủ cung cấp
                        if so_pass_second_check:
                            checking_so.state = 'in product'
                            # cấp nhật lại tổng số lượng đem check của backlist
                            for item_sale in sol_checking_list:
                                total_product_check = convet_second_checking_list.get(item_sale) - sol_checking_list.get(
                                    item_sale)
                                convet_second_checking_list.update({item_sale: total_product_check})

                sql_sale_order_line_ids = """
                                        UPDATE sale_order_line SET check_product_id = %s 
                                            WHERE id in %s
                                     """ % (cp.id, str(tuple(sale_order_line)))
                self._cr.execute(sql_sale_order_line_ids)