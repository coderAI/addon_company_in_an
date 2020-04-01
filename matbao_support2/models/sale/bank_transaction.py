# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
from datetime import timedelta, datetime


class SplitBankTransaction(models.Model):
    _inherit = "split.bank.transaction"

    @api.multi
    def action_open(self):
        ir_values_env = self.env['ir.values']
        splits = self.filtered(lambda l: l.state == 'draft')
        for record in splits:
            template = self.env.ref(
                'matbao_support2.split_bank_transaction_template')
            sbt_email = ir_values_env.get_default(
                'sale.config.settings', 'split_bank_transaction') or ''
            email_to_lst = []
            if sbt_email:
                email_to_lst = sbt_email.split(';')
                email_to_lst = ','.join(email_to_lst)
            template.send_mail(res_id=record.id, force_send=True, email_values={
                'email_from': '%s <%s>' % (self.company_id.name,self.company_id.email),
                'email_to': email_to_lst})
        rs = super(SplitBankTransaction, self).action_open()
        return rs
