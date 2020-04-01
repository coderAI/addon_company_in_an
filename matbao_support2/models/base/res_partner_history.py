# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerHistory(models.Model):
    _name = "res.partner.history"

    customer_id = fields.Many2one('res.partner', 'Customer')
    user_id = fields.Many2one('res.users', 'Viewer')
    time_view = fields.Datetime(string='Time')
    info_view = fields.Char(string='Info View')
    type_id = fields.Many2one('mb.data.contact.type', string='Type')
