# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models
from datetime import date, datetime
import json
import logging

_logger = logging.getLogger(__name__)


class Coupon(models.Model):
    _inherit = "mb.coupon"

    @api.model
    def check_coupon_action(self, coupon, partner_code):
        messages='Successfully'
        code=200
        if coupon== False or coupon=='':
            return messages, code
        coupon_id = self.search([('name', '=', str(coupon).strip())], limit= 1)
        partner_id = self.env['res.partner'].search([('ref', '=', partner_code)], limit= 1)

        if not coupon_id.id:
            messages = "Coupon not exists"
        count_order = self.env['sale.order'].search_count([('fully_paid', '=', True),
                                                           ('coupon', '=', str(coupon).strip())])

        if count_order >= coupon_id.max_used_time:
            messages = "Coupon used exceeded number of times allowed"
            code = 402
        if datetime.now().strftime('%Y-%m-%d %H:%M:%S') > coupon_id.expired_date:
            messages = "Coupon used over expired time"
            code = 402
        promotion_id = coupon_id.promotion_id
        if promotion_id.status <> 'run':
            messages = "Promotion have stopped"
            code = 402
        if promotion_id.date_from > datetime.now().strftime('%Y-%m-%d %H:%M:%S') or \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S') > promotion_id.date_to:
            messages = "Promotion not yet started"
            code = 402
        for i in coupon_id:
            if i.partner_id:
                if i.partner_id.id != partner_id.id:
                    messages = "This coupon can not apply for this customer"
                    code = 402
        return messages, code

    @api.model
    def check_coupon_new(self, coupon, partner_code):
        data=[]
        messages, code = self.check_coupon_action(coupon, partner_code)
        res = {'code': code, 'messages': messages}
        return json.dumps(res)