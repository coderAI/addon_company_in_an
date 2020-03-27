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
from datetime import datetime
from odoo.addons.mail.models.mail_template import format_tz


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def unlink(self):
        try:
            ctx = self._context
        except:
            return super(AccountInvoice, self).unlink()
        if ctx.get('force_unlink'):
            for invoice in self:
                if invoice.state not in ('draft', 'cancel'):
                    raise UserError(_(""" You cannot delete an invoice which is
                     not draft or cancelled. You should refund it instead."""))
            return super(models.Model, self).unlink()
        return super(AccountInvoice, self).unlink()

    @api.multi
    def action_invoice_open(self):
        # for inv in self:
        #     if inv.type == 'out_invoice' and inv.partner_id.main_account < inv.amount_total:
        #         raise UserError(_("Main Account %s not enough to validate invoice (%s)" % (inv.partner_id.main_account, inv.amount_total)))
        res = super(AccountInvoice, self).action_invoice_open()
        for inv in self:
            if inv.type == 'out_invoice':
                sale_ids = inv.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    sale_ids.write({'invisible_match_payment': True})
        return res

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals.get('state') == 'paid':
                sale_ids = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    for order in sale_ids:
                        order.write({
                            'fully_paid': True
                        })
                        if not order.order_line.filtered(lambda line: line.service_status == 'draft'):
                            order.write({
                                'state': 'completed'
                            })
                        # if order.date_order and self.date_invoice and (datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').month <> datetime.strptime(self.date_invoice, '%Y-%m-%d').month \
                        #     or datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').year <> datetime.strptime(self.date_invoice, '%Y-%m-%d').year):
                        # order.write({'date_order': self.date_invoice and format_tz(self.env, (self.date_invoice + ' ' + datetime.now().strftime('%H:%M:%S')), tz=self.env.user.tz, format='%Y%m%dT%H%M%SZ') or datetime.now()})
        return super(AccountInvoice, self).write(vals)
