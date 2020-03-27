# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
# -------------------------------Snow say by CC code ngu ma by by--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re
from datetime import datetime

class ExternalResellerCustomer(models.AbstractModel):
    _description = 'Reseller Customer API'
    _name = 'external.reseller.customer'

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    @api.multi
    def _validate_email(self, email):
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,6})$', email)
        if match == None:
            return False
        return True

    @api.model
    def create_reseller_customer(self, reseller_vals={}, contact_vals=[]):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResPartner = self.env['res.partner']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        ResellerCustomer = self.env['reseller.customer']
        # Check type parameter
        if not reseller_vals or type(reseller_vals) is not dict:
            return {'"msg"': '"Reseller Vals could not be empty and must be dict"'}
        if type(contact_vals) is not list:
            res['"msg"'] = '"Contact vals must be list"'
            return res
        # Check data Reseller Vals
        # If it have code, just update, else create
        if reseller_vals.get('code', ''):
            if ResellerCustomer.search([('code', '=', reseller_vals.get('code', ''))], limit=1):
                flag = True
            else:
                flag = False
        else:
            flag = False
        if not flag:
            res_vals = {'type': 'contact'}
            # Check name
            if reseller_vals.get('code', ''):
                code = reseller_vals.get('code', '')
            else:
                code = self.env['ir.sequence'].next_by_code('reseller.customer') or ''
            if not reseller_vals.get('name', ''):
                return {'"msg"': '"Reseller Name could not be empty"'}
            res_vals.update({
                'name': reseller_vals.get('name'),
                'code': code
            })
            # Check customer type
            if not reseller_vals.get('company_type') or reseller_vals.get('company_type') not in ('person', 'company'):
                return {'"msg"': '"Customer Type could not be empty and must belong `person` or `company`"'}
            res_vals.update({
                'company_type': reseller_vals.get('company_type')
            })
            # Check Agency
            if not reseller_vals.get('agency_id'):
                return {'"msg"': '"Agency could not be empty"'}
            agency = ResPartner.search([('ref', '=', reseller_vals.get('agency_id')), ('company_type', '=', 'agency')])
            if not agency:
                return {'"msg"': '"Agency not exists"'}
            res_vals.update({
                'agency_id': agency.id
            })
            # Check email
            if not reseller_vals.get('email'):
                return {'"msg"': '"Email could not be empty"'}
            if not self._validate_email(reseller_vals.get('email')):
                return {'"msg"': '"Invalid email."'}
            res_vals.update({
                'email': reseller_vals.get('email')
            })
            list_fields = ['street', 'city', 'mobile', 'gender', 'vat', 'indentify_number', 'function', 'phone', 'fax',
                           'representative', 'company_id', 'password_idpage']
            for field in list_fields:
                if not reseller_vals.get(field):
                    continue
                res_vals.update({field: reseller_vals.get(field)})
            if reseller_vals.get('gender') and reseller_vals.get('gender') not in ('male', 'female', 'others'):
                return {'"msg"': '"Gender must belong `male`, `female` or `others`."'}
            if reseller_vals.get('company_id') and not ResCompany.browse(reseller_vals.get('company_id')):
                return {'"msg"': '"Company not exists"'}
            # Check State
            if reseller_vals.get('state_code', ''):
                state_id = ResCountyState.search([('code', '=', reseller_vals.get('state_code', ''))], limit=1)
                if state_id:
                    res_vals.update({'state_id': state_id.id})
                else:
                    return {'"msg"': '"State Code %s is not found"' % reseller_vals.get('state_code', '')}
            # Check Country
            if reseller_vals.get('country_code', ''):
                country_id = ResCountry.search([('code', '=', reseller_vals.get('country_code', ''))], limit=1)
                if country_id:
                    res_vals.update({'country_code': country_id.id})
                else:
                    return {'"msg"': '"Country Code %s is not found"' % reseller_vals.get('country_code', '')}
            # Chech Date of Birth
            try:
                if reseller_vals.get('date_of_birth'):
                    date_of_birth_fix = datetime.strptime(str(reseller_vals.get('date_of_birth')), DF)
                    res_vals.update({'date_of_birth': date_of_birth_fix})
            except ValueError:
                return {'"msg"': '"Invalid date_of_birth yyyy-mm-dd"'}
            if contact_vals:
                child_ids = []
                for contact in contact_vals:
                    ct_dict = {'company_type': 'person'}
                    # Check name
                    if not contact.get('name', ''):
                        return {'"msg"': '"Contact Name is not found"'}
                    ct_dict.update({'name': contact.get('name', '')})
                    # Check Type
                    if not contact.get('type') or contact.get('type') not in ('contact', 'payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager'):
                        return {'"msg"': '"Contact type could not be empty and must belong `contact`, `payment_manager`, `technical_manager`, `domain_manager` or `helpdesk_manager`."'}
                    ct_dict.update({'type': contact.get('type')})
                    # Check email
                    if contact.get('email'):
                        if not self._validate_email(contact.get('email')):
                            return {'"msg"': '"Contact Invalid email."'}
                        else:
                            ct_dict.update({'email': contact.get('email')})
                    list_fields = ['street', 'city', 'country_code', 'mobile',
                                   'vat', 'indentify_number', 'function', 'phone', 'fax', 'company_id']
                    for field in list_fields:
                        if not contact.get(field):
                            continue
                        ct_dict.update({field: contact.get(field)})
                    if contact.get('gender'):
                        if contact.get('gender') not in ('male', 'female', 'others'):
                            return {'"msg"': '"Contact Gender must belong `male`, `female` or `others`."'}
                        else:
                            ct_dict.update({'gender': contact.get('gender')})
                    if contact.get('company_id') and not ResCompany.browse(contact.get('company_id')):
                        res['"msg"'] = '"Contact Company not exists"'
                    # Check State
                    if contact.get('state_code', ''):
                        state_id = ResCountyState.search([('code', '=', contact.get('state_code', ''))], limit=1)
                        if state_id:
                            ct_dict.update({'state_id': state_id.id})
                        else:
                            return {'"msg"': '"Contact State Code %s is not found"' % contact.get('state_code', '')}
                    # Check Country
                    if contact.get('country_code', ''):
                        country_id = ResCountry.search([('code', '=', contact.get('country_code', ''))],
                                                       limit=1)
                        if country_id:
                            ct_dict.update({'country_code': country_id.id})
                        else:
                            return {'"msg"': '"Contact Country Code %s is not found"' % contact.get('country_code', '')}
                    # Chech Date of Birth
                    try:
                        if contact.get('date_of_birth'):
                            date_of_birth_fix = datetime.strptime(str(contact.get('date_of_birth')), DF)
                            ct_dict.update({'date_of_birth': date_of_birth_fix})
                    except ValueError:
                        return {'"msg"': '"Contact Invalid date_of_birth yyyy-mm-dd"'}
                    child_ids.append((0, 0, ct_dict))
                res_vals.update({'child_ids': child_ids})
            try:
                rc = ResellerCustomer.create(res_vals)
                res['"msg"'] = '"Create Reseller Customer %s successfully"' % rc.name
                res['"data"'] = '"%s"' % rc.code
            except Exception as e:
                res['"msg"'] = '"Create Reseller Customer error: %s"' % (e.message or repr(e))
        else:
            reseller_id = ResellerCustomer.search([('code', '=', reseller_vals.get('code', ''))], limit=1)
            if not reseller_id:
                return {'"msg"': '"Reseller Customer %s not exists"' % reseller_vals.get('code', '')}
            res_vals = {}
            # Check name
            if reseller_vals.get('name', ''):
                res_vals.update({
                    'name': reseller_vals.get('name')
                })
            # Check customer type
            if reseller_vals.get('company_type') and reseller_vals.get('company_type') in ('person', 'company'):
                res_vals.update({
                    'company_type': reseller_vals.get('company_type')
                })
            # Check Agency
            if reseller_vals.get('agency_id'):
                agency = ResPartner.search([('ref', '=', reseller_vals.get('agency_id')), ('company_type', '=', 'agency')])
                if agency:
                    res_vals.update({
                        'agency_id': agency.id
                    })
            # Check email
            if reseller_vals.get('email') and self._validate_email(reseller_vals.get('email')):
                res_vals.update({
                    'email': reseller_vals.get('email')
                })
            list_fields = ['street', 'city', 'mobile', 'gender', 'vat', 'indentify_number', 'function', 'phone', 'fax',
                           'representative', 'company_id', 'password_idpage']
            for field in list_fields:
                if not reseller_vals.get(field):
                    continue
                res_vals.update({field: reseller_vals.get(field)})
            if reseller_vals.get('gender') and reseller_vals.get('gender') not in ('male', 'female', 'others'):
                return {'"msg"': '"Gender must belong `male`, `female` or `others`."'}
            if reseller_vals.get('company_id') and not ResCompany.browse(reseller_vals.get('company_id')):
                return {'"msg"': '"Company not exists"'}
            # Check State
            if reseller_vals.get('state_code', ''):
                state_id = ResCountyState.search([('code', '=', reseller_vals.get('state_code', ''))], limit=1)
                if state_id:
                    res_vals.update({'state_id': state_id.id})
                else:
                    return {'"msg"': '"State Code %s is not found"' % reseller_vals.get('state_code', '')}
            # Check Country
            if reseller_vals.get('country_code', ''):
                country_id = ResCountry.search([('code', '=', reseller_vals.get('country_code', ''))], limit=1)
                if country_id:
                    res_vals.update({'country_code': country_id.id})
                else:
                    return {'"msg"': '"Country Code %s is not found"' % reseller_vals.get('country_code', '')}
            # Chech Date of Birth
            try:
                if reseller_vals.get('date_of_birth'):
                    date_of_birth_fix = datetime.strptime(str(reseller_vals.get('date_of_birth')), DF)
                    res_vals.update({'date_of_birth': date_of_birth_fix})
            except ValueError:
                return {'"msg"': '"Invalid date_of_birth yyyy-mm-dd"'}
            reseller_id.write(res_vals)
            res['"msg"'] = '"Update Reseller Customer %s successfully"' % reseller_id.name
            res['"data"'] = '"%s"' % reseller_id.code
        res['"code"'] = 1
        return res

    @api.model
    def update_contact(self, reseller_code, type, date_of_birth, gender, street, state_code, country_code, contact_name,
                       indentify_number, function, email, phone, mobile, fax, company_id):
        res = {'"code"': 0, '"msg"': '""'}
        ResCountyState = self.env['res.country.state']
        ResellerCustomer = self.env['reseller.customer']
        ResCountry = self.env['res.country']
        ResCompany = self.env['res.company']
        customer_vals = {}
        # Check type of data
        if not reseller_code:
            return {'"msg"': '"Reseller Code could not be empty"'}
        reseller_id = ResellerCustomer.search([('code', '=', reseller_code)])
        if not reseller_id:
            return {'"msg"': '"Reseller not exists"'}
        if not type or type not in ('payment_manager', 'technical_manager', 'domain_manager', 'helpdesk_manager', 'contact'):
            res['"msg"'] = '"Customer Type could not be empty and must belong `payment_manager`, `technical_manager`, `domain_manager`, `helpdesk_manager` or `contact`"'
            return res
        contact_id = reseller_id.child_ids.filtered(lambda c: c.type == type)
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
                'parent_id': reseller_id.id,
            })
            ResellerCustomer.create(customer_vals)
            return {'"Create successful contact of customer"': '\"' + reseller_id.name + '\"', '"msg"': msg,
                    '"code"': 1}
        else:
            contact_id.write(customer_vals)
            return {'"Update successful contact of customer"': '\"' + reseller_id.name + '\"', '"msg"': msg, '"code"': 1}

    @api.model
    def get_contact(self, code, type=False):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        # ResPartner = self.env['res.partner']
        ResellerCustomer = self.env['reseller.customer']
        SaleService = self.env['sale.service']
        data = []
        # Check partner
        if not code:
            res.update({'"msg"': '"Code could be not empty"'})
            return res
        partner_id = ResellerCustomer.search([('code', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Reseller not found."'})
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
                        '"code"': '\"' + (contact.code or '') + '\"',
                        '"name"': '\"' + (contact.name or '') + '\"',
                        '"email"': '\"' + (contact.email or '') + '\"',
                        '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                        '"company_type"': '\"' + (contact.company_type or '') + '\"',
                        '"street"': '\"' + (contact.street or '') + '\"',
                        '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                        '"state_code"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                        '"state_name"': '\"' + (contact.state_id and contact.state_id.name or '') + '\"',
                        '"mobile"': '\"' + (contact.mobile or '') + '\"',
                        '"phone"': '\"' + (contact.phone or '') + '\"',
                        '"fax"': '\"' + (contact.fax or '') + '\"',
                        '"function"': '\"' + (contact.function or '') + '\"',
                        '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                        '"gender"': '\"' + (contact.gender or '') + '\"',
                        '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                        '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                        '"country_name"': '\"' + (contact.country_id and contact.country_id.name or '') + '\"',
                        '"id"': '\"' + str(partner_id.id) + '\"'
                    })
                    dict.update({
                        '\"' + contact.type + '\"': [contact_dict]
                    })
                    break
            else:
                contact_dict.update({
                    '"code"': '\"' + (contact.code or '') + '\"',
                    '"name"': '\"' + (contact.name or '') + '\"',
                    '"email"': '\"' + (contact.email or '') + '\"',
                    '"indentify_number"': '\"' + (contact.indentify_number or '') + '\"',
                    '"company_type"': '\"' + (contact.company_type or '') + '\"',
                    '"street"': '\"' + (contact.street or '') + '\"',
                    '"state_id"': '\"' + (contact.state_id and str(contact.state_id.id) or '') + '\"',
                    '"state_name"': '\"' + (contact.state_id and contact.state_id.name or '') + '\"',
                    '"mobile"': '\"' + (contact.mobile or '') + '\"',
                    '"phone"': '\"' + (contact.phone or '') + '\"',
                    '"fax"': '\"' + (contact.fax or '') + '\"',
                    '"function"': '\"' + (contact.function or '') + '\"',
                    '"date_of_birth"': '\"' + (contact.date_of_birth or '') + '\"',
                    '"gender"': '\"' + (contact.gender or '') + '\"',
                    '"city"': '\"' + (contact.state_id and contact.state_id.code or '') + '\"',
                    '"country"': '\"' + (contact.country_id and contact.country_id.code or '') + '\"',
                    '"country_name"': '\"' + (contact.country_id and contact.country_id.name or '') + '\"',
                    '"id"': '\"' + str(partner_id.id) + '\"'
                })
                dict.update({
                    '\"' + contact.type + '\"': [contact_dict]
                })
        # Add Customer
        # dict = {}
        cus_arr = {}
        # service_count = SaleService.search_count([('customer_id', '=', partner_id.id)])
        cus_arr.update({
            '"code"': '\"' + (partner_id.code or '') + '\"',
            '"name"': '\"' + (partner_id.name or '') + '\"',
            '"agency_id"': '\"' + (partner_id.agency_id and str(partner_id.agency_id.id) or '') + '\"',
            '"agency_code"': '\"' + (partner_id.agency_id and partner_id.agency_id.ref or '') + '\"',
            '"email"': '\"' + (partner_id.email or '') + '\"',
            '"indentify_number"': '\"' + (partner_id.indentify_number or '') + '\"',
            '"company_type"': '\"' + (partner_id.company_type or '') + '\"',
            '"street"': '\"' + (partner_id.street or '') + '\"',
            '"state_id"': '\"' + (partner_id.state_id and str(partner_id.state_id.id) or '') + '\"',
            '"state_name"': '\"' + (partner_id.state_id and partner_id.state_id.name or '') + '\"',
            '"mobile"': '\"' + (partner_id.mobile or '') + '\"',
            '"phone"': '\"' + (partner_id.phone or '') + '\"',
            '"fax"': '\"' + (partner_id.fax or '') + '\"',
            '"function"': '\"' + (partner_id.function or '') + '\"',
            '"date_of_birth"': '\"' + (partner_id.date_of_birth or '') + '\"',
            '"representative"': '\"' + (partner_id.representative or '') + '\"',
            '"gender"': '\"' + (partner_id.gender or '') + '\"',
            '"city"': '\"' + (partner_id.state_id and partner_id.state_id.code or '') + '\"',
            '"country"': '\"' + (partner_id.country_id and partner_id.country_id.code or '') + '\"',
            '"country_name"': '\"' + (partner_id.country_id and partner_id.country_id.name or '') + '\"',
            '"password_idpage"': '\"' + (partner_id.password_idpage or '') + '\"',
            '"vat"': '\"' + (partner_id.vat or '') + '\"',
            '"service_count"': SaleService.search_count([('reseller_id', '=', partner_id.id)]) or 0,
            '"id"': '\"' + str(partner_id.id) + '\"'
        })
        dict.update({
            '\"' + 'reseller' + '\"': [cus_arr]
        })
        data.append(dict)
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def reset_password(self, code, password):
        res = {'"code"': 0, '"msg"': '""'}
        if not code:
            res['"msg"'] = '"Reseller Code could not be empty"'
            return res
        reseller_id = self.env['reseller.customer'].search([('code', '=', code)])
        if not reseller_id:
            res['"msg"'] = '"Reseller not exists"'
            return res
        if not password:
            res['"msg"'] = '"Password could not be empty"'
            return res
        try:
            reseller_id.write({
                'password_idpage': password
            })
            res['"msg"'] = '"Update Password successfully"'
        except:
            res['"msg"'] = '"Can`t reset password"'
            return res
        res['"code"'] = 1
        return res

    @api.model
    def update_service(self, service_code, reseller_code):
        res = {'"code"': 0, '"msg"': '""'}
        if not service_code:
            res['"msg"'] = '"Service Code could not be empty"'
            return res
        service_id = self.env['sale.service'].search([('reference', '=', service_code)], limit=1)
        if not service_id:
            res['"msg"'] = '"Service not exists"'
            return res
        if not reseller_code:
            res['"msg"'] = '"Reseller Code could not be empty"'
            return res
        reseller_id = self.env['reseller.customer'].search([('code', '=', reseller_code)], limit=1)
        if not reseller_id:
            res['"msg"'] = '"Reseller not exists"'
            return res
        try:
            service_id.write({
                'reseller_id': reseller_id.id
            })
            res['"msg"'] = '"Update Reseller successfully"'
        except:
            res['"msg"'] = '"Can`t update reseller"'
            return res
        res['"code"'] = 1
        return res

