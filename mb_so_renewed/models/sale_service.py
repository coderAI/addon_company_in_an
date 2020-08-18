# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging as _logger
from odoo.exceptions import Warning

class SaleService(models.Model):
    _inherit = 'sale.service'

    @api.model
    def renew_sales_orders_by_days(self, days):
        try:
            self.env['mb.so.renewed'].api_final_so_renewed(days)
            return {'code': 1, 'msg': 'Successfully'}
        except Exception as e:
            _logger.error("SO Renewed error: %s" % (e.message or repr(e)))
            return {'code': 0, 'msg': 'Can not pour renewal order.'}