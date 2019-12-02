# -*- coding: utf-8 -*-

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'


class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    work_order_line_ids = fields.Many2many('work.order.line', 'stock_move_work_order_rel', 'stock_move_id',
                                           'work_order_id', string='Work Order')
