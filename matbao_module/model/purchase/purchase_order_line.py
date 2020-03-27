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
from ..sale.sale_order_line import REGISTER_TYPE


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    register_type = fields.Selection(REGISTER_TYPE, 'Register Type',
                                     readonly=True)
    template = fields.Char(string='Template')
