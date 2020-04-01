# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
import pytz
import logging as _logger

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_info_customer(self):
        vals = super(SaleOrder, self).get_info_customer()
        # _logger.info("---------------------- %s ----------------------", vals)
        for con in self.partner_id.contact_ids:
            if con.type == 'domain_manager':
                vals['domain'] = con
            elif con.type == 'technical_manager':
                vals['technical'] = con
            elif con.type == 'payment_manager':
                vals['payment'] = con
            elif con.type == 'helpdesk_manager':
                vals['helpdesk'] = con
        # _logger.info("********************** %s ----------------------", vals)
        return vals