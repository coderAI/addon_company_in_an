# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()

        for inv in self:
            for so in inv.invoice_line_ids.mapped('sale_line_ids.order_id'):
                if so.state in ['draft', 'sent', 'sale']:
                    so.write({'state': 'paid'})
        return res

    @api.model
    def generate_payments(self):
        payment_obj = self.env['account.payment'].sudo()
        journal_obj = self.env['account.journal'].sudo()
        account_payment_method_obj = self.env['account.payment.method'].sudo()
        payment_method_id = account_payment_method_obj.search([('code', '=', 'manual'),
                                                               ('payment_type', '=', 'inbound')])[0]
        journal_id = journal_obj.search([('type', '=', 'cash')])[0]
        payment_val = {
            'partner_id': self.partner_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_method_id': payment_method_id.id,
            'journal_id': journal_id.id,
            'amount': self.amount_total,
            'payment_date': self.date_invoice,
        }
        payment = payment_obj.create(payment_val)
        payment.invoice_ids = [self.id]
        payment.post()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def remove_move_reconcile(self):
        if self.env.context.get('invoice_id'):
            current_invoice = self.env['account.invoice'].browse(self.env.context['invoice_id'])
            for so in current_invoice.invoice_line_ids.mapped('sale_line_ids.order_id'):
                if so.state in ['in product', 'to delivery', 'done']:
                    raise Warning('You can not unreconcile with this sale order state :' + so.name)
                if so.state in ['paid', 'product hold']:
                    so.write({'state': 'sale'})
        return super(AccountMoveLine, self).remove_move_reconcile()
