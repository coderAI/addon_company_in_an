# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64
import logging
from odoo.exceptions import UserError, Warning
_logger = logging.getLogger(__name__)

class cancel_work_order(models.TransientModel):
    _name = 'cancel.work.order'
    reason_cancel_id = fields.Many2one('reason.cancel', string='Reason Cancel')

    @api.multi
    def button_confrim(self):
        work_order_line_obj = self.env['work.order.line']
        work_order_line = work_order_line_obj.browse(self._context['res_id'])
        work_order_line.reason_cancel_id = self.reason_cancel_id.id
        work_order_line.sale_order_line_id.state_new = 'draft'
        work_order_line.state = 'cancel'


class loading_sale_order(models.TransientModel):
    _name = 'loading.sale.order'

    def default_sale_order_line_ids(self):
        # ('id', 'not in', self._context['old_work_order_line_ids']),

        sale_order_data = self.env['sale.order.line'].sudo().search(
            [('order_id.state', '=', 'in product'),('state_new','=','draft')])
        return sale_order_data.ids

    sale_order_ids = fields.Many2many('sale.order', 'sale_order_rel', 'loading_id', 'so_id', string="Sale Order",
                                      domain=[('state', '=', 'in product')])
    sale_order_line_ids = fields.Many2many('sale.order.line', 'sale_order_line_rel', 'loading_id', 'so_line_id',
                                           string="Sale Order Lines",
                                           default=default_sale_order_line_ids,
                                           domain=[('state_new','=','draft'),('state_new', '=', 'draft'), ('order_id.state', '=', 'in product')])
    log = fields.Text()


    @api.multi
    def button_add_sale_order(self):
        work_order_line_obj= self.env['work.order.line']
        work_order_obj= self.env['work.order']
        if self._context['o2m_selection']:
            for sol in self._context['o2m_selection'].get('sale_order_line_ids').get('rows'):
                old_total = len(work_order_line_obj.search([('sale_order_line_id','=',sol.get('id')),('state','!=','cancel')]))
                if old_total < int(sol.get('product_uom_qty')):
                    for i in range(old_total, int(sol.get('product_uom_qty'))):
                        work_order_line_obj.create({
                            'sale_order_line_id': sol.get('id'),
                            'sale_order_id': sol.get('order_id'),
                            'work_order_id': self.env.context.get('res_id'),
                            'product_id': sol.get('product_id'),
                            'bar_code':  self.env['ir.sequence'].next_by_code('work.order.line'),
                            'name': str(i+1)+'/'+str(int(sol.get('product_uom_qty'))),
                        })
        else:
            raise Warning('You need to choose line before this action')
