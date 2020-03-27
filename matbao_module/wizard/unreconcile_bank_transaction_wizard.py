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
from odoo import models, fields, api, SUPERUSER_ID


class UnreconcileBankTransactionWizard(models.TransientModel):
    _name = "unreconcile.bank.transaction.wizard"
    _description = "Unreconcile Bank Transaction Wizard"

    @api.multi
    def unreconcile_all(self):
        if self.env.uid <> SUPERUSER_ID:
            return True
        context = dict(self._context or {})
        bank_transaction_ids = self.env['bank.transaction'].browse(
            context.get('active_ids'))
        bank_transaction_ids.button_unreconcile()
