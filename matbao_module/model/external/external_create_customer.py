# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re
import logging as _logger
import hashlib
from odoo.exceptions import ValidationError

class ExternalCreateCustomer(models.AbstractModel):
    _description = 'Create Customer API'
    _name = 'external.create.customer'

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    @api.multi
    def _validate_email(self, email):
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
        if match == None:
            return False
        return True

    @api.model
    def create_customer(self, code, name, company_type, street, state_code, country_code, email, date_of_birth, date_of_founding, mobile, gender, website, vat,
                        indentify_number, function, phone, fax, sub_email_1, sub_email_2, main_account, promotion_account, representative, source, password_idpage, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        if not code:
            ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
        else:
            ref = code
            if self.env['res.partner'].search([('ref', '=', code)]):
                return {'"msg"': '"Customer already exists."'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        customer_vals = {}
        # Check type of data
        name = self._convert_str(name)
        if not name:
            return {'"msg"': '"Customer name could not be empty"'}
        customer_vals.update({'name': name})
        if not company_type:
            res['"msg"'] = '"Company Type could not be empty and must belong `person`, `company` or `agency`"'
            return res
        customer_vals.update({'company_type': company_type})
        if not email:
            res['"msg"'] = '"Email could not be empty"'
            return res
        if company_id:
            if not ResCompany.browse(company_id):
                res['"msg"'] = '"Company not exists"'
                return res
            customer_vals.update({'company_id': company_id})
        if not self._validate_email(email) or (sub_email_1 and not self._validate_email(sub_email_1)) or (sub_email_2 and not self._validate_email(sub_email_2)):
            return {'"msg"': '"Invalid email."'}
        customer_vals.update({
            'email': email,
            'sub_email_1': sub_email_1 or False,
            'sub_email_2': sub_email_2 or False,
        })
        msg = '""'
        try:
            street_fix = unicode(street, "utf-8")
        except ValidationError:
            street_fix = street
        customer_vals.update({
            'ref': ref,
            'customer': True,
            'street': street_fix,
            'mobile': mobile,
            'website': website,
            'vat': vat,
            'indentify_number': indentify_number,
            'function': function,
            'phone': phone,
            'fax': fax,
            'main_account': main_account,
            'promotion_account': promotion_account,
            'state_code': state_code,
            'country_code': country_code,
            'representative': representative,
            'password_idpage': password_idpage
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
            if date_of_founding:
                date_of_founding_fix = datetime.strptime(str(date_of_founding), DF)
                customer_vals.update({'date_of_founding': date_of_founding_fix})
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
        # Check source
        if source:
            source_id = self.env['res.partner.source'].search(
                [('code', '=', source)], limit=1)
            if not source_id:
                return {'"msg"': ('"Customer source `%s` is not found.  "' % source)}
            customer_vals.update({'source_id': source_id.id})
        try:
            customer = ResPartner.create(customer_vals)
            return {'"customer"': '\"' + customer.name + '\"', '"customer_code"': '\"' + customer.ref + '\"', '"msg"': msg, '"code"': 1}
        except Exception as e:
            _logger.error('"Can`t create customer %s"' % (e.message or repr(e)))
            return {'"msg"': '"Can`t create customer %s"' % (e.message or repr(e))}

    @api.model
    def update_customer(self, code, name, company_type, street, state_code, country_code, email, date_of_birth, date_of_founding, mobile, gender, website, vat,
                        indentify_number, function, phone, fax, sub_email_1, sub_email_2, representative, source, password_idpage, company_id):
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        res = {'"code"': 0, '"msg"': '""'}
        if not code:
            res['"msg"'] = '"Code can not empty"'
            return res
        customer_id = ResPartner.search([('ref', '=', code)])
        if not customer_id:
            return {'"msg"': '"Customer not exists."'}
        if len(customer_id) > 1:
            return {'"msg"': '"Many customer same code."'}
        customer_vals = {}
        # Check type of data
        name = self._convert_str(name)
        if name:
            customer_vals.update({'name': name})
        if company_type and company_type in ('person', 'company', 'agency'):
            customer_vals.update({'company_type': company_type})
        if company_id and ResCompany.browse(company_id):
            customer_vals.update({'company_id': company_id})
        if email and self._validate_email(email):
            customer_vals.update({'email': email})
        if sub_email_1 and self._validate_email(sub_email_1):
            customer_vals.update({'sub_email_1': sub_email_1})
        if sub_email_2 and self._validate_email(sub_email_2):
            customer_vals.update({'sub_email_2': sub_email_2})
        if street:
            customer_vals.update({'street': street.encode("utf-8")})
        if mobile:
            customer_vals.update({'mobile': mobile})
        if website:
            customer_vals.update({'website': website})
        if indentify_number:
            customer_vals.update({'indentify_number': indentify_number})
        if function:
            customer_vals.update({'function': function})
        if phone:
            customer_vals.update({'phone': phone})
        if fax:
            customer_vals.update({'fax': fax})
        if vat:
            customer_vals.update({'vat': vat})
        if representative:
            customer_vals.update({'representative': representative})
        if password_idpage:
            customer_vals.update({'password_idpage': password_idpage})
        if state_code and ResCountyState.search([('code', '=', state_code)], limit=1):
            customer_vals.update({'state_id': ResCountyState.search([('code', '=', state_code)], limit=1).id})
        if country_code and ResCountry.search([('code', '=', country_code)], limit=1):
            customer_vals.update({'country_id': ResCountry.search([('code', '=', country_code)], limit=1).id})
        try:
            if date_of_birth:
                date_of_birth_fix = datetime.strptime(str(date_of_birth), DF)
                customer_vals.update({'date_of_birth': date_of_birth_fix})
            if date_of_founding:
                date_of_founding_fix = datetime.strptime(str(date_of_founding), DF)
                customer_vals.update({'date_of_founding': date_of_founding_fix})
        except ValueError:
            return {
                '"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                '"data"': {}}

        # Check gender value
        if gender and gender in ['male', 'female']:
            customer_vals.update({'gender': gender})

        # Check source
        if source:
            source_id = self.env['res.partner.source'].search([('code', '=', source)], limit=1)
            if source_id:
                customer_vals.update({'source_id': source_id.id})
        try:
            customer_id.write(customer_vals)
        except Exception as e:
            # _logger.error("Error: %s" % (e.message or repr(e)))
            return "Error: %s" % (e.message or repr(e))
        return {'"msg"': '"Update Customer %s successfully"' % customer_id.name, '"code"': 1}

    @api.model
    def update_contact(self, cus_code, type, date_of_birth, gender, street, state_code, country_code, contact_name, indentify_number, function, email, phone, mobile, fax, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
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
        contact_id = customer_id.child_ids.filtered(lambda c: c.type == type)
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
        if not contact_id:
            customer_vals.update({
                'parent_id': customer_id.id,
                'customer': False,
                'supplier': False
            })
            contact_id = ResPartner.create(customer_vals)
        else:
            contact_id.sudo().write(customer_vals)
        return {'"Update successful contact of customer"': '\"' + customer_id.name + '\"', '"msg"': msg, '"code"': 1}

    @api.model
    def create_list_customer(self, lines=[]):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']

        # Check type of data
        if not lines:
            return {'"msg"': '"Lines could not be empty"'}
        if type(lines) is not list:
            return {'"msg"': '"Invalid OrderLineEntity"'}
        for line in lines:
            customer_vals = {'customer': True}
            if not line.get('code'):
                ref = self.env['ir.sequence'].next_by_code('res.partner') or '/'
            else:
                ref = line.get('code')
                if self.env['res.partner'].search([('ref', '=', line.get('code'))]):
                    res['"msg"'] = '"Customer already exists."'
                    break
            name = self._convert_str(line.get('name'))
            if not name:
                res['"msg"'] = '"Customer name could not be empty"'
                break
            customer_vals.update({'name': name, 'ref': ref})
            if not line.get('company_type') or line.get('company_type') not in ('person', 'company', 'agency'):
                res['"msg"'] = '"Company Type could not be empty and must belong `person`, `company` or `agency`"'
                break
            customer_vals.update({'company_type': line.get('company_type')})
            if not line.get('email'):
                res['"msg"'] = '"Email could not be empty"'
                break
            if not self._validate_email(line.get('email')) or (line.get('sub_email_1') and not self._validate_email(line.get('sub_email_1'))) \
                    or (line.get('sub_email_2') and not self._validate_email(line.get('sub_email_2'))):
                res['"msg"'] = '"Invalid email."'
                break
            customer_vals.update({
                'email': line.get('email'),
                'sub_email_1': line.get('sub_email_1') or '',
                'sub_email_2': line.get('sub_email_2') or '',
            })
            msg = '""'
            list_fields = ['street', 'state_code', 'country_code', 'date_of_birth', 'date_of_founding', 'mobile',
                           'gender', 'website', 'vat', 'indentify_number', 'function', 'phone', 'fax',
                           'main_account', 'promotion_account', 'representative', 'source', 'password_idpage', 'company_id']
            for field in list_fields:
                if not line.get(field):
                    continue
                if field in ['email', 'sub_email_1', 'sub_email_2']:
                    if not self._validate_email([line[field]]):
                        res['msg'] = 'Invalid email {} : {} .' . format(field, line[field])
                        break
                customer_vals.update({field: line[field]})

            if line.get('company_id'):
                if not ResCompany.browse(line.get('company_id')):
                    res['"msg"'] = '"Company not exists"'
                    break
                customer_vals.update({'company_id': line.get('company_id')})

            # Get state id
            if line.get('state_code', ''):
                state_id = ResCountyState.search([('code', '=', line.get('state_code', ''))], limit=1)
                if state_id:
                    customer_vals.update({'state_id': state_id.id})
                else:
                    res['"msg"'] = '"State Code {} is not found"'. format(customer_vals['state_code'])
                    break

            try:
                if line.get('date_of_birth'):
                    date_of_birth_fix = datetime.strptime(str(line.get('date_of_birth')), DF)
                    customer_vals.update({'date_of_birth': date_of_birth_fix})
                if line.get('date_of_founding'):
                    date_of_founding_fix = datetime.strptime(str(line.get('date_of_founding')), DF)
                    customer_vals.update({'date_of_founding': date_of_founding_fix})
            except ValueError:
                res = {'"code"': 0, '"msg"': '"Invalid date_of_birth or date_of_founding yyyy-mm-dd"',
                    '"data"': {}}
                break

            # Get Country id
            country_code = self._convert_str(line.get('country_code'))
            if country_code:
                country_id = ResCountry.search(
                    [('code', '=', line.get('country_code'))], limit=1)
                if country_id:
                    customer_vals.update({'country_id': country_id.id})
                else:
                    res = {'"msg"': '"Country Code {} is not found"'.
                            format(line.get('country_code'))}
                    break

            # Check gender value
            if line.get('gender'):
                if line.get('gender') not in ['male', 'female']:
                    res['"msg"'] = '"Gender must be in (`male`, `female`)"'
                    break
                customer_vals.update({'gender': line.get('gender')})

            # Check source
            if line.get('source'):
                source_id = self.env['res.partner.source'].search(
                    [('code', '=', line.get('source'))], limit=1)
                if not source_id:
                    res['"msg"'] = ('"Customer source `%s` is not found.  "' % line.get('source'))
                    break
                customer_vals.update({'source_id': source_id.id})
            customer = ResPartner.create(customer_vals)
            res['"customer"'] = customer.name
        res['"code"'] = 1
        return res

    @api.model
    def get_partner(self, code):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        data = {}

        # Check partner
        if not code:
            res.update({'"msg"': '"Ref could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Partner not found."'})
            return res

        # If arguments are ok
        try:
            # Parse data
            data.update({
                '"id"': partner_id.id,
                '"name"': '\"' + partner_id.name + '\"',
                '"ref"': '\"' + (partner_id.ref or '') + '\"',
                '"company_type"': '\"' + partner_id.company_type + '\"',
                '"street"': '\"' + (partner_id.street or '') + '\"',
                '"state_id"': '\"' + (partner_id.state_id and partner_id.state_id.name or '') + '\"',
                '"country_id"': '\"' + (partner_id.country_id and partner_id.country_id.name or '') + '\"',
                '"website"': '\"' + (partner_id.website or '') + '\"',
                '"date_of_birth"': '\"' + (partner_id.date_of_birth or '') + '\"',
                '"date_of_founding"': '\"' + (partner_id.date_of_founding or '') + '\"',
                '"vat"': '\"' + (partner_id.vat or '') + '\"',
                '"indentify_number"': '\"' + (partner_id.indentify_number or '') + '\"',
                '"accounting_ref"': '\"' + (partner_id.accounting_ref or '') + '\"',
                '"phone"': '\"' + (partner_id.phone or '') + '\"',
                '"mobile"': '\"' + (partner_id.mobile or '') + '\"',
                '"fax"': '\"' + (partner_id.fax or '') + '\"',
                '"email"': '\"' + (partner_id.email or '') + '\"',
                '"sub_email_1"': '\"' + (partner_id.sub_email_1 or '') + '\"',
                '"sub_email_2"': '\"' + (partner_id.sub_email_2 or '') + '\"',
                '"title"': '\"' + (partner_id.title and partner_id.title.name or '') + '\"',
                '"main_account"': '\"' + str(partner_id.with_context(force_company=partner_id.company_id.id).main_account or 0) + '\"',
                '"promotion_account"': '\"' + str(partner_id.with_context(force_company=partner_id.company_id.id).promotion_account_compute or 0) + '\"',
                '"password_idpage"': '\"' + (partner_id.password_idpage or '') + '\"',
                '"company_id"': partner_id.company_id and partner_id.company_id.id or 0,
                '"no_sms"': partner_id.no_sms and '"True"' or '"False"',
                '"no_auto_call"': partner_id.no_auto_call and '"True"' or '"False"',
                '"gender"': '\"' + (partner_id.gender or '') + '\"',
                '"representative"': '\"' + (partner_id.representative or '') + '\"',
            })

            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['msg'] = '"Can not get partner"'
            return res
        return res

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
        if not partner_id.child_ids:
            res.update({'"msg"': '"No contact."'})
            return res
        dict = {}
        for contact in partner_id.child_ids:
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
                if type == 'customer':
                    data.append('\"' + (service.customer_id.indentify_number or '') + '\"')
                else:
                    if not service.customer_id.child_ids or not service.customer_id.child_ids.filtered(lambda contact: contact.type == contact_type):
                        res.update({'"msg"': '"No Contact."'})
                        return res
                    contact = service.customer_id.child_ids.filtered(lambda contact: contact.type == contact_type)
                    data.append('\"' + (contact.indentify_number or '') + '\"')
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_partner_by_mobile(self, mobile):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        # Check partner
        if not mobile:
            res.update({'"msg"': '"Mobile could be not empty"'})
            return res
        partner_ids = ResPartner.search([('mobile', 'like', mobile), ('customer', '=', True)])
        if not partner_ids:
            res.update({'"msg"': '"Partner not found."'})
            return res
        try:
            res.update({
                '"code"': 1,
                '"msg"': '"Successfully"',
                '"partner_name"': '\"' + '###'.join(partner.name for partner in partner_ids) + '\"',
                '"partner"': [{'"id"': partner.id, '"name"': '\"' + partner.name + '\"'} for partner in partner_ids]
            })
        except Exception as e:
            res['msg'] = '"Can`t get partner: %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def generate_password_api(self, customer_code, password):
        if not customer_code or not password:
            return {'"code"': 0, '"msg"': '"Customer Code and Password could be not empty"'}
        if len(password) < 6:
            return {'"code"': 0, '"msg"': '"Password must be more than 6 characters."'}
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code), ('customer', '=', True)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer."' % len(customer_id)}
        try:
            customer_id.write({
                'password_idpage': hashlib.md5(password.encode("utf-8")).hexdigest()
            })
            return {'"code"': 1, '"msg"': '"Completed."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Change pass error: %s"' % (e.message or repr(e))}


