# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleConfigSetting(models.TransientModel):
    _inherit = 'sale.config.settings'

    split_bank_transaction = fields.Text(
        string='Send request "split bank transaction" to email')
    upgrade_service = fields.Text(
        string='Send request "upgrade service" to email')

    @api.multi
    def set_split_bank_transaction(self):
        ir_values_obj = self.env['ir.values']
        if self.split_bank_transaction:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', 'split_bank_transaction', self.split_bank_transaction)

    @api.multi
    def set_upgrade_service(self):
        ir_values_obj = self.env['ir.values']
        if self.upgrade_service:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', 'upgrade_service', self.upgrade_service)