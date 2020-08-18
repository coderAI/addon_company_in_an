# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ChiliAffiliateReport(models.Model):
    _name = "chili.affiliate.report"
    _inherit = "sale.report"
    afu_id = fields.Many2one('chili.affiliate.user', string='Affiliate User')
    lead_source = fields.Many2one('utm.source', string='Lead Source')
    lead_campaign = fields.Many2one('utm.campaign', string='Lead Campaign')
    referrer_name = fields.Char(string='Referrer name')
    aff_price_subtotal = fields.Float(string='Aff Subtotal')
    aff_partner = fields.Many2one('res.partner', string='Aff Partner')

    @api.depends('price_subtotal')
    def _compute_amount_subtotal(self):
        for sale in self:
            if sale.afu_id.aff_program_id.matrix_type == 'p':
                sale.aff_price_subtotal = sale.price_subtotal * (sale.afu_id.aff_program_id.amount/100)
            else:
                sale.aff_price_subtotal = sale.afu_id.aff_program_id.amount or 0


    @api.model_cr
    def init(self):
        self._table = "chili_affiliate_report"
