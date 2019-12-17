# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64
import logging

_logger = logging.getLogger(__name__)

class loading_sale_order(models.TransientModel):
    _name = 'loading.sale.order'


    sale_order_ids = fields.Many2many('sale.order', 'sale_order_rel', 'loading_id', 'so_id',string="Sale Order", domain=[('state', '=', 'in product')])
    log = fields.Text()


    @api.multi
    def button_add_sale_order(self):
        work_order_line_obj= self.env['work.order.line']
        for so in self.sale_order_ids:
            for sol in so:
                for i in range(0, int(sol.product_uom_qty)):
                    work_order_line_obj.create({
                        'sale_order_line_id': sol.id,
                        'sale_order_id': so.id,
                        'work_order_id': self.id,
                        'name': str(i)+'/'+str(int(sol.product_uom_qty)),
                    })

