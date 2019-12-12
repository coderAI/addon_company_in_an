# -*- coding: utf-8 -*-

from odoo import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
