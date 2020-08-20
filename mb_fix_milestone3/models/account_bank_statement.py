# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_round, float_repr
# import logging as _logger

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def action_update_statement_id(self):
        for line in self.mapped('line_ids').filtered(lambda l: not l.journal_entry_ids):
            if line.partner_id:
                company_currency = self.journal_id.company_id.currency_id
                st_line_currency = line.currency_id or line.journal_id.currency_id
                precision = st_line_currency and st_line_currency.decimal_places or company_currency.decimal_places
                params = {'company_id': self.env.user.company_id.id,
                          'account_payable_receivable': (line.journal_id.default_credit_account_id.id, line.journal_id.default_debit_account_id.id),
                          'amount': float_repr(float_round(line.amount, precision_digits=precision), precision_digits=precision),
                          'partner_id': line.partner_id.id,
                          'move_date': line.date
                          }
                cr = self.env.cr
                cr.execute("""  SELECT aml.id 
                                FROM account_move_line aml 
                                    JOIN account_account acc ON acc.id = aml.account_id 
                                WHERE aml.company_id = %(company_id)s
                                    AND aml.statement_id IS NULL 
                                    AND aml.account_id IN %(account_payable_receivable)s 
                                    AND aml.partner_id = %(partner_id)s 
                                    AND aml.date = %(move_date)s 
                                    AND (acc.internal_type = 'liquidity' AND debit = abs(%(amount)s::numeric))                                 
                                ORDER BY date_maturity asc, aml.id asc LIMIT 1 """, params)
                result = cr.dictfetchall()
                if result:
                    move_line = [ml['id'] for ml in result]
                    move_line_ids = self.env['account.move.line'].browse(move_line)
                    move_line_ids.write({'statement_id': False})
            # line.unlink()
        self.mapped('line_ids').filtered(lambda l: not l.journal_entry_ids).unlink()