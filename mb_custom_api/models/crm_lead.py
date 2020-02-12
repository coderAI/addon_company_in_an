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

from odoo import api,  models
LIST_CONVERT = [
                ['team_id','crm.team','code'],
                ['state_id', 'res.country.state','code'],
                ['partner_id','res.partner','ref'],
                ['title','res.partner.title','name'],
                ['source_id','utm.source','name'],
                ['country_id','res.country','code']
               ]

class Lead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create_lead(self, vals={}):
        data=[]
        messages='Successfully'
        code=200
        for i in LIST_CONVERT:
            if vals.get(i[0]):
                vals.update({i[0]:self.env[i[1]].search([(i[2],'=',vals.get(i[0]))],limit=1).id})
        self.create(vals)
        res = {'code': code, 'messages':messages}
        return json.dumps(res)