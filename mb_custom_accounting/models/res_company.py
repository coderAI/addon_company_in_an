# -*- coding: utf-8 -*-



from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)



class AccountInvoice(models.Model):
    _inherit = "res.company"

    account_journal_id = fields.Many2one('account.journal', 'Promotion Journal')
    account_account_id = fields.Many2one('account.account', 'Promotion Account Receivable')
    product_id = fields.Many2one('product.product', 'Promotion Product')

