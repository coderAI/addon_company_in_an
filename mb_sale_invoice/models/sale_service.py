from odoo import api, fields, models


class SaleService(models.Model):
    _inherit = 'sale.service'

    subscription_id = fields.Char('Subscription ID')