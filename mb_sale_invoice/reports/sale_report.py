# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class SaleReport(models.Model):
    _inherit = 'sale.report'

    untaxed_revenue = fields.Float('Untaxed Revenue')
    revenue = fields.Float()

    def _select(self):
        select = super(SaleReport, self)._select()
        select += """
        , sum(l.price_subtotal / COALESCE(cr.rate, 1.0)) - sum(COALESCE(l.up_price, 0) / COALESCE(cr.rate, 1.0)) as untaxed_revenue,
        sum(l.price_total / COALESCE(cr.rate, 1.0)) - sum(COALESCE(l.up_price_wt, 0) / COALESCE(cr.rate, 1.0)) as revenue
        """
        return select
