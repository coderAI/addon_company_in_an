# -*- coding: utf-8 -*-
from odoo import api, fields, models
import json


class ExternalCreateCustomer(models.AbstractModel):

    _inherit = 'external.create.customer'

    @api.model
    def get_partner(self, res_partner_ref):
        data={}
        messages='Successfully'
        code=200
        res_partner_obj = self.env['res.partner']

        res_partner = res_partner_obj.search([('ref', '=', res_partner_ref)],limit=1)
        if res_partner.id:
            data = res_partner.read(['id', 'name', 'ref', 'company_type', 'street', 'website', 'date_of_birth', 'date_of_founding', 'vat',
                                     'indentify_number', 'accounting_ref', 'phone',
                                     'mobile', 'fax', 'email', 'sub_email_1', 'sub_email_2', 'password_idpage', 'no_sms', 'no_auto_call', 'gender',
                                     'representative'])[0]
            field_convert=['accounting_ref','phone',
                           'date_of_birth','date_of_founding','representative',
                           'indentify_number','website','fax','mobile',
                           'accounting_ref','sub_email_1','sub_email_2',
                           'street']
            for i_field in field_convert:
                if data[i_field] == False:
                    data[i_field] = ''
            data.update({
                'state_id': res_partner.state_id and res_partner.state_id.name or '',
                'company_id': res_partner.company_id and res_partner.company_id.id or '',
                'country_id': res_partner.country_id and res_partner.country_id.name or '',
                'title': res_partner.title and res_partner.title.name or '',
                'function': res_partner.function or '',
                'main_account': res_partner.with_context(force_company=res_partner.company_id.id).main_account or 0,
                'promotion_account': res_partner.with_context(force_company=res_partner.company_id.id).promotion_account_compute or 0,
            })
        else:
            messages='your customer ref not in system'
            code=402
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)

