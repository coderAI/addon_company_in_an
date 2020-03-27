# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re

class ExternalCRM(models.AbstractModel):
    _description = 'CRM API'
    _name = 'external.crm'

    @api.model
    def create_lead(self, lead_vals={}):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResUsers = self.env['res.users']
        ResPartner = self.env['res.partner']
        ResPartnerTitle = self.env['res.partner.title']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        UtmSource = self.env['utm.source']
        CrmTeam = self.env['crm.team']
        CrmLead = self.env['crm.lead']
        # Check type parameter
        if not lead_vals or type(lead_vals) is not dict:
            return {'"msg"': '"Leads Vals could not be empty and must be dict"'}
        # Check data Leads Vals
        lead_dict = {'type': 'lead'}
        # Check name
        if not lead_vals.get('name', ''):
            return {'"msg"': '"Lead Name could not be empty"'}
        lead_dict.update({
            'name': lead_vals.get('name')
        })
        list_fields = ['street', 'street2', 'city', 'zip', 'company_name', 'contact_name', 'function', 'phone', 'email_from', 'mobile', 'fax', 'description', 'referred']
        for field in list_fields:
            if not lead_vals.get(field):
                continue
            lead_dict.update({field: lead_vals.get(field)})
        # Check Customer
        if lead_vals.get('partner_id'):
            customer_id = ResPartner.search([('ref', '=', lead_vals.get('partner_id'))], limit=1)
            if customer_id:
                lead_dict.update({'partner_id': customer_id.id})
        # Check Salesperson
        lead_dict.update({'user_id': False})
        if lead_vals.get('user_id'):
            user_id = ResUsers.search([('login', '=', lead_vals.get('user_id'))], limit=1)
            if user_id:
                lead_dict.update({'user_id': user_id.id})
        # Check SalesTeam
        lead_dict.update({'team_id': False})
        if lead_vals.get('team_id'):
            team_id = CrmTeam.search([('code', '=', lead_vals.get('team_id'))], limit=1)
            if team_id:
                lead_dict.update({'team_id': team_id.id})
        # Check Company
        if lead_vals.get('company_id'):
            company_id = ResCompany.browse(lead_vals.get('company_id'))
            if company_id:
                lead_dict.update({'company_id': company_id.id})
        # Check State
        if lead_vals.get('state_id', ''):
            state_id = ResCountyState.search([('code', '=', lead_vals.get('state_id', ''))], limit=1)
            if state_id:
                lead_dict.update({'state_id': state_id.id})
        # Check Country
        if lead_vals.get('country_id', ''):
            country_id = ResCountry.search([('code', '=', lead_vals.get('country_id', ''))], limit=1)
            if country_id:
                lead_dict.update({'country_id': country_id.id})
        # Check Title
        if lead_vals.get('title', ''):
            title = ResPartnerTitle.search([('name', '=', lead_vals.get('title', ''))], limit=1)
            if title:
                lead_dict.update({'title': title.id})
        # Check Source
        if lead_vals.get('source_id', ''):
            source_id = UtmSource.search([('name', '=', lead_vals.get('source_id', ''))], limit=1)
            if source_id:
                lead_dict.update({'source_id': source_id.id})
        lead = CrmLead.create(lead_dict)
        res['"msg"'] = '"Create Lead: %s successfully"' % lead.name
        res['"code"'] = 1
        return res