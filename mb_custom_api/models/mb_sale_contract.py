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
    _inherit = 'mb.sale.contract'

    @api.model
    def api_get_data_contract(self, contract_id=0):
        values={}
        messages='Successfully'
        code=200
        contract = self.browse(contract_id)
        values = contract.read()
        #pdf = self.env['report'].get_pdf([contract.order_id.id], 'mb_sale_contract.sale_contract_mb')
        data_sale_order = contract.order_id.get_values()
        data_sale_order.update({
            'customer':data_sale_order.get('customer').name,
            'amount_tax':data_sale_order.get('order_id')[0].amount_tax,
            'amount_total':data_sale_order.get('order_id')[0].amount_total,
            'amount_subtotal':data_sale_order.get('order_id')[0].amount_untaxed,
            'order_name':data_sale_order.get('order_id')[0].name,
            'company_name':data_sale_order.get('company_id')[0].name,
            'company_id':data_sale_order.get('company_id')[0].id,
            'order_id':data_sale_order.get('order_id')[0].id,
                                })
        values[0].update(data_sale_order)
        res = {'code': code, 'messages': messages, 'data':values}
        return json.dumps(res)




    @api.model
    def create_contract_agency(self,sol_id):
        data={
            'contract_id':None,
            'contract_name':None,
              }
        messages='Successfully'
        code=200
        sol_obj = self.env['sale.order.line']
        contract_obj = self.env['mb.sale.contract']
        # sol = sol_obj.search([('name','=',sol_name)],limit=1)
        sol = sol_obj.browse(sol_id)
        if sol:
            for i in sol:
                i.create_contract()
                contract_id = contract_obj.search([('order_id', '=', i.order_id.id)], order='id desc',
                                                                  limit=1)
                for i_contract in contract_id:
                    data={
                    'contract_id':i_contract.id,
                    'contract_name':i_contract.name,
                      }
        else:
            messages = 'sale order line input not correct'
        res = {'code': code, 'messages':messages ,'data':data}
        return json.dumps(res)

    @api.model
    def push_file(self,contract_id,vals={}):
        data=[]
        messages='Successfully'
        code=200

        for i in self.browse(contract_id):
            for i_vals in vals:
                if i_vals.get('reseller_id_attachments'):
                    i.write({'reseller_id_attachments': [(0, 0,i_vals.get('reseller_id_attachments'))]
                             })
                if i_vals.get('attachments'):
                    i.write({'attachments': [(0, 0,i_vals.get('attachments'))]
                             })
            i.state = 'submit'
            i.is_online = True


        res = {'code': code, 'messages':messages}
        return json.dumps(res)