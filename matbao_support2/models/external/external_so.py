# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
import re
from odoo.exceptions import UserError
import logging as _logger
import json


class ExternalSO(models.AbstractModel):
    _inherit = 'external.so'

    @api.model
    def add_log_internal(self, so, mobile, invoice_time, content, result):
        res = {'"code"': 0, '"msg"': '""'}
        SaleOrder = self.env['sale.order']
        SaleOrderVoice = self.env['sale.order.voice']
        if not so:
            return {'"code"': 0, '"msg"': '"Order Name could not be empty"'}
        order_id = SaleOrder.search([('name', '=', so)], limit=1)
        if not order_id:
            res['"msg"'] = '"SALE ORDER `{}` is not found"'.format(so)
            return res
        if not mobile:
            return {'"code"': 0, '"msg"': '"Mobile could not be empty"'}
        if not invoice_time:
            return {'"code"': 0, '"msg"': '"Call Time could not be empty"'}
        if not content:
            return {'"code"': 0, '"msg"': '"Content could not be empty"'}
        if not result:
            return {'"code"': 0, '"msg"': '"Result could not be empty"'}
        # Check invoice_time
        try:
            invoice_time = datetime.strptime(invoice_time, DTF) + \
                timedelta(hours=-7)
        except ValueError:
            return {'"code"': 0, '"msg"': '"Invalid Call Time yyyy-mm-dd h:m:s"',
                    '"data"': {}}
        try:
            existed_voice = SaleOrderVoice.search(
                [('order_id', '=', order_id.id),
                 ('invoice_time', '=', datetime.strftime(invoice_time, DTF)),
                 ('mobile', '=', mobile)])
            if not existed_voice:
                voice_vals = {'order_id': order_id.id,
                              'mobile': mobile,
                              'invoice_time': invoice_time,
                              'content': content,
                              'result': result}
                SaleOrderVoice.create(voice_vals)
            else:
                return {'"code"': 0, '"msg"': '"Existed Value!!!"'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t add log for SO %s: %s"' % (
                so, e.message or repr(e))}
        return {'"code"': 1, '"msg"': '"Successfully!!!"'}
