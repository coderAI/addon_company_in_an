# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        sale_obj = self.env['sale.order']
        for inv in self:
            if inv.origin:
                for so in sale_obj.search[('name', '=', inv.origin)]:
                    if so.state in ['draft', 'sent', 'sale']:
                        so.write({'state':'paid'})
        return res
