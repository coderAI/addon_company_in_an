# -*- coding: utf-8 -*-
from odoo import fields, models


class ResellerCustomer(models.Model):
    _inherit = 'reseller.customer'

    microsoft_customer_id = fields.Char('Microsoft Customer ID')
