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

import json

import logging

_logger = logging.getLogger(__name__)


class VnnicCustomer(models.Model):
    _name = 'vnnic.customer'

    partner_id = fields.Char(string='Partner')
    type = fields.Char(string='Type')
    seen_check = fields.Boolean('Seen')
    quantity = fields.Float(string="Quantity")
    rank = fields.Float(string="rank")
    percent = fields.Float(string="Percent")
    quantity_year = fields.Float(string="Quantity Year")
    quantity_month = fields.Float(string="Quantity Month")
    date = fields.Date(string='Date')




    @api.model
    def set_vnnic_customer(self,vals={}):
        data=[]
        messages='Successfully'
        code=200
        self.create(vals)
        res = {'code': code, 'messages':messages}
        return json.dumps(res)

