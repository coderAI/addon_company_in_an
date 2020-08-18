# -*- coding: utf-8 -*-
from odoo import api, fields, models
import json
from datetime import datetime, timedelta

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
                                     'indentify_number', 'accounting_ref', 'phone','state',
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



class ExternalActiveService(models.AbstractModel):
    _description = 'Create Product and Service API'
    _inherit = 'external.create.service'

    @api.model
    def get_service_info_new(self, partner_id, reference):

        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data={}
        messages='Successfully'
        code=200

        # Check partner
        if not partner_id and type(partner_id) is not int:
            messages = "Customer ID could be not empty and must be number"

        partner = ResPartner.browse(partner_id)
        if not partner:
            messages = "Customer not found."

        service = SaleService.search([('customer_id', '=', partner_id), ('reference', '=', reference), ('end_date', '>=', datetime.now().date() - timedelta(days=60))], limit=1)
        if not service:
            messages = "Service not found."


        order_line_id = self.env['sale.order.line'].search([('product_id', '=', service.product_id.id),
                                                            ('service_status', '=', 'done')], order='id desc', limit =1)
        data.update({
            "id": service.id,
            "name": service.name,
            "reference": service.reference or '',
            "product_id": service.product_id and service.product_id.default_code or '',
            "product_category_id": service.product_category_id.id,
            "product_category_code": service.product_category_id.code or '',
            "parent_product_category_code": service.product_category_id and service.product_category_id.parent_id and service.product_category_id.parent_id.code or '',
            "ip_hosting": service.ip_hosting or '',
            "ip_email": service.ip_email or '',
            "start_date": service.start_date  or '0001-01-01',
            "end_date": service.end_date  or '0001-01-01',
            "write_date": service.write_date  or '0001-01-01',
            "status": service.status or '',
            "parent_product_id": service.parent_product_id and service.parent_product_id.default_code or '',
            "reseller_code": service.reseller_id and service.reseller_id.code or '',
            "billing_cycle": service.product_category_id and service.product_category_id.billing_cycle or 0,
            "sold": service.product_category_id and service.product_category_id.sold  or False,
            "is_stop_manual": service.is_stop_manual  or False,
            "date_stop": service.date_stop or '0001-01-01',
            "can_be_renew": service.product_category_id and service.product_category_id.can_be_renew  or False,
            "uom": service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or service.uom_id and service.uom_id.name or '',
            "id_domain_floor": service.id_domain_floor or '',
            "time": order_line_id and order_line_id.time or 0,
            "is_stop": service.is_stop  or False,
            "temp_stop_date": service.temp_stop_date or '0001-01-01',
            "temp_un_stop_date": service.temp_un_stop_date or '0001-01-01',
            "is_active": service and service.is_active  or False,
            "is_auto_renew": service and service.is_auto_renew  or False,
            "order_ssl_id": service.order_ssl_id or 0,
            "price": service.price or 0,
            "license": service.license or '',
            "vps_code": service.vps_code or '',
            "os_template": service.os_template or '',
            "open": service.open or False,
            "temp_open_date": service.temp_open_date or '0001-01-01',
            "is_addons": service.product_category_id and service.product_category_id.is_addons  or False})
        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)



    @api.model
    def get_service_new(self, cus_code, type=False, limit=False, reseller_code='', categ=[], offset=0):
       
        messages='Successfully'
        code=200
        ResPartner = self.env['res.partner']
        ResellerCustomer = self.env['reseller.customer']
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = []
        domain = [('end_date', '>=', datetime.now().date() - timedelta(days=60))]
        # Check partner
        if not cus_code:
            messages="Customer code could be not empty"

        partner_id = ResPartner.search([('ref', '=', cus_code)])
        if not partner_id:
            messages="Customer not found."
           
        domain.append(('customer_id', '=', partner_id.id))
        # Check Reseller
        if reseller_code:
            reseller_id = ResellerCustomer.search([('code', '=', reseller_code)])
            if not reseller_id:
                messages="Reseller not found."
               
            domain.append(('reseller_id', '=', reseller_id.id))
        if type and type not in ('DM', 'HO'):
            messages="Type must be in DM, HO"
     
        if categ:
            categ_ids = ProductCategory.search([('code', 'in', list(categ))])
            categ_ids = categ_ids and ProductCategory.search([('id', 'child_of', categ_ids.ids)]) or False
            if categ_ids:
                domain.append(('product_category_id', 'in', categ_ids.ids))
        services = SaleService.search(domain, limit=limit, offset=offset)

        for service in services:
            service_type = ''
            if service.product_id and service.product_id.categ_id:
                parent_categ = self.get_parent_product_category(service.product_category_id)
                if service.product_id.categ_id.code[:1] == '.':
                    if '.vn' in service.product_id.categ_id.code:
                        service_type = 'DMVN'
                    else:
                        service_type = 'DMQT'
                else:
                    if parent_categ.code == 'CHILI':
                        service_type = 'CHILI'
                    elif parent_categ.code == 'HO':
                        service_type = 'HO'
                    elif parent_categ.code == 'EMAIL':
                        service_type = 'EMAIL'
                    elif parent_categ.code == 'CLOUDSERVER':
                        service_type = 'CLOUDSERVER'
            item = {}
            if type:
                if type == 'DM' and service.product_category_id.code and service.product_category_id.code[:1] == '.':
                    item.update({
                        "id": service.id,
                        "name":service.name or '',
                        "reference":service.reference or '',
                        "product_id":service.product_id and service.product_id.default_code or '',
                        "product_category_id": service.product_category_id and service.product_category_id.id or "",
                        "product_category_code":service.product_category_id.code or '',
                        "product_category_name":service.product_category_id.name or '',
                        "parent_product_category_code":service.product_category_id and service.product_category_id.parent_id and
                                                                  service.product_category_id.parent_id.code or '',
                        "parent_product_code":service.parent_product_id and service.parent_product_id.code or '',
                        "ip_hosting":service.ip_hosting or '',
                        "ip_email":service.ip_email or '',
                        "start_date":service.start_date  or '0001-01-01',
                        "end_date":service.end_date  or '0001-01-01',
                        "write_date":service.write_date  or '0001-01-01',
                        "is_stop_manual": service.is_stop_manual or False,
                        "date_stop":service.date_stop  or '0001-01-01',
                        "is_stop":service.is_stop or False,
                        "temp_stop_date":service.temp_stop_date  or '0001-01-01',
                        "temp_un_stop_date":service.temp_un_stop_date  or '0001-01-01',
                        "status":service.status or '',
                        "reseller_id": service.reseller_id and service.reseller_id.id or "",
                        "reseller_code":service.reseller_id and service.reseller_id.code or '',
                        "reseller_type":service.reseller_id and service.reseller_id.company_type or '',
                        "service_type": service_type,
                        "parent_product_id":service.parent_product_id and service.parent_product_id.default_code or '',
                        "billing_cycle": service.product_category_id and service.product_category_id.billing_cycle or 0,
                        "sold": service.product_category_id and service.product_category_id.sold or False,
                        "can_be_renew": service.product_category_id and service.product_category_id.can_be_renew or False,
                        "uom":service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or service.uom_id and service.uom_id.name or '',
                        "id_domain_floor":service.id_domain_floor or '',
                        "is_active":service.is_active or False,
                        "is_auto_renew":service.is_auto_renew or False,
                        "order_ssl_id": service.order_ssl_id or 0,
                        "price": service.price or 0,
                        "vps_code":service.vps_code or '',
                        "os_template":service.os_template or '',
                        "open":service.open or False,
                        "temp_open_date":service.temp_open_date  or '0001-01-01',
                        "is_addons":service.product_category_id and service.product_category_id.is_addons
                                               or False,
                        # "is_protect": is_protect or False,
                    })
                    data.append(item)
                elif type == 'HO' and service.product_category_id.code and service.product_category_id.code[:1] <> '.':
                    item.update({
                        "id": service.id,
                        "name":service.name or '',
                        "reference":service.reference or '',
                        "product_id":service.product_id and service.product_id.default_code or '',
                        "product_category_id": service.product_category_id and service.product_category_id.id or "",
                        "product_category_code":service.product_category_id.code or '',
                        "product_category_name":service.product_category_id.name or '',
                        "parent_product_category_code":
                                    service.product_category_id and service.product_category_id.parent_id and
                                    service.product_category_id.parent_id.code or '',
                        "parent_product_code":
                                    service.parent_product_id and service.parent_product_id.code or '',
                        "ip_hosting":service.ip_hosting or '',
                        "ip_email":service.ip_email or '',
                        "start_date":service.start_date  or '0001-01-01',
                        "end_date":service.end_date  or '0001-01-01',
                        "is_stop":service.is_stop or False,
                        "is_stop_manual": service.is_stop_manual or False,
                        "date_stop":service.date_stop  or '0001-01-01',
                        "temp_stop_date":service.temp_stop_date  or '0001-01-01',
                        "temp_un_stop_date":service.temp_un_stop_date  or '0001-01-01',
                        "write_date":service.write_date  or '0001-01-01',
                        "status":service.status or '',
                        "reseller_id": service.reseller_id and service.reseller_id.id or "",
                        "reseller_code":service.reseller_id and service.reseller_id.code or '',
                        "reseller_type":service.reseller_id and service.reseller_id.company_type or '',
                        "service_type": service_type ,
                        "parent_product_id":service.parent_product_id and service.parent_product_id.default_code or '',
                        "billing_cycle": service.product_category_id and
                                           service.product_category_id.billing_cycle or 0,
                        "sold": service.product_category_id and service.product_category_id.sold or False,
                        "can_be_renew": service.product_category_id and service.product_category_id.can_be_renew or False,
                        "uom":service.product_category_id and service.product_category_id.uom_id and
                                         service.product_category_id.uom_id.name or
                                         service.uom_id and service.uom_id.name or '',
                        "id_domain_floor":service.id_domain_floor or '',
                        "is_active":service.is_active or False,
                        "is_auto_renew":service.is_auto_renew or False,
                        "order_ssl_id": service.order_ssl_id or 0,
                        "price": service.price or 0,
                        "vps_code":service.vps_code or '',
                        "os_template":service.os_template or '',
                        "open":service.open or False,
                        "temp_open_date":service.temp_open_date  or '0001-01-01',
                        "is_addons":service.product_category_id and service.product_category_id.is_addons
                                               or False,
                    })
                    data.append(item)
            else:
                item.update({
                    "id": service.id,
                    "name":service.name or '',
                    "reference":service.reference or '',
                    "product_id":service.product_id and service.product_id.default_code or '',
                    "product_category_id": service.product_category_id and service.product_category_id.id or "",
                    "product_category_code":service.product_category_id.code or '',
                    "product_category_name":service.product_category_id.name or '',
                    "parent_product_category_code":
                                service.product_category_id and service.product_category_id.parent_id and
                                service.product_category_id.parent_id.code or '',
                    "parent_product_code":
                                service.parent_product_id and service.parent_product_id.code or '',
                    "ip_hosting":service.ip_hosting or '',
                    "ip_email":service.ip_email or '',
                    "start_date":service.start_date or '0001-01-01',
                    "end_date":service.end_date  or '0001-01-01',
                    "write_date":service.write_date  or '0001-01-01',
                    "status":service.status or '',

                    "temp_stop_date":service.temp_stop_date  or '0001-01-01',
                    "temp_un_stop_date":service.temp_un_stop_date  or '0001-01-01',
                    "reseller_id": service.reseller_id and service.reseller_id.id or "",
                    "reseller_code":service.reseller_id and service.reseller_id.code or '',
                    "reseller_type":service.reseller_id and service.reseller_id.company_type or '',
                    "service_type": service_type,
                    "parent_product_id":service.parent_product_id and service.parent_product_id.default_code or '',
                    "billing_cycle": service.product_category_id and service.product_category_id.billing_cycle or 0,
                    "sold": service.product_category_id and service.product_category_id.sold or False,
                    "can_be_renew": service.product_category_id and service.product_category_id.can_be_renew or False,
                    "uom":service.product_category_id and
                                     service.product_category_id.uom_id and
                                     service.product_category_id.uom_id.name or
                                     service.uom_id and service.uom_id.name or '',
                    "id_domain_floor":service.id_domain_floor or '',
                    "is_active":service.is_active or False,
                    "is_auto_renew":service.is_auto_renew or False,
                    "is_stop":service.is_stop or False,
                    "is_stop_manual": service.is_stop_manual or False,
                    "date_stop":service.date_stop  or '0001-01-01',
                    "order_ssl_id": service.order_ssl_id or 0,
                    "price": service.price or 0,
                    "vps_code":service.vps_code or '',
                    "os_template":service.os_template or '',
                    "open":service.open or False,
                    "temp_open_date":service.temp_open_date  or '0001-01-01',
                    "is_addons":service.product_category_id and service.product_category_id.is_addons
                                           or False,
                })
                data.append(item)

        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)
