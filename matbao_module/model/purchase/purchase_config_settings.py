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
from odoo import fields, models, api, _
from odoo.exceptions import Warning


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    partner_id = fields.Many2one(
        'res.partner', string='Default Vendor',
        domain=[('supplier', '=', True)], required=True)

    @api.multi
    def set_partner_id_defaults(self):
        ir_values_obj = self.env['ir.values']
        if self.partner_id:
            ir_values_obj.sudo().set_default(
                'purchase.order', "partner_id", self.partner_id.id)
            ir_values_obj.sudo().set_default(
                'purchase.config.settings', 'partner_id', self.partner_id.id)
