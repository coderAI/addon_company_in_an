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

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        [('delivered', 'Invoiceable lines')],
        string='What do you want to invoice?',
        default=lambda *x: 'delivered', required=True)

    @api.multi
    def create_invoices(self):
        order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(order_id)
        for line in order.order_line:
            if not line.price_updated:
                raise Warning(_('''
                Some products are missing price. Please UPDATE PRICE for all
                sales order lines before creating customer invoices'''))
        return super(SaleAdvancePaymentInv, self).create_invoices()
