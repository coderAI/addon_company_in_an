# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import json
from odoo import api, fields, models, _
import logging
import time
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class customer_contact(models.Model):
    _inherit = "customer.contact"
    update_mass_contact = fields.Many2many('mb.data.contact.type','mb_contact_customer_contact_rel','contact_id','contact_type_id',string='Contact Update')
    update_mass_contacts = fields.Many2many('customer.contact','mb_contact_mb_contact_rel','contact_id','contact_s_id',string='Contact Update')
    vn_indentify_number_date = fields.Date(String='Indentify Number Date',track_visibility='onchange')

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            name = record.name + ' - ' + record.contact_type.name
            res.append((record.id, name))
        return res

class res_partner(models.Model):
    _inherit = "res.partner"

    vn_indentify_number_date = fields.Date(String='Indentify Number Date',track_visibility='onchange')
    mb_verify_support_contract = fields.Date(String='Verify Date',track_visibility='onchange')
    mb_verify_contract = fields.Boolean(String='Verify',track_visibility='onchange')


    @api.multi
    def write(self, vals):

        check_update = False
        # for check and covert data
        full_data_udpate={}
        udpate_contact_list=[]
        children_customer = self.contact_ids.filtered(
            lambda c: c.type == self.info_types.code)
        if vals.get('contact_ids'):
            for i in vals.get('contact_ids'):
                if i[2]:
                    if i[2].get('update_mass_contacts'):
                        check_update = True
                        udpate_contact_list= i[2].get('update_mass_contacts')[0][2]
                        del i[2]['update_mass_contacts']
                        full_data_udpate = i[2]
                        break
        #for update
        if check_update:
            for i in vals.get('contact_ids'):
                if i[1] in udpate_contact_list:
                    i[2]= full_data_udpate
                    i[0]= 1

        return super(res_partner, self).write(vals)


    @api.multi
    def button_verify_contract(self):
        self.mb_verify_contract= True


    @api.multi
    def button_unverify_contract(self):
        self.mb_verify_contract= False