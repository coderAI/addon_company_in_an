# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare

class ExternalBankTransaction(models.AbstractModel):
    _description = 'Match Payment API'
    _name = 'external.match.payment'

    @api.model
    def match_payment_so(self, so_code, bank_code):
        res = {'code': 0, 'msg': ''}
        # context = self._context() or {}
        # context['active_model'] = 'sale.order'
        if not so_code:
            res['msg'] = "SO Code could not be empty"
            return res
        so = self.env['sale.order'].search([('name', '=', so_code), ('state', 'in', ('sale', 'paid'))])
        if not so:
            res['msg'] = "SO must be state In progress"
            return res
        if not bank_code:
            res['msg'] = "Bank Transaction Code could not be empty"
            return res
        bank_id = self.env['bank.transaction'].search([('code', '=', bank_code), ('is_reconciled', '=', False)])
        if not bank_id:
            res['msg'] = "Bank Transaction must be not reconciled"
            return res
        # Copy function from match payment wizard
        AccountInvoice = self.env['account.invoice']
        IrValues = self.env['ir.values']
        if so.fully_paid:
            res['msg'] = 'Sale order is fully paid'
            return res

        total_amount = bank_id.amount
        invoices_to_pay = AccountInvoice
        if so.invoice_ids:
            # filter invoices which state in ['draft', 'open']
            invoices_draft_open = so.invoice_ids.filtered(
                lambda r: r.type == "out_invoice" and
                          r.state in ['draft', 'open'])
            if invoices_draft_open:
                invoices_to_pay = invoices_draft_open[0]
                invoices_to_pay.sudo().action_invoice_open()

        if not invoices_to_pay:
            if total_amount < so.amount_total:
                res['msg'] = 'The bank transaction amount must be equal or larger than the total sales amount'
                return res
            invoice_ids = so.action_invoice_create()
            invoices_to_pay = AccountInvoice.browse(invoice_ids[0])
            invoices_to_pay.sudo().action_invoice_open()

        # reconcile bank transaction(s) and invoice
        amount_due = invoices_to_pay.residual
        default_acc_id = int(self.env['ir.property'].get(
            'property_account_receivable_id', 'res.partner'))

        inv_move_line_ids = invoices_to_pay.move_id.line_ids.filtered(
            lambda r: r.account_id.id == default_acc_id and
                      r.reconciled is False)[0]
        bank_vals = {'is_reconciled': True,
                     'order_id': so.id,
                     'invoice_id': invoices_to_pay.id}

        acc_move_line_ids = bank_id.mapped('account_move_id.line_ids')
        move_line_ids = acc_move_line_ids.filtered(
            lambda r: r.account_id.id == default_acc_id and
                      r.reconciled is False)
        acc_move_line_ids.write({'partner_id': so.partner_id.id})
        if float_compare(total_amount, amount_due, precision_digits=3) > 0:
            # reconcile with writeoff
            write_off_account_id = self.env['account.account'].browse(
                int(IrValues.get_default(
                    'sale.config.settings', 'defaut_write_off_account_id')))
            if not write_off_account_id:
                res['msg'] = "Please set default write-off account at  menu: Sale --> Configuration --> Settings --> Default Write-off Account."
            writeoff = (move_line_ids + inv_move_line_ids).sudo().reconcile(
                write_off_account_id, bank_id.journal_id)
            bank_vals.update({
                'writeoff_journal_id': writeoff.move_id.id
            })
        else:
            (move_line_ids + inv_move_line_ids).sudo().reconcile()
        bank_id.write(bank_vals)
        res['code'] = 1
        return res