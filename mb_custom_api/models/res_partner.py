# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json
import base64
import logging as _logger


class MBSaleContract(models.Model):
    _inherit = 'mb.sale.contract'

    @api.model
    def api_get_contract_signed(self, contract_id, ref):
        data=[]
        messages='Successfully'
        code=200
        contract = self.browse(contract_id)
        if not contract or contract.partner_id.ref != ref:
            messages = 'Contract is not exist'
            code=402
        else:
            for i in contract.attachments:
                data.append({
                    'name':i.name,
                    'type':i.type,
                    'mimetype':i.mimetype,
                    'data':i.datas,
                 })
                break
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)
class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def get_customer_contact(self,res_partner_ref):
        data=[]
        messages='Successfully'
        code=200
        res_partner_obj = self.env['res.partner']
        customer_contact_obj = self.env['customer.contact']
        res_partner = res_partner_obj.search([('ref', '=', res_partner_ref)],limit=1)
        if res_partner.id:
            data = customer_contact_obj.search([('parent_id','=',res_partner.id)]).read(['id','name', 'date_of_birth','contact_type',
                                                                                         'indentify_number','street','accounting_ref',
                                                                                         'sub_email_1','sub_email_2','website','vat',
                                                                                         'function','phone','email','mobile','fax','title','gender'
                                                                                         ])
            field_convert=['function','title','street','accounting_ref','sub_email_1','sub_email_2','website','fax','vat','gender']
            for i_data in data:
                if i_data:
                    for i_field in field_convert:
                        try:
                            if i_data[i_field] == False:
                                i_data[i_field] = None
                        except Exception:
                            i_data[i_field] = None
        else:
            messages='your customer ref not in system'
            code=402
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)