# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re
import logging as _logger
import hashlib

class ExternalCreateCustomer(models.AbstractModel):
    _name = 'external.create.customer'
    _inherit = 'external.create.customer'

    @api.model
    def get_contact(self, code, type=False):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        data = []
        # Check partner
        if not code:
            res.update({'"msg"': '"Ref could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Partner not found."'})
            return res
        if type and type not in ('payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res.update({'"msg"': '"Type must be in (`payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager`, `contact`)"'})
            return res
        if not partner_id.contact_ids and not partner_id.child_ids:
            res.update({'"msg"': '"No contact."'})
            return res
        contact_ids = partner_id.contact_ids or partner_id.child_ids
        dict = {}
        for contact in contact_ids:
            contact_dict = {}
            if type:
                if contact.type == type:
                    contact_dict.update({
                        '"ref"': '\"' + (contact.ref or '') + '\"',
                        '"name"': '\"' + (contact.name or '') + '\"',
                        '"email"': '\"' + (contact.email or '') + '\"',
                        '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                        '"company_type"': '\"' + (contact.company_type or '') + '\"',
                        '"street"': '\"' + (contact.street or '') + '\"',
                        '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                        '"zip"': '\"' + (contact.zip or '') + '\"',
                        '"mobile"': '\"' + (contact.mobile or '') + '\"',
                        '"phone"': '\"' + (contact.phone or '') + '\"',
                        '"fax"': '\"' + (contact.fax or '') + '\"',
                        '"function"': '\"' + (contact.function or '') + '\"',
                        '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                        '"gender"': '\"' + (contact.gender or '') + '\"',
                        '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                        '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                        '"id"': '\"' + str(partner_id.id) + '\"'
                    })
                    dict.update({
                        '\"' + contact.type + '\"': [contact_dict]
                    })
                    break
            else:
                contact_dict.update({
                    '"ref"': '\"' + (contact.ref or '') + '\"',
                    '"name"': '\"' + (contact.name or '') + '\"',
                    '"email"': '\"' + (contact.email or '') + '\"',
                    '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                    '"company_type"': '\"' + (contact.company_type or '') + '\"',
                    '"street"': '\"' + (contact.street or '') + '\"',
                    '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                    '"zip"': '\"' + (contact.zip or '') + '\"',
                    '"mobile"': '\"' + (contact.mobile or '') + '\"',
                    '"phone"': '\"' + (contact.phone or '') + '\"',
                    '"fax"': '\"' + (contact.fax or '') + '\"',
                    '"function"': '\"' + (contact.function or '') + '\"',
                    '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                    '"gender"': '\"' + (contact.gender or '') + '\"',
                    '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                    '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                    '"id"': '\"' + str(partner_id.id) + '\"'
                })
                dict.update({
                    '\"' + contact.type + '\"': [contact_dict]
                })
        # Add Customer
        # dict = {}
        cus_arr = {}
        cus_arr.update({
            '"ref"': '\"' + (partner_id.ref or '') + '\"',
            '"name"': '\"' + (partner_id.name or '') + '\"',
            '"email"': '\"' + (partner_id.email or '') + '\"',
            '"indentify_number"': '\"' + (partner_id.indentify_number or '') + '\"',
            '"company_type"': '\"' + (partner_id.company_type or '') + '\"',
            '"street"': '\"' + (partner_id.street or '') + '\"',
            '"state_id"': '\"' + (partner_id.state_id and str(partner_id.state_id.id) or '') + '\"',
            '"zip"': '\"' + (partner_id.zip or '') + '\"',
            '"mobile"': '\"' + (partner_id.mobile or '') + '\"',
            '"phone"': '\"' + (partner_id.phone or '') + '\"',
            '"fax"': '\"' + (partner_id.fax or '') + '\"',
            '"function"': '\"' + (partner_id.function or '') + '\"',
            '"date_of_birth"': '\"' + (partner_id.date_of_birth or '') + '\"',
            '"date_of_founding"': '\"' + (partner_id.date_of_founding or '') + '\"',
            '"representative"': '\"' + (partner_id.representative or '') + '\"',
            '"gender"': '\"' + (partner_id.gender or '') + '\"',
            '"city"': '\"' + (partner_id.state_id and partner_id.state_id.code or '') + '\"',
            '"country"': '\"' + (partner_id.country_id and partner_id.country_id.code or '') + '\"',
            '"id"': '\"' + str(partner_id.id) + '\"'
        })
        dict.update({
            '\"' + 'customer' + '\"': [cus_arr]
        })
        data.append(dict)
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_identification(self, domain, contact_type):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleService = self.env['sale.service']
        data = []
        # Check data
        if not domain:
            res.update({'"msg"': '"Domain name could be not empty"'})
            return res
        service_ids = SaleService.search([('product_id.name', '=ilike', domain), ('status', '=', 'active')])
        if not service_ids:
            res.update({'"msg"': '"Service not found."'})
            return res
        service_ids = service_ids.filtered(lambda service: service.product_category_id and service.product_category_id.code and '.vn' in service.product_category_id.code)
        if contact_type and contact_type not in ('customer', 'payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res.update({'"msg"': '"Type must be in (`customer`, `payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager`, `contact`)"'})
            return res
        for service in service_ids:
            if service.customer_id:
                contact_ids = service.customer_id.contact_ids or service.customer_id.child_ids
                if type == 'customer':
                    data.append('\"' + (service.customer_id.indentify_number or '') + '\"')
                else:
                    if not contact_ids or not contact_ids.filtered(lambda contact: contact.type == contact_type):
                        res.update({'"msg"': '"No Contact."'})
                        return res
                    contact = service.customer_id.contact_ids.filtered(lambda contact: contact.type == contact_type)
                    data.append('\"' + (contact.indentify_number or '') + '\"')
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def update_contact(self, cus_code, type, date_of_birth, gender, street, state_code, country_code, contact_name, indentify_number, function, email, phone, mobile, fax, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        CustomerContact = self.env['customer.contact']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        customer_vals = {}
        # Check type of data
        if not cus_code:
            return {'"msg"': '"Customer Code could not be empty"'}
        customer_id = ResPartner.search([('ref', '=', cus_code)])
        if not customer_id:
            return {'"msg"': '"Customer not exists"'}
        if not type or type not in ('payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res['"msg"'] = '"Customer Type could not be empty and must belong `payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager` or `contact`"'
            return res
        contact_id = customer_id.contact_ids.filtered(lambda c: c.type == type)
        if not contact_name:
            res['"msg"'] = '"Contact name could not be empty"'
            return res
        customer_vals.update({
            'company_type': 'person',
            'name': contact_name
        })
        if company_id:
            if not ResCompany.browse(company_id):
                res['"msg"'] = '"Company not exists"'
                return res
            customer_vals.update({'company_id': company_id})
        # if not email:
        #     res['"msg"'] = '"Email could not be empty"'
        #     return res
        if email and not self._validate_email(email):
            return {'"msg"': '"Invalid email."'}
        customer_vals.update({'email': email})
        msg = '""'
        customer_vals.update({
            'street': street,
            'mobile': mobile,
            'indentify_number': indentify_number,
            'function': function,
            'phone': phone,
            'fax': fax,
            'state_code': state_code,
            'country_code': country_code,
        })
        # Get state id
        if state_code:
            state_id = ResCountyState.search([('code', '=', state_code)], limit=1)
            if state_id:
                customer_vals.update({'state_id': state_id.id})
            else:
                return {'"msg"': '"State Code {} is not found"'.
                        format(customer_vals['state_code'])}

        try:
            if date_of_birth:
                date_of_birth_fix = datetime.strptime(str(date_of_birth), DF)
                customer_vals.update({'date_of_birth': date_of_birth_fix})
        except ValueError:
            return {
                '"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                '"data"': {}}

        # Get Country id
        country_code = self._convert_str(country_code)
        if country_code:
            country_id = ResCountry.search(
                [('code', '=', country_code)], limit=1)
            if country_id:
                customer_vals.update({'country_id': country_id.id})
            else:
                return {'"msg"': '"Country Code {} is not found"'.
                        format(country_code)}

        # Check gender value
        if gender:
            if gender not in ['male', 'female']:
                return {
                    '"msg"': '"Gender must be in (`male`, `female`)"'
                }
            customer_vals.update({'gender': gender})
        # print customer_vals
        if not contact_id:
            customer_vals.update({
                'parent_id': customer_id.id,
                'customer': False,
                'supplier': False
            })
            CustomerContact.create(customer_vals)
        else:
            contact_id.sudo().write(customer_vals)
        return {'"Update successful contact of customer"': '\"' + customer_id.name + '\"', '"msg"': msg, '"code"': 1}