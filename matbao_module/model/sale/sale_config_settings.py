# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class SaleConfigSetting(models.TransientModel):
    _inherit = 'sale.config.settings'

    days_to_renew = fields.Integer('Days to Renew', required=True)
    url = fields.Char("URL", required=True)
    defaut_write_off_account_id = fields.Many2one(
        'account.account', 'Default Write-off Account',
        domain=[('deprecated', '=', False)])
    partner_id = fields.Many2one(
        'res.partner', 'Default Customer',
        domain="[('customer', '=', True)]")

    @api.multi
    def set_url(self):
        ir_values_obj = self.env['ir.values']
        if self.url:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', 'url', self.url)

    @api.model
    def set_default_days_to_renew(self):
        ir_values_obj = self.env['ir.values']
        if self.days_to_renew:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', "days_to_renew", self.days_to_renew)

    def set_default_write_off_account(self):
        ir_values_obj = self.env['ir.values']
        if self.defaut_write_off_account_id:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', "defaut_write_off_account_id",
                self.defaut_write_off_account_id.id)

    def set_default_partner_id(self):
        ir_values_obj = self.env['ir.values']
        if self.partner_id:
            ir_values_obj.sudo().set_default(
                'sale.config.settings', "partner_id",
                self.partner_id.id)

        