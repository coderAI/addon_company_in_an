# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_voice_line_ids = fields.One2many(
        'sale.order.voice', 'order_id', string='Voice Lines')
