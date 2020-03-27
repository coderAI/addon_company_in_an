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
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    bank_transaction_id = fields.Many2one('bank.transaction',
                                          string='Bank Transactions')

    @api.multi
    def unlink(self):
        ctx = self._context
        if ctx.get('force_unlink'):
            if any(bool(rec.move_line_ids) for rec in self):
                raise UserError(_(
                    "You can not delete a payment that is already posted"))
            return super(models.Model, self).unlink()
        return super(AccountPayment, self).unlink()
