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
from odoo.tools import float_compare
from datetime import datetime


class MatchPaymentWizard(models.TransientModel):
    _name = "match.payment.wizard"

    bank_transaction_ids = fields.Many2many(
        'bank.transaction', string='Bank Transaction Lines')

    @api.multi
    def button_match_payment(self):
        if not self.bank_transaction_ids:
            raise Warning(_("Pls choose bank transaction!!!"))
        # SaleOrder = self.env['sale.order'].sudo()
        SaleOrder = self.env['sale.order']
        AccountInvoice = self.env['account.invoice']
        IrValues = self.env['ir.values']
        order_id = self._context.get('order_id', False)
        if not order_id:
            return False
        so = SaleOrder.browse(order_id)

        if so.fully_paid:
            raise Warning(_('Sale order is fully paid'))

        # calculate total amount of bank transactions
        total_amount = 0.0
        for line in self.bank_transaction_ids:
            total_amount += line.amount

        if total_amount < so.amount_total or total_amount - so.amount_total > 100000:
            raise Warning(_('The bank transaction amount must '
                            'be equal or no larger than 100,000 the '
                            'total sales amount'))

        default_acc_id = int(self.env['ir.property'].get(
            'property_account_receivable_id', 'res.partner'))
        acc_move_line_ids = \
            self.bank_transaction_ids.mapped('account_move_id.line_ids')
        move_line_ids = acc_move_line_ids.filtered(
            lambda r: r.account_id.id == default_acc_id and
                      r.reconciled is False)
        acc_move_line_ids.write({'partner_id': so.partner_id.id})

        invoices_to_pay = AccountInvoice
        if so.invoice_ids:
            # filter invoices which state in ['draft', 'open']
            invoices_draft_open = so.invoice_ids.filtered(
                lambda r: r.type == "out_invoice" and
                r.state in ['draft', 'open'])
            if invoices_draft_open:
                invoices_to_pay = invoices_draft_open[0]
                invoices_to_pay.write({
                    'date_invoice': datetime.now().date()
                })
                invoices_to_pay.sudo().with_context(force_company=so.partner_id.company_id.id).action_invoice_open()

        if not invoices_to_pay:
            invoice_ids = so.with_context(force_company=so.partner_id.company_id.id).action_invoice_create()
            invoices_to_pay = AccountInvoice.browse(invoice_ids[0])
            invoices_to_pay.sudo().with_context(force_company=so.partner_id.company_id.id).action_invoice_open()

        # reconcile bank transaction(s) and invoice
        amount_due = invoices_to_pay.residual
        # default_acc_id = int(self.env['ir.property'].get(
        #     'property_account_receivable_id', 'res.partner'))

        inv_move_line_ids = invoices_to_pay.move_id.line_ids.filtered(
            lambda r: r.account_id.id == default_acc_id and
            r.reconciled is False)[0]
        bank_vals = {'is_reconciled': True,
                     'order_id': so.id,
                     'invoice_id': invoices_to_pay.id}

        # acc_move_line_ids = \
        #     self.bank_transaction_ids.mapped('account_move_id.line_ids')
        # move_line_ids = acc_move_line_ids.filtered(
        #         lambda r: r.account_id.id == default_acc_id and
        #         r.reconciled is False)
        # acc_move_line_ids.write({'partner_id': so.partner_id.id})
        if float_compare(total_amount, amount_due, precision_digits=3) > 0:
            # # reconcile with writeoff
            # write_off_account_id = self.env['account.account'].browse(
            #     int(IrValues.get_default(
            #         'sale.config.settings', 'defaut_write_off_account_id')))
            # if not write_off_account_id:
            #     raise Warning(_("Please set default write-off account at"
            #                     " menu: Sale --> Configuration --> "
            #                     "Settings --> Default Write-off Account."))
            # writeoff = (move_line_ids + inv_move_line_ids).sudo().with_context(force_company=so.partner_id.company_id.id).reconcile(
            #     write_off_account_id, self.bank_transaction_ids[0].journal_id)
            # bank_vals.update({
            #     'writeoff_journal_id': writeoff.move_id.id
            #     })
            payment_method = self.env.ref('account.account_payment_method_manual_in')
            payment_name = self.env['ir.sequence'].with_context(ir_sequence_date=datetime.now().date().strftime('%Y-%m-%d')).next_by_code('account.payment.customer.invoice')
            # payment_id = self.env['account.payment'].sudo().with_context(force_company=so.partner_id.company_id.id).create({
            payment_id = self.env['account.payment'].with_context(force_company=so.partner_id.company_id.id).create({
                'name': payment_name,
                'journal_id': self.bank_transaction_ids[0].journal_id.id,
                'payment_method_id': payment_method.id or False,
                'payment_type': 'inbound',
                'payment_date': datetime.now().date(),
                'amount': sum(pay.amount for pay in self.bank_transaction_ids),
                'partner_id': so.partner_id.id,
                'partner_type': 'customer',
                'communication': 'Auto add funds to customer when match payment',
                'receive_form': True,
                'bank_transaction_ids': [(4, line.id) for line in self.bank_transaction_ids],
                'state': 'posted'
            })
            # so.partner_id.sudo().write({
            #     'main_account': so.partner_id.main_account + payment_id.amount
            # })
            for move in move_line_ids:
                invoices_to_pay.sudo().with_context(force_company=so.partner_id.company_id.id).assign_outstanding_credit(move.id)
        else:
            (move_line_ids + inv_move_line_ids).sudo().with_context(force_company=so.partner_id.company_id.id).reconcile()
        self.bank_transaction_ids.write(bank_vals)
        return invoices_to_pay
