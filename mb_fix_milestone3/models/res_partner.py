# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta
import logging as _logger
from odoo.exceptions import Warning
import hashlib
import urllib2
import json
from lxml import etree
from odoo.osv.orm import setup_modifiers

class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one(track_visibility='onchange')
    no_sms = fields.Boolean("No SMS")
    no_auto_call = fields.Boolean("No Auto Call")
    mobile_status = fields.Boolean("Validated Mobile")
    email_status = fields.Boolean("Validated Email")
    identify_status = fields.Boolean("Validated Identify")

    @api.model
    def get_customer_as_dob_dof(self, day, month):
        if not day:
            return {'"code"': 0, '"msg"': '"Day could be not empty"'}
        if not month:
            return {'"code"': 0, '"msg"': '"Month could be not empty"'}
        cr = self.env.cr
        cr.execute("""SELECT rp.company_type, rp.name, rp.ref, rp.date_of_birth, rp.date_of_founding,
                             rp.vat, rp.phone, rp.mobile, rp.email, rp.no_sms, rp.no_auto_call, rp.company_id
                      FROM res_partner AS rp
                            JOIN mb_sale_contract sc ON sc.partner_id = rp.id AND sc.state = 'return'
                      WHERE rp.company_type = 'person'
                            AND rp.parent_id IS NULL
                            AND rp.ref IS NOT NULL
                            AND EXTRACT(DAY FROM rp.date_of_birth) = %s
                            AND EXTRACT(MONTH FROM rp.date_of_birth) = %s
                            AND EXTRACT(YEAR FROM NOW()) - EXTRACT(YEAR FROM rp.date_of_birth) >= 18
                            AND rp.company_id IN (1, 3)
                            AND rp.state = 'approved'
                      GROUP BY rp.company_type, rp.name, rp.ref, rp.date_of_birth, rp.date_of_founding,
                               rp.vat, rp.phone, rp.mobile, rp.email, rp.no_sms, rp.no_auto_call, rp.company_id
                      UNION ALL
                      SELECT rp.company_type, rp.name, rp.ref, rp.date_of_birth, rp.date_of_founding,
                             rp.vat, rp.phone, rp.mobile, rp.email, rp.no_sms, rp.no_auto_call, rp.company_id
                      FROM res_partner AS rp
                            JOIN mb_sale_contract sc ON sc.partner_id = rp.id AND sc.state = 'return'
                      WHERE rp.company_type = 'company'
                            AND rp.parent_id IS NULL
                            AND rp.ref IS NOT NULL
                            AND EXTRACT(DAY FROM rp.date_of_founding) = %s
                            AND EXTRACT(MONTH FROM rp.date_of_founding) = %s
                            AND rp.company_id IN (1, 3)
                            AND rp.state = 'approved'
                      GROUP BY rp.company_type, rp.name, rp.ref, rp.date_of_birth, rp.date_of_founding,
                               rp.vat, rp.phone, rp.mobile, rp.email, rp.no_sms, rp.no_auto_call, rp.company_id""",
                   (day, month, day, month))

        customers = cr.dictfetchall()
        try:
            data = []
            if customers:
                for customer in customers:
                    data.append({
                        '"customer_type"': '\"' + (customer['company_type'] or '') + '\"',
                        '"name"': '\"' + (customer['name'] or '') + '\"',
                        '"code"': '\"' + (customer['ref'] or '') + '\"',
                        '"date_of_birth"': '\"' + (customer['date_of_birth'] or '') + '\"',
                        '"date_of_founding"': '\"' + (customer['date_of_founding'] or '') + '\"',
                        '"vat"': '\"' + (customer['vat'] or '') + '\"',
                        '"phone"': '\"' + (customer['phone'] or '') + '\"',
                        '"mobile"': '\"' + (customer['mobile'] or '') + '\"',
                        '"email"': '\"' + (customer['email'] or '') + '\"',
                        '"no_sms"': customer['no_sms'] and '"True"' or '"False"',
                        '"no_auto_call"': customer['no_auto_call'] and '"True"' or '"False"',
                        '"company_id"': customer['company_id'] or '""',
                    })
            return {'"code"': 1, '"msg"': '"Get successfully"', '"data"': data}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def generate_password_api(self, customer_code, password):
        if not customer_code or not password:
            return {'"code"': 0, '"msg"': '"Customer Code and Password could be not empty"'}
        if len(password) < 6:
            return {'"code"': 0, '"msg"': '"Password must be more than 6 characters."'}
        customer_id = self.search([('ref', '=', customer_code), ('customer', '=', True)])
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

    @api.model
    def update_no_sms_no_auto_call(self, customer_code, no_sms, no_auto_call):
        if not customer_code or no_sms not in (0, 1) or no_auto_call not in (0, 1):
            return {'"code"': 0, '"msg"': '"Customer code, no_sms, no_auto_call must be empty"'}
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer with %s."' % (len(customer_id), customer_code)}
        try:
            customer_id.write({
                'no_sms': False if no_sms == 0 else True,
                'no_auto_call': False if no_auto_call == 0 else True
            })
            return {'"code"': 1, '"msg"': '"Updated successfully."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Update error: %s"' % (e.message or repr(e))}

    @api.model
    def update_dof(self, customer_code):
        if not customer_code:
            return {'"code"': 0, '"msg"': '"Customer code, VAT must be empty"'}
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer with %s."' % (len(customer_id), customer_code)}
        try:
            url = self.env['ir.values'].get_default('sale.config.settings', 'url')
            if not url:
                raise Warning(_(
                    "Please set the API URL at menu Sale --> Configuration"
                    " --> Settings --> URL"))
            url = url[:-6] + 'ThongTinDoanhNghiep?mst='
            full_url = url + customer_id.vat
            try:
                res_data = urllib2.urlopen(full_url)
                res_data = res_data.read()
                res_data = json.loads(res_data)
            except Exception as e:
                return {'"code"': 0, '"msg"': '"Get data error: %s"' % (e.message or repr(e))}
            if res_data and res_data.get('date_of_founding', False):
                self._cr.execute("""UPDATE res_partner SET date_of_founding = %s WHERE id = %s""", (res_data.get('date_of_founding', False), customer_id.id))
                # customer_id.write({'date_of_founding': res_data.get('date_of_founding', '')})
                return {'"code"': 1, '"msg"': '"Updated successfully."'}
            else:
                return {'"code"': 0, '"msg"': '"No data"'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Update error: %s"' % (e.message or repr(e))}

    @api.model
    def get_customer_ref(self, type='company'):
        if type not in ('person', 'company', 'agency'):
            return {'"code"': 0, '"msg"': '"Type must be in `person`, `company` or `agency`"'}
        partner_ids = self.search_read([('parent_id', '=', False), ('ref', '!=', False), ('vat', '!=', False),
                                        ('customer', '=', True), ('company_type', '=', type)], ['ref'])
        return {'"code"': 1, '"msg"': '"Successfully"', '"data"': partner_ids and ['\"' + partner['ref'] + '\"' for partner in partner_ids] or []}

    @api.model
    def unlink_contact(self, id):
        contact_id = self.browse(id)
        if not contact_id:
            return {'msg': 'No contact'}
        try:
            contact_id.unlink()
            return {'msg': 'Successfully'}
        except Exception as e:
            return {'msg': 'Error: %s' % (e.message or repr(e))}

    @api.model
    def update_mobile_status(self, customer_code, mobile_status, mobile=''):
        if not customer_code or mobile_status not in (0,1):
            return {'"code"': 0, '"msg"': '"Customer Code and Mobile must be in 0 (False) or 1 (True)"'}
        customer_id = self.search([('ref', '=', customer_code), ('customer', '=', True)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer."' % len(customer_id)}
        try:
            args = {'mobile_status': True if mobile_status == 1 else False}
            if mobile:
                args.update({
                    'mobile': mobile
                })
            customer_id.write(args)
            return {'"code"': 1, '"msg"': '"Completed."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Updated error: %s"' % (e.message or repr(e))}

    @api.model
    def update_email_status(self, customer_code, email_status, email=''):
        if not customer_code or email_status not in (0,1):
            return {'"code"': 0, '"msg"': '"Customer Code and Email Status must be in 0 (False) or 1 (True)"'}
        customer_id = self.search([('ref', '=', customer_code), ('customer', '=', True)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer."' % len(customer_id)}
        try:
            args = {'email_status': True if email_status == 1 else False}
            if email:
                args.update({'email': email})
            customer_id.write(args)
            return {'"code"': 1, '"msg"': '"Completed."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Updated error: %s"' % (e.message or repr(e))}

    @api.model
    def update_identify_status(self, customer_code, identify_status, identify=''):
        if not customer_code or identify_status not in (0,1):
            return {'"code"': 0, '"msg"': '"Customer Code and Mobile must be in 0 (False) or 1 (True)"'}
        customer_id = self.search([('ref', '=', customer_code), ('customer', '=', True)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found."'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer."' % len(customer_id)}
        try:
            args = {'identify_status': True if identify_status == 1 else False}
            if identify:
                args.update({'indentify_number': identify})
            customer_id.write(args)
            return {'"code"': 1, '"msg"': '"Completed."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Updated error: %s"' % (e.message or repr(e))}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            no_sms = doc.xpath("//field[@name='no_sms']")
            no_auto_call = doc.xpath("//field[@name='no_auto_call']")
            fields_to_options = doc.xpath("//field")
            for node in fields_to_options:
                if no_sms and no_auto_call and node in (no_sms[0], no_auto_call[0]):
                    if self.user_has_groups('base.group_system') or \
                        self.user_has_groups('mb_sale_contract.group_operator_mb_sale_contract'):
                        node.set('readonly', "0")
                        setup_modifiers(node)
                    else:
                        node.set('readonly', "1")
                        setup_modifiers(node)
        res['arch'] = etree.tostring(doc)
        return res

