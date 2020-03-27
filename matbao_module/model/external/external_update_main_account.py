# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from datetime import datetime

class ExternalReceiveMoney(models.AbstractModel):
    _description = 'Update Main Account API'
    _name = 'external.update.main.account'

    @api.model
    def update_main_account(self, company_id, account_code, cus_code, journal, amount):
        res = {'code': 0, 'msg': ''}
        # Check Company
        if not company_id:
            res['msg'] = "Company could not be empty"
            return res
        if not self.env['res.company'].browse(company_id):
            res['msg'] = "Company not exists."
            return res
        # Check Customer
        if not cus_code:
            res['msg'] = "Customer Code could not be empty"
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', cus_code)])
        if not customer_id:
            res['msg'] = "Customer not exists."
            return res
        # Check Account
        if not account_code:
            res['msg'] = "Account Code could not be empty"
            return res
        account_id = self.env['account.account'].search([('code', '=', account_code), ('company_id', '=', company_id)])
        if not account_id:
            res['msg'] = "Account not exists."
            return res
        if not customer_id.with_context(force_company=company_id).property_account_receivable_id:
            res['msg'] = "Customer Receivable Account could not found."
            return res
        # Check Journal
        if not journal:
            res['msg'] = "Journal could not be empty"
            return res
        journal_id = self.env['account.journal'].search([('id', '=', journal), ('company_id', '=', company_id)])
        if not journal_id:
            res['msg'] = "Journal not exists"
            return res
        # Check Amount
        if amount <= 0:
            res['msg'] = "Amount must be larger than 0"
            return res

        move_vals = {
            'date': datetime.now().date(),
            'journal_id': journal_id.id,
            'line_ids': [(0, 0, {
                'name': 'Thu tiền khách hàng',
                'account_id': account_id.id,
                'debit': amount,
                'credit': 0,
                'partner_id': customer_id.id,
                'company_id': company_id,
            }), (0, 0, {
                'name': 'Phải thu của khách hàng',
                'account_id': customer_id.with_context(force_company=company_id).property_account_receivable_id.id,
                'debit': 0,
                'credit': amount,
                'date': datetime.now().date(),
                'partner_id': customer_id.id,
                'company_id': company_id,
            })],
            'company_id': company_id,
        }
        try:
            move = self.env['account.move'].with_context(force_company=company_id).create(move_vals)
        except:
            res['msg'] = "Can't create Payment"
            return res
        # Confirm payment
        try:
            move.post()
        except:
            res['msg'] = "Can't post Payment"
            return res
        # Update Main Account
        customer_id.write({
            'main_account': amount
        })
        res['code'] = 1
        return res