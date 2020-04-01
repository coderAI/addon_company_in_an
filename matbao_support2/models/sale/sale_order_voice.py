# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderVoice(models.Model):
    _name = 'sale.order.voice'

    mobile = fields.Char(string='Mobile')
    invoice_time = fields.Datetime(string='Call Time')
    content = fields.Text(string='Content')
    result = fields.Text(string='Result')
    order_id = fields.Many2one('sale.order', string='Sale Order')
