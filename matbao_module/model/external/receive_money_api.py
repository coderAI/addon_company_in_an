# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare

class ExternalReceiveMoney(models.AbstractModel):
    _description = 'Receive Money API'
    _name = 'external.receive.money'

    @api.model
    def receive_money_and_match_payment(self, cus_code, payment_amount, payment_journal, payment_date, memo, bank_code):
        res = {'code': 0, 'msg': ''}
        if not cus_code:
            res['msg'] = "Customer Code could not be empty"
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', cus_code)])
        if not customer_id:
            res['msg'] = "Customer not exists."
            return res
        if payment_amount == 0:
            res['msg'] = "Payment Amount must be difference 0"
            return res
        if not payment_journal:
            res['msg'] = "Payment Journal could not be empty"
            return res
        journal_id = self.env['account.journal'].search([('code', '=', payment_journal), ('type', '=', 'bank')])
        if not journal_id:
            res['msg'] = "Payment Journal must be bank"
            return res
        if not payment_date:
            res['msg'] = "Payment Date could not be empty"
            return res
        if not bank_code:
            res['msg'] = "Bank Transaction Code could not be empty"
            return res
        bank_id = self.env['bank.transaction'].search([('code', '=', bank_code), ('is_reconciled', '=', False)])
        if not bank_id:
            res['msg'] = "Bank Transaction must be not reconciled"
            return res
        payment_method = self.env.ref('account.account_payment_method_manual_in')
        payment_id = self.env['account.payment'].create({
            'journal_id': journal_id.id,
            'payment_method_id': payment_method.id or False,
            'payment_type': 'inbound',
            'payment_date': payment_date,
            'amount': payment_amount,
            'partner_id': customer_id.id,
            'partner_type': 'customer',
            'communication': memo,
            'receive_form': True,
        })
        # Match payment
        payment_name = self.env['ir.sequence'].with_context(ir_sequence_date=payment_id.payment_date).next_by_code(
            'account.payment.customer.invoice')
        payment_id.write({
            'name': payment_name,
            'bank_transaction_ids': [(4, bank_id.id)],
            'state': 'posted'
        })
        if payment_id.bank_transaction_ids:
            payment_id.write({
                'amount': sum(line.amount for line in payment_id.bank_transaction_ids)
            })
        # Update Bank Transaction and journal entries
        for line in payment_id.bank_transaction_ids:
            line.write({
                'is_reconciled': True,
                'payment_id': payment_id.id,
            })
            if line.account_move_id and line.account_move_id.line_ids:
                for item in line.account_move_id.line_ids:
                    item.write({
                        'partner_id': payment_id.partner_id.id
                    })
        # Update Main Account Customer
        # payment_id.partner_id.sudo().write({
        #     'main_account': payment_id.partner_id.main_account + payment_id.amount
        # })
        res['code'] = 1
        return res

    @api.model
    def receive_money(self, cus_code, payment_amount, payment_journal, payment_date, memo, transaction_id=''):
        res = {'"code"': 0, '"msg"': '""'}
        key = memo and memo[memo.find('['):memo.find(']')+1] or ''
        if key:
            pay_id = self.env['account.payment'].search_count([('communication', 'like', key)])
            if pay_id > 0:
                res['"msg"'] = '"Have exists payment key."'
                return res
        if not cus_code:
            res['"msg"'] = '"Customer Code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', cus_code)], limit=1)
        if not customer_id:
            res['msg'] = "Customer not exists."
            return res
        if payment_amount == 0:
            res['msg'] = "Payment Amount must be difference 0"
            return res
        if not payment_journal:
            res['"msg"'] = '"Payment Journal could not be empty"'
            return res
        journal_id = self.env['account.journal'].search([('code', '=', payment_journal), ('type', '=', 'bank')], limit=1)
        if not journal_id:
            res['"msg"'] = '"Payment Journal must be bank"'
            return res
        if not payment_date:
            res['msg'] = "Payment Date could not be empty"
            return res
        try:
            payment_method = self.env.ref('account.account_payment_method_manual_in')
            payment_id = self.env['account.payment'].with_context(force_company=customer_id.company_id.id).create({
                'journal_id': journal_id.id,
                'payment_method_id': payment_method.id or False,
                'payment_type': 'inbound',
                'payment_date': payment_date,
                'amount': payment_amount,
                'partner_id': customer_id.id,
                'partner_type': 'customer',
                'communication': memo,
                'receive_form': True,
                'transaction_id': transaction_id
            })
            if payment_id:
                payment_id.with_context(force_company=customer_id.company_id.id, no_add_funds=self._context.get('no_add_funds', False)).post()
        except Exception as e:
            self._cr.rollback()
            res['"msg"'] = '"Error: %s"' % (e.message or repr(e))
            return res
        res['"code"'] = 1
        return res