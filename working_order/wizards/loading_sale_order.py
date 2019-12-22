# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64
import logging

_logger = logging.getLogger(__name__)

class loading_sale_order(models.TransientModel):
    _name = 'loading.sale.order'

    def default_sale_order_line_ids(self):
        sale_order_data = self.env['sale.order.line'].sudo().search(
            [
                # ('state_new', '=', 'draft'),  # tam thơi # de co data
             ('order_id.state', '=', 'in product')])
        return sale_order_data.ids

    sale_order_ids = fields.Many2many('sale.order', 'sale_order_rel', 'loading_id', 'so_id', string="Sale Order",
                                      domain=[('state', '=', 'in product')])
    sale_order_line_ids = fields.Many2many('sale.order.line', 'sale_order_line_rel', 'loading_id', 'so_line_id',
                                           string="Sale Order Lines",
                                           default=default_sale_order_line_ids,
                                           domain=[('state_new', '=', 'draft'), ('order_id.state', '=', 'in product')])
    log = fields.Text()


    @api.multi
    def button_add_sale_order(self):
        work_order_line_obj= self.env['work.order.line']
        work_order_obj= self.env['work.order']

        for sol in self._context['o2m_selection']:
            old_total = len(work_order_line_obj.search([('sale_order_line_id','=',sol.id),('state','=','cancel')]))
            for i in range(old_total, int(sol.product_uom_qty)):
                work_order_line_obj.create({
                    'sale_order_line_id': sol.id,
                    'sale_order_id': sol.order_id.id,
                    'work_order_id': self.env.context.get('res_id'),
                    'product_id': sol.product_id.id,
                    'bar_code':  self.env['ir.sequence'].next_by_code('work.order.line'),
                    'name': str(i+1)+'/'+str(int(sol.product_uom_qty)),
                })

