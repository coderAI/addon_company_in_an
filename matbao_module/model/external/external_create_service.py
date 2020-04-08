# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
import logging as _logger

class ExternalActiveService(models.AbstractModel):
    _description = 'Create Product and Service API'
    _name = 'external.create.service'

    def get_parent_product_category(self, categ_id):
        if categ_id and categ_id.parent_id:
            return self.get_parent_product_category(categ_id.parent_id)
        else:
            return categ_id

    @api.model
    def create_service(self, product_name, product_code, product_category_code, customer_code, ip_hosting, ip_email, start_date, end_date, status):
        res = {'code': 0, 'msg': ''}
        IrSequence = self.env['ir.sequence']
        Product = self.env['product.product']
        ProductCategory = self.env['product.category']
        Service = self.env['sale.service']
        if not customer_code:
            res['msg'] = "Customer code could not be empty"
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['msg'] = "Customer not exists"
            return res
        # Create Product
        if not product_name:
            res['msg'] = "Product name could not be empty"
            return res
        if product_code and Product.search([('default_code', '=', product_code)]):
            res['msg'] = "Product already exists."
            return res
        if not product_category_code:
            res['msg'] = "Product category code could not be empty"
            return res
        product_category_id = ProductCategory.search([('code', '=', product_category_code)])
        if not product_category_id:
            res['msg'] = ("Product Category: %s not exists" % product_category_code)
            return res
        try:
            if product_category_code[:2] == 'DM' and product_category_id.name <> product_name[product_name.index('.'):]:
                res['msg'] = "Service not belong Category."
                return res
        except Exception:
            res['msg'] = "Check syntax."
            return res
        product_id = Product.create({
            'default_code': product_code or IrSequence.next_by_code('product.product'),
            'name': product_name,
            'categ_id': product_category_id.id,
            'type': 'service',
            'uom_id': product_category_id.uom_id.id,
            'uom_po_id': product_category_id.uom_id.id,
        })
        if not start_date:
            res['msg'] = "Start Date could not be empty"
            return res
        if not status or status not in ('draft', 'waiting', 'active', 'refused', 'closed'):
            res['msg'] = "Status could not be empty and must belong 'draft', 'waiting', 'active', 'refused' and 'closed'."
            return res
        # Create Service
        Service.create({
            'customer_id': customer_id.id,
            'product_category_id': product_category_id.id,
            'product_id': product_id.id,
            'uom_id': product_id.uom_id.id,
            'ip_hosting': ip_hosting or False,
            'ip_email': ip_email or False,
            'start_date': start_date,
            'end_date': end_date or datetime.now().date(),
            'status': status,
        })
        res['code'] = 1
        return res

    @api.model
    def create_list_service(self, lines=[]):
        res = {'code': 0, 'msg': ''}
        IrSequence = self.env['ir.sequence']
        Product = self.env['product.product']
        ProductCategory = self.env['product.category']
        Service = self.env['sale.service']

        # Check type of data
        if not lines:
            return {'"msg"': '"Lines could not be empty"'}
        if type(lines) is not list:
            return {'"msg"': '"Invalid OrderLineEntity"'}

        for line in lines:
            product_vals = {'type': 'service'}
            service_vals = {}
            # Get Customer for Service
            if not line.get('customer_code',''):
                res['msg'] = "Customer code could not be empty"
                break
            customer_id = self.env['res.partner'].search([('ref', '=', line.get('customer_code',''))])
            if not customer_id:
                res['msg'] = "Customer not exists"
                break
            service_vals.update({'customer_id': customer_id.id})
            # Get Product name
            if not line.get('product_name',''):
                res['msg'] = "Product name could not be empty"
                break
            product_vals.update({'name': line.get('product_name','')})
            # Get product code
            if line.get('product_code','') and Product.search([('default_code', '=', line.get('product_code',''))]):
                res['msg'] = "Product already exists."
                break
            product_vals.update({'default_code': line.get('product_code','') or IrSequence.next_by_code('product.product')})
            # Get product category, product uom, product purchase uom
            if not line.get('product_category_code',''):
                res['msg'] = "Product category code could not be empty"
                break
            product_category_id = ProductCategory.search([('code', '=', line.get('product_category_code',''))])
            if not product_category_id:
                res['msg'] = ("Product Category: %s not exists" % line.get('product_category_code',''))
                break
            product_vals.update({'categ_id': product_category_id.id,
                                 'uom_id': product_category_id.uom_id.id,
                                 'uom_po_id': product_category_id.uom_id.id})
            service_vals.update({'product_category_id': product_category_id.id})
            # try:
            #     if product_category_code[:2] == 'DM' and product_category_id.name <> product_name[product_name.index('.'):]:
            #         res['msg'] = "Service not belong Category."
            #         break
            # except Exception:
            #     res['msg'] = "Check syntax."
            #     break
            # Create Product
            product_id = Product.create(product_vals)
            res['msg'] = "Product %s have create successfully." % product_id.name

            # Get product for service
            service_vals.update({'product_id': product_id.id,
                                 'uom_id': product_id.uom_id.id})
            # Get start date of service
            if not line.get('start_date'):
                res['msg'] = "Start Date could not be empty"
                break
            service_vals.update({'start_date': line.get('start_date')})
            if not line.get('status') or line.get('status','') not in ('draft', 'waiting', 'active', 'refused', 'closed'):
                res['msg'] = "Status could not be empty and must belong 'draft', 'waiting', 'active', 'refused' and 'closed'."
                break
            service_vals.update({'status': line.get('status'),
                                 'ip_hosting': line.get('ip_hosting','') or '',
                                 'ip_email': line.get('ip_email','') or '',
                                 'end_date': line.get('end_date','') or False,})
            # Create Service
            service_id = Service.create(service_vals)
            res['msg'] = "Service %s have create successfully." % service_id.name
        res['code'] = 1
        return res

    @api.model
    def get_service_by_product_wo_customer(self, product):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        SaleService = self.env['sale.service']
        data = []
        services = SaleService.search([('product_id.name', '=', product.strip())])
        # If arguments are ok
        try:
            # Parse data
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
                item.update({
                    '"id"': service.id,
                    '"name"': '\"' + (service.name or '') + '\"',
                    '"reference"': '\"' + (service.reference or '') + '\"',
                    '"customer"': '\"' + (service.customer_id.display_name or '') + '\"',
                    '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                    '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                    '"parent_product_category_code"': '\"' + (service.product_category_id and service.product_category_id.parent_id and
                                                              service.product_category_id.parent_id.code or '') + '\"',
                    '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                    '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                    '"start_date"': '\"' + (service.start_date or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"write_date"': '\"' + (service.write_date or '') + '\"',
                    '"status"': '\"' + (service.status or '') + '\"',
                    '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                    '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                    '"reseller_type"': '\"' + (service.reseller_id and service.reseller_id.company_type or '') + '\"',
                    '"service_type"': '\"' + service_type + '\"',
                    '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                    '"sold"': service.product_category_id and service.product_category_id.sold and '"True"' or '"False"',
                    '"uom"': '\"' + (service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or (service.uom_id and service.uom_id.name or '')) + '\"',
                    '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                    '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                    '"order_ssl_id"': service.order_ssl_id or 0,
                    '"price"': service.price or 0,
                    '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                    '"os_template"': '\"' + (service.os_template or '') + '\"',
                    '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                    '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                })
                data.append(item)
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except Exception as e:
            res['"msg"'] = '"Can not get services %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def get_service_by_product(self, product, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        data = []
        # Check partner
        if not cus_code:
            res.update({'"msg"': '"Customer code could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', cus_code)])
        if not partner_id:
            res.update({'"msg"': '"Customer not found."'})
            return res
        else:
            services = SaleService.search([('customer_id', '=', partner_id.id),
                                           ('product_id.name', '=', product.strip())])
        # If arguments are ok
        try:
            # Parse data
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
                item.update({
                    '"id"': service.id,
                    '"name"': '\"' + (service.name or '') + '\"',
                    '"reference"': '\"' + (service.reference or '') + '\"',
                    '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                    '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                    '"parent_product_category_code"': '\"' + (service.product_category_id and service.product_category_id.parent_id and
                                                              service.product_category_id.parent_id.code or '') + '\"',
                    '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                    '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                    '"start_date"': '\"' + (service.start_date or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"write_date"': '\"' + (service.write_date or '') + '\"',
                    '"status"': '\"' + (service.status or '') + '\"',
                    '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                    '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                    '"reseller_type"': '\"' + (service.reseller_id and service.reseller_id.company_type or '') + '\"',
                    '"service_type"': '\"' + service_type + '\"',
                    '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                    '"sold"': service.product_category_id and service.product_category_id.sold and '"True"' or '"False"',
                    '"uom"': '\"' + (service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or (service.uom_id and service.uom_id.name or '')) + '\"',
                    '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                    '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                    '"order_ssl_id"': service.order_ssl_id or 0,
                    '"price"': service.price or 0,
                    '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                    '"os_template"': '\"' + (service.os_template or '') + '\"',
                    '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                    '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                })
                data.append(item)
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except Exception as e:
            res['"msg"'] = '"Can not get services %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def get_service(self, cus_code, type=False, limit=False, reseller_code='', categ=[], offset=0):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        ResellerCustomer = self.env['reseller.customer']
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = []
        domain = [('end_date', '>=', datetime.now().date() - timedelta(days=60))]
        # Check partner
        if not cus_code:
            res.update({'"msg"': '"Customer code could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', cus_code)])
        if not partner_id:
            res.update({'"msg"': '"Customer not found."'})
            return res
        domain.append(('customer_id', '=', partner_id.id))
        # Check Reseller
        if reseller_code:
            reseller_id = ResellerCustomer.search([('code', '=', reseller_code)])
            if not reseller_id:
                res.update({'"msg"': '"Reseller not found."'})
                return res
            domain.append(('reseller_id', '=', reseller_id.id))
        if type and type not in ('DM', 'HO'):
            res.update({'"msg"': '"Type must be in `DM`, `HO`."'})
            return res
        if categ:
            categ_ids = ProductCategory.search([('code', 'in', list(categ))])
            categ_ids = categ_ids and ProductCategory.search([('id', 'child_of', categ_ids.ids)]) or False
            if categ_ids:
                domain.append(('product_category_id', 'in', categ_ids.ids))
        services = SaleService.search(domain, limit=limit, offset=offset)
        # If arguments are ok
        try:
            # Parse data
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
                            '"id"': service.id,
                            '"name"': '\"' + (service.name or '') + '\"',
                            '"reference"': '\"' + (service.reference or '') + '\"',
                            '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                            '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                            '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                            '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                            '"parent_product_category_code"': '\"' + (service.product_category_id and service.product_category_id.parent_id and
                                                                      service.product_category_id.parent_id.code or '') + '\"',
                            '"parent_product_code"': '\"' + (service.parent_product_id and service.parent_product_id.code or '') + '\"',
                            '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                            '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                            '"start_date"': '\"' + (service.start_date or '') + '\"',
                            '"end_date"': '\"' + (service.end_date or '') + '\"',
                            '"write_date"': '\"' + (service.write_date or '') + '\"',
                            '"is_stop"': '\"' + (service.is_stop and 'True' or 'False') + '\"',
                            '"temp_stop_date"': '\"' + (service.temp_stop_date or '') + '\"',
                            '"temp_un_stop_date"': '\"' + (service.temp_un_stop_date or '') + '\"',
                            '"status"': '\"' + (service.status or '') + '\"',
                            '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                            '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                            '"reseller_type"': '\"' + (service.reseller_id and service.reseller_id.company_type or '') + '\"',
                            '"service_type"': '\"' + service_type + '\"',
                            '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                            '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                            '"sold"': service.product_category_id and service.product_category_id.sold and '"True"' or '"False"',
                            '"can_be_renew"': service.product_category_id and service.product_category_id.can_be_renew and '"True"' or '"False"',
                            '"uom"': '\"' + (service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or (service.uom_id and service.uom_id.name or '')) + '\"',
                            '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                            '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                            '"order_ssl_id"': service.order_ssl_id or 0,
                            '"price"': service.price or 0,
                            '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                            '"os_template"': '\"' + (service.os_template or '') + '\"',
                            '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                            '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                            '"is_addons"': '\"' + (service.product_category_id and service.product_category_id.is_addons
                                                   and 'True' or 'False') + '\"',
                            # '"is_protect"': is_protect and '"True"' or '"False"',
                        })
                        data.append(item)
                    elif type == 'HO' and service.product_category_id.code and service.product_category_id.code[:1] <> '.':
                        item.update({
                            '"id"': service.id,
                            '"name"': '\"' + (service.name or '') + '\"',
                            '"reference"': '\"' + (service.reference or '') + '\"',
                            '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                            '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                            '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                            '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                            '"parent_product_category_code"': '\"' + (
                                        service.product_category_id and service.product_category_id.parent_id and
                                        service.product_category_id.parent_id.code or '') + '\"',
                            '"parent_product_code"': '\"' + (
                                        service.parent_product_id and service.parent_product_id.code or '') + '\"',
                            '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                            '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                            '"start_date"': '\"' + (service.start_date or '') + '\"',
                            '"end_date"': '\"' + (service.end_date or '') + '\"',
                            '"is_stop"': '\"' + (service.is_stop and 'True' or 'False') + '\"',
                            '"temp_stop_date"': '\"' + (service.temp_stop_date or '') + '\"',
                            '"temp_un_stop_date"': '\"' + (service.temp_un_stop_date or '') + '\"',
                            '"write_date"': '\"' + (service.write_date or '') + '\"',
                            '"status"': '\"' + (service.status or '') + '\"',
                            '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                            '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                            '"reseller_type"': '\"' + (service.reseller_id and service.reseller_id.company_type or '') + '\"',
                            '"service_type"': '\"' + service_type + '\"',
                            '"parent_product_id"': '\"' + (service.parent_product_id and
                                                           service.parent_product_id.default_code or '') + '\"',
                            '"billing_cycle"': service.product_category_id and
                                               service.product_category_id.billing_cycle or 0,
                            '"sold"': service.product_category_id and service.product_category_id.sold and
                                      '"True"' or '"False"',
                            '"can_be_renew"': service.product_category_id and service.product_category_id.can_be_renew and '"True"' or '"False"',
                            '"uom"': '\"' + (service.product_category_id and service.product_category_id.uom_id and
                                             service.product_category_id.uom_id.name or
                                             (service.uom_id and service.uom_id.name or '')) + '\"',
                            '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                            '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                            '"order_ssl_id"': service.order_ssl_id or 0,
                            '"price"': service.price or 0,
                            '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                            '"os_template"': '\"' + (service.os_template or '') + '\"',
                            '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                            '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                            '"is_addons"': '\"' + (service.product_category_id and service.product_category_id.is_addons
                                                   and 'True' or 'False') + '\"',
                        })
                        data.append(item)
                else:
                    item.update({
                        '"id"': service.id,
                        '"name"': '\"' + (service.name or '') + '\"',
                        '"reference"': '\"' + (service.reference or '') + '\"',
                        '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                        '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                        '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                        '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                        '"parent_product_category_code"': '\"' + (
                                    service.product_category_id and service.product_category_id.parent_id and
                                    service.product_category_id.parent_id.code or '') + '\"',
                        '"parent_product_code"': '\"' + (
                                    service.parent_product_id and service.parent_product_id.code or '') + '\"',
                        '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                        '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                        '"start_date"': '\"' + (service.start_date or '') + '\"',
                        '"end_date"': '\"' + (service.end_date or '') + '\"',
                        '"write_date"': '\"' + (service.write_date or '') + '\"',
                        '"status"': '\"' + (service.status or '') + '\"',

                        '"temp_stop_date"': '\"' + (service.temp_stop_date or '') + '\"',
                        '"temp_un_stop_date"': '\"' + (service.temp_un_stop_date or '') + '\"',
                        '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                        '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                        '"reseller_type"': '\"' + (service.reseller_id and service.reseller_id.company_type or '') + '\"',
                        '"service_type"': '\"' + service_type + '\"',
                        '"parent_product_id"': '\"' + (service.parent_product_id and
                                                       service.parent_product_id.default_code or '') + '\"',
                        '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                        '"sold"': service.product_category_id and
                                  service.product_category_id.sold and '"True"' or '"False"',
                        '"can_be_renew"': service.product_category_id and service.product_category_id.can_be_renew and '"True"' or '"False"',
                        '"uom"': '\"' + (service.product_category_id and
                                         service.product_category_id.uom_id and
                                         service.product_category_id.uom_id.name or
                                         (service.uom_id and service.uom_id.name or '')) + '\"',
                        '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                        '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                        '"is_stop"': '\"' + (service.is_stop and 'True' or 'False') + '\"',

                        '"order_ssl_id"': service.order_ssl_id or 0,
                        '"price"': service.price or 0,
                        '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                        '"os_template"': '\"' + (service.os_template or '') + '\"',
                        '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                        '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                        '"is_addons"': '\"' + (service.product_category_id and service.product_category_id.is_addons
                                               and 'True' or 'False') + '\"',
                    })
                    data.append(item)

            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except Exception as e:
            res['"msg"'] = '"Can not get services %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def get_service_info(self, partner_id, reference):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = {}

        # Check partner
        if not partner_id and type(partner_id) is not int:
            res.update({'"msg"': '"Customer ID could be not empty and must be number"'})
            return res
        partner = ResPartner.browse(partner_id)
        if not partner:
            res.update({'"msg"': '"Customer not found."'})
            return res

        service = SaleService.search([('customer_id', '=', partner_id), ('reference', '=', reference), ('end_date', '>=', datetime.now().date() - timedelta(days=60))], limit=1)
        if not service:
            res.update({'"msg"': '"Service not found."'})
            return res
        # If arguments are ok
        try:
            # Parse data
            order_line_id = self.env['sale.order.line'].search([('product_id', '=', service.product_id.id),
                                                                ('service_status', '=', 'done')], order='id desc', limit =1)
            # is_protect = 0
            # if service.product_category_id.code and service.product_category_id.code[:1] == '.':
            #     id_protect_category = ProductCategory.search([('code', '=', 'HP20070907103139')], limit=1)
            #     if id_protect_category:
            #         is_protect = SaleService.search_count([('product_id.name', '=', service.product_id.name),
            #                                                ('product_category_id', '=', id_protect_category.id),
            #                                                ('end_date', '>=', datetime.now().date()),
            #                                                ('status', '=', 'active')])
            data.update({
                '"id"': service.id,
                '"name"': '\"' + service.name + '\"',
                '"reference"': '\"' + (service.reference or '') + '\"',
                '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                '"product_category_id"': service.product_category_id.id,
                '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                '"parent_product_category_code"': '\"' + (service.product_category_id and
                                                          service.product_category_id.parent_id and
                                                          service.product_category_id.parent_id.code or '') + '\"',
                '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                '"start_date"': '\"' + (service.start_date or '') + '\"',
                '"end_date"': '\"' + (service.end_date or '') + '\"',
                '"write_date"': '\"' + (service.write_date or '') + '\"',
                '"status"': '\"' + (service.status or '') + '\"',
                '"parent_product_id"': '\"' + (service.parent_product_id and
                                               service.parent_product_id.default_code or '') + '\"',
                '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                '"sold"': service.product_category_id and service.product_category_id.sold and '"True"' or '"False"',
                '"can_be_renew"': service.product_category_id and service.product_category_id.can_be_renew and '"True"' or '"False"',
                '"uom"': '\"' + (service.product_category_id and
                                 service.product_category_id.uom_id and
                                 service.product_category_id.uom_id.name or
                                 (service.uom_id and service.uom_id.name or '')) + '\"',
                '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                '"time"': order_line_id and order_line_id.time or 0,
                '"is_stop"': '\"' + (service.is_stop and 'True' or 'False') + '\"',
                '"temp_stop_date"': '\"' + (service.temp_stop_date or '') + '\"',
                '"temp_un_stop_date"': '\"' + (service.temp_un_stop_date or '') + '\"',

                '"is_active"': service and service.is_active and '"True"' or '"False"',
                '"order_ssl_id"': service.order_ssl_id or 0,
                '"price"': service.price or 0,
                '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                '"os_template"': '\"' + (service.os_template or '') + '\"',
                '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                '"is_addons"': '\"' + (service.product_category_id and service.product_category_id.is_addons
                                       and 'True' or 'False') + '\"',
                # '"is_protect"': is_protect and '"True"' or '"False"',
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def get_service_info_is_protect(self, reference):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = {}
        service = SaleService.search([('reference', '=', reference), ('end_date', '>=', datetime.now().date() - timedelta(days=60))], limit=1)
        if not service:
            res.update({'"msg"': '"Service not found."'})
            return res
        # If arguments are ok
        try:
            is_protect = 0
            if service.product_category_id.code and service.product_category_id.code[:1] == '.':
                id_protect_category = ProductCategory.search([('code', '=', 'HP20070907103139')], limit=1)
                if id_protect_category:
                    is_protect = SaleService.search_count([('product_id.name', '=', service.product_id.name),
                                                           ('product_category_id', '=', id_protect_category.id),
                                                           ('end_date', '>=', datetime.now().date()),
                                                           ('status', '=', 'active')])
            data.update({
                '"is_protect"': is_protect and '"True"' or '"False"',
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def get_service_info_wo_partner(self, reference):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        data = {}

        service = SaleService.search([('reference', '=', reference)], limit=1)
        if not service:
            res.update({'"msg"': '"Service not found."'})
            return res
        # If arguments are ok
        try:
            # Parse data
            data.update({
                '"id"': service.id,
                '"name"': '\"' + service.name + '\"',
                '"customer_id"': '\"' + (service.customer_id.ref or '') + '\"',
                '"reference"': '\"' + (service.reference or '') + '\"',
                '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                '"product_category_id"': service.product_category_id.id,
                '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                '"start_date"': '\"' + (service.start_date or '') + '\"',
                '"end_date"': '\"' + (service.end_date or '') + '\"',
                '"license"': '\"' + (service.license or '') + '\"',
                '"write_date"': '\"' + (service.write_date or '') + '\"',
                '"status"': '\"' + (service.status or '') + '\"',
                '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                '"price"': service.price or 0,
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def update_service(self, po_name, start_date, end_date, ip_hosting, ip_email):
        res = {'"code"': 0, '"msg"': '""'}
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        # Check data
        # Check PO
        if not po_name:
            res['"msg"'] = '"Purchase order name could not be empty"'
            return res
        po = PurchaseOrder.search([('name', '=', po_name)], limit=1)
        if not po:
            res['"msg"'] = '"Purchase order `{}` is not found"'.format(po_name)
            return res
        elif po.state != 'draft':
            res['"msg"'] = \
                '"Status of Purchase Order `{}` must be draft"'.format(po_name)
            return res
        # Check Date
        if not start_date:
            res['"msg"'] = '"Start Date could not be empty"'
            return res

        try:
            system_start_date = self.env['ir.fields.converter']._str_to_date(None, None, start_date)
        except ValueError:

            res['"msg"'] = '"Wrong start date format"'
            return res
        try:
            system_end_date = self.env['ir.fields.converter']._str_to_date(
                None, None, end_date)
            end_date = system_end_date[0]
        except ValueError:
            end_date =False


        if not po.sale_order_line_id:
            res['"msg"'] = '"Purchase order does not have related sale order line"'
            return res
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['"msg"'] = \
                '"Service of purchase order `{}` is not found"'.format(po_name)
            return res
        try:
            po.write({'is_active': True})
            service.write({
                'start_date': system_start_date[0],
                'end_date': end_date,
                'ip_hosting': ip_hosting,
                'ip_email': ip_email,
                'status': 'active'
            })
            # Update SO line
            po.sale_order_line_id.write({
                'service_status': 'done'
            })
            res['"msg"'] = '"Update Successfully!!!"'
            res['"data"'] = service.id
            try:
                tag_ids = po.sale_order_line_id and po.sale_order_line_id.order_id.partner_id and po.sale_order_line_id.order_id.partner_id.category_id or False
                tags = []
                if tag_ids:
                    tags = [tag.name for tag in tag_ids]
                if po.sale_order_line_id and po.sale_order_line_id.product_category_id and po.sale_order_line_id.product_category_id.name not in tags:
                    check_tag = self.env['res.partner.category'].search([('name', '=', po.sale_order_line_id.product_category_id.name)], limit=1)
                    if not check_tag:
                        new_tag = self.env['res.partner.category'].create({
                            'name': po.sale_order_line_id.product_category_id.name,
                            'active': True,
                            'parent_id': False
                        })
                        po.sale_order_line_id.order_id.partner_id.write({
                            'category_id': [(4, new_tag.id)]
                        })
                    else:
                        po.sale_order_line_id.order_id.partner_id.write({
                            'category_id': [(4, check_tag.id)]
                        })
            except Exception as e:
                _logger.error('Could not create and add tags for customer %s' % (e.message or repr(e)))
        except Exception as e:
            res['"msg"'] = '"Can`t update service: %s"' % (e.message or repr(e))
            return res
        res['"code"'] = 1
        return res

    @api.model
    def update_service_upgrade(self, po_name, start_date, end_date, ip_hosting, ip_email):
        res = {'code': 0, 'msg': ''}
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        # Check data
        # Check PO
        if not po_name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', po_name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(po_name)
            return res
        elif po.state != 'draft':
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(po_name)
            return res
        # Check Date
        if not end_date:
            res['msg'] = "End Date could not be empty"
            return res
        try:
            system_end_date = self.env['ir.fields.converter']._str_to_date(
                None, None, end_date)
        except ValueError:
            res['msg'] = 'Wrong end date format'
            return res

        if not po.sale_order_line_id:
            res['msg'] = 'Purchase order does not have related sale order line'
            return res
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(po_name)
            return res
        try:
            po.write({'is_active': True})
            service.write({
                'end_date': system_end_date[0],
                'ip_hosting': ip_hosting,
                'ip_email': ip_email,
                'status': 'active'
            })
            if start_date:
                try:
                    system_start_date = self.env['ir.fields.converter']._str_to_date(None, None, start_date)
                except ValueError:
                    res['msg'] = 'Wrong start date format'
                    return res
                service.write({'start_date': system_start_date[0]})
            # Update SO line
            po.sale_order_line_id.write({
                'service_status': 'done'
            })
            res['msg'] = "Update Successfully!!!"
            try:
                tag_ids = po.sale_order_line_id and po.sale_order_line_id.order_id.partner_id and po.sale_order_line_id.order_id.partner_id.category_id or False
                tags = []
                if tag_ids:
                    tags = [tag.name for tag in tag_ids]
                if po.sale_order_line_id and po.sale_order_line_id.product_category_id and po.sale_order_line_id.product_category_id.name not in tags:
                    check_tag = self.env['res.partner.category'].search([('name', '=', po.sale_order_line_id.product_category_id.name)], limit=1)
                    if not check_tag:
                        new_tag = self.env['res.partner.category'].create({
                            'name': po.sale_order_line_id.product_category_id.name,
                            'active': True,
                            'parent_id': False
                        })
                        po.sale_order_line_id.order_id.partner_id.write({
                            'category_id': [(4, new_tag.id)]
                        })
                    else:
                        po.sale_order_line_id.order_id.partner_id.write({
                            'category_id': [(4, check_tag.id)]
                        })
            except Exception as e:
                _logger.error('Could not create and add tags for customer %s' % (e.message or repr(e)))
        except:
            res['msg'] = "Can't update service"
            return res
        res['code'] = 1
        return res

    @api.model
    def get_service_active(self, date, status='active', category_code='', limit=100):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = []
        args = []
        if not date:
            res['msg'] = "Date could not be empty"
            return res
        try:
            datetime.strptime(str(date), DF)
        except ValueError:
            return {
                'code': 0, 'msg':
                'Invalid Date yyyy-mm-dd',
                'data': {}}
        args += [('end_date', '>=', date), ('end_date', '<', datetime.now().date())]
        if not category_code:
            res['msg'] = "Product Category Code could not be empty"
            return res
        categ_id = ProductCategory.search([('code', '=', category_code)], limit=1)
        if not categ_id:
            res.update({'"msg"': '"Product Category not exists."'})
            return res
        args += [('product_category_id', 'child_of', categ_id.id)]
        if status and status not in ('draft', 'waiting', 'active', 'refused', 'closed'):
            res.update({'"msg"': '"Service must be in `draft`, `waiting` , `active` , `refused` or `closed`."'})
            return res
        args += [('status', '=', status or 'active')]
        service_ids = SaleService.search(args, limit=limit)
        if not service_ids:
            res.update({'"msg"': '"No Service."'})
            return res
        # If arguments are ok 'open', 'temp_open_date'
        try:
            # Parse data
            for service in service_ids:
                data.append({
                    '"id"': service.id,
                    '"name"': '\"' + service.name + '\"',
                    '"customer_id"': '\"' + (service.customer_id.ref or '') + '\"',
                    '"customer"': '\"' + (service.customer_id.name or '') + '\"',
                    '"customer_email"': '\"' + (service.customer_id and service.customer_id.email or '') + '\"',
                    '"sub_email_1"': '\"' + (service.customer_id and service.customer_id.sub_email_1 or '') + '\"',
                    '"reference"': '\"' + (service.reference or '') + '\"',
                    '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                    '"product"': '\"' + (service.product_id and service.product_id.name or '') + '\"',
                    '"product_category_id"': service.product_category_id.id,
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"product_category"': '\"' + (service.product_category_id.display_name or '') + '\"',
                    '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                    '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                    '"start_date"': '\"' + (service.start_date or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"write_date"': '\"' + (service.write_date or '') + '\"',
                    '"status"': '\"' + (service.status or '') + '\"',
                    '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                    '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                    '"reseller"': '\"' + (service.reseller_id and service.reseller_id.name or '') + '\"',
                    '"reseller_email"': '\"' + (service.reseller_id and service.reseller_id.email or '') + '\"',
                    '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    '"parent_product"': '\"' + (service.parent_product_id and service.parent_product_id.name or '') + '\"',
                    '"customer_type"': '\"' + (service.customer_id and service.customer_id.company_type or '') + '\"',
                    '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                    '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['"msg"'] = '"Can not get service"'
            return res
        return res

    @api.model
    def update_status_service(self, reference):
        res = {'code': 0, 'msg': ''}
        SaleService = self.env['sale.service']
        # Check data
        if not reference:
            res['msg'] = "Service Reference could not be empty"
            return res
        service = SaleService.search([('reference', '=', reference)], limit=1)
        if not service:
            res['msg'] = "Service is not found"
            return res
        try:
            service.write({
                'status': 'closed',
                'date_stop': datetime.now(),
                'is_stop_manual': False,
                'stop_user': self._uid
            })
            res['msg'] = "Update Successfully!!!"
        except:
            res['msg'] = "Can't update status service"
            return res
        res['code'] = 1
        return res

    @api.model
    def update_temp_open(self, service_code, cus_code, open=1, content=''):
        res = {'"code"': 0, '"msg"': '""'}
        SaleService = self.env['sale.service']
        ResPartner = self.env['res.partner']
        if not cus_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = ResPartner.search([('ref', '=', cus_code)], limit=1)
        if not customer_id:
            res['"msg"'] = '"Customer not found."'
            return res
        if len(customer_id) > 1:
            res['"msg"'] = '"Have %s Customer"' % len(customer_id)
            return res
        if not service_code:
            res['"msg"'] = '"Service code could not be empty"'
            return res
        service_id = SaleService.search([('reference', '=', service_code), ('customer_id.ref', '=', cus_code)], limit=1)
        if not service_id:
            res['"msg"'] = '"Service not found."'
            return res
        _logger.info("ggggggggggggggg, %s", open)
        if open not in (0, 1):
            res['"msg"'] = '"Open could be not empty and must be in 0 or 1"'
            return res
        vals = {'open': open == 1 and True or False}
        if open == 1:
            vals.update({
                'temp_open_date': datetime.now().date(),
                'temp_open_user': customer_id and customer_id.id or False
            })
        service_id.write(vals)
        if content:
            try:
                service_id.message_post(body=content, subtype="mail.mt_note")
            except Exception as e:
                return {'"code"': 1, '"msg"': '"Cant`t write log: %s"' % (e.message or repr(e))}
        return {'"msg"': '"Update Successfully!!!"', '"code"': 1}

    @api.model
    def get_service_by_days(self, days=30):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        end_date = (datetime.now().date() + timedelta(days=days)).strftime('%Y-%m-%d')
        SaleService = self.env['sale.service']
        # service_ids = SaleService.search([('status', '=', 'active'), ('customer_id.company_type', '=', 'agency'), ('end_date', '=', end_date)])
        service_ids = SaleService.search([('status', '=', 'active'), ('end_date', '=', end_date)])
        data = []
        try:
            for service in service_ids:
                item = {
                    '"customer_code"': '\"' + (service.customer_id.ref or '') + '\"',
                    '"customer_type"': '\"' + (service.customer_id.company_type or '') + '\"',
                    '"sub_email_1"': '\"' + (service.customer_id.sub_email_1 or '') + '\"',
                    '"company_id"': '\"' + (str(service.customer_id.company_id.id) or '') + '\"',
                    '"customer"': '\"' + (service.customer_id.name or '') + '\"',
                    '"email"': '\"' + (service.customer_id.email or '') + '\"',
                    '"mobile"': '\"' + (service.customer_id.mobile or service.customer_id.phone or '') + '\"',
                    '"product"': '\"' + (service.product_id.name or '') + '\"',
                    '"product_category"': '\"' + (service.product_category_id.name or '') + '\"',
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"mst_cmnd"': '\"' + (service.customer_id and service.customer_id.company_type == 'person' and service.customer_id.indentify_number or (service.customer_id.vat or '')) + '\"',
                    '"address"': '\"' + (service.customer_id and service.customer_id.street or '' + (service.customer_id.state_id and (', ' + service.customer_id.state_id.name) or '') + (service.customer_id.country_id and (', ' + service.customer_id.country_id.name) or '')) + '\"',
                }
                data.append(item)
            res.update({'"code"': 1, '"msg"': '"Get Services Successfully"', '"data"': data})
        except Exception as e:
            _logger.error("Get Services error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Get Services error: %s"' % (e.message or repr(e))}
        return res

    @api.model
    def get_service_by_open(self, category_code, date):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        if not category_code:
            res.update({'"msg"': '"Category Code could be not empty."'})
            return res
        categ_id = ProductCategory.search([('code', '=', category_code)], limit=1)
        if not categ_id:
            res.update({'"msg"': '"Product Category not exists."'})
            return res
        if not date:
            return {'"code"': 0, '"msg"': '"Date could be not empty."'}
        data = []
        services = SaleService.search([('open', '=', True), ('status', '=', 'closed'), ('product_category_id', '=', categ_id.id), ('end_date', '>=', date)])
        try:
            for service in services:
                item = {}
                item.update({
                    '"id"': service.id,
                    '"name"': '\"' + service.name + '\"',
                    '"customer_id"': '\"' + (service.customer_id.ref or '') + '\"',
                    '"customer"': '\"' + (service.customer_id.name or '') + '\"',
                    '"customer_email"': '\"' + (service.customer_id and service.customer_id.email or '') + '\"',
                    '"reference"': '\"' + (service.reference or '') + '\"',
                    '"product_id"': '\"' + (service.product_id and service.product_id.default_code or '') + '\"',
                    '"product"': '\"' + (service.product_id and service.product_id.name or '') + '\"',
                    '"product_category_id"': service.product_category_id.id,
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"product_category"': '\"' + (service.product_category_id.display_name or '') + '\"',
                    '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                    '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                    '"start_date"': '\"' + (service.start_date or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"write_date"': '\"' + (service.write_date or '') + '\"',
                    '"status"': '\"' + (service.status or '') + '\"',
                    '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                    '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                    '"reseller"': '\"' + (service.reseller_id and service.reseller_id.name or '') + '\"',
                    '"reseller_email"': '\"' + (service.reseller_id and service.reseller_id.email or '') + '\"',
                    '"parent_product_id"': '\"' + (service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    '"parent_product"': '\"' + (service.parent_product_id and service.parent_product_id.name or '') + '\"',
                    '"customer_type"': '\"' + (service.customer_id and service.customer_id.company_type or '') + '\"',
                })
                data.append(item)
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except Exception as e:
            res['"msg"'] = '"Can not get services: %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def update_product_category_service(self, service, new_code):
        ProductCategory = self.env['product.category']
        SaleService = self.env['sale.service']
        if not service:
            return {'"code"': 0, '"msg"': '"Service Reference could not be empty"'}
        service_id = SaleService.search([('reference', '=', service)])
        if not service_id:
            return {'"code"': 0, '"msg"': '"Service not found."'}
        if len(service_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s services with reference {%s}."' % (len(service_id), service)}

        if not new_code:
            return {'"code"': 0, '"msg"': '"Product Category Code could not be empty"'}
        categ_id = ProductCategory.search([('code', '=', new_code)])
        if not categ_id:
            return {'"code"': 0, '"msg"': '"Product Category not found."'}
        if len(categ_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s Product Category with code {%s}."' % (len(categ_id), new_code)}
        try:
            service_id.product_category_id = categ_id.id
            service_id.product_id.categ_id = categ_id.id
            return {'"code"': 1, '"msg"': '"Updated Successfully Product Category for Service and Product."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Update error: %s"' % (e.message or repr(e))}

    @api.model
    def get_service_by_category_state(self, state=[], category='', cus_code=''):
        res = {'"code"': 0, '"msg"': '', '"data"': {}}
        ResPartner = self.env['res.partner']
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        data = []
        domain = [('status', 'in', state and list(state) or ['draft', 'waiting'])]
        # Check partner
        if cus_code:
            partner_id = ResPartner.search([('ref', '=', cus_code)])
            if not partner_id:
                res.update({'"msg"': '"Customer not found."'})
                return res
            domain.append(('customer_id', '=', partner_id.id))
        if category:
            categ_ids = ProductCategory.search([('code', '=', category)])
            if not categ_ids:
                res.update({'"msg"': '"Category not found."'})
                return res
            categ_ids = categ_ids and ProductCategory.search([('id', 'child_of', categ_ids.ids)]) or False
            if categ_ids:
                domain.append(('product_category_id', 'in', categ_ids.ids))
        services = SaleService.search(domain)
        # If arguments are ok
        try:
            # Parse data
            for service in services:
                item = {}
                item.update({
                    '"id"': service.id,
                    '"name"': '\"' + (service.name or '') + '\"',
                    '"reference"': '\"' + (service.reference or '') + '\"',
                    '"product_id"': '\"' + (
                                service.product_id and service.product_id.default_code or '') + '\"',
                    '"product_category_id"': service.product_category_id and service.product_category_id.id or '""',
                    '"product_category_code"': '\"' + (service.product_category_id.code or '') + '\"',
                    '"product_category_name"': '\"' + (service.product_category_id.name or '') + '\"',
                    '"parent_product_category_code"': '\"' + (
                                service.product_category_id and service.product_category_id.parent_id and
                                service.product_category_id.parent_id.code or '') + '\"',
                    '"ip_hosting"': '\"' + (service.ip_hosting or '') + '\"',
                    '"ip_email"': '\"' + (service.ip_email or '') + '\"',
                    '"start_date"': '\"' + (service.start_date or '') + '\"',
                    '"end_date"': '\"' + (service.end_date or '') + '\"',
                    '"write_date"': '\"' + (service.write_date or '') + '\"',
                    '"status"': '\"' + (service.status or '') + '\"',
                    '"reseller_id"': service.reseller_id and service.reseller_id.id or '""',
                    '"reseller_code"': '\"' + (service.reseller_id and service.reseller_id.code or '') + '\"',
                    '"reseller_type"': '\"' + (
                                service.reseller_id and service.reseller_id.company_type or '') + '\"',
                    '"parent_product_id"': '\"' + (
                                service.parent_product_id and service.parent_product_id.default_code or '') + '\"',
                    '"billing_cycle"': service.product_category_id and service.product_category_id.billing_cycle or 0,
                    '"sold"': service.product_category_id and service.product_category_id.sold and '"True"' or '"False"',
                    '"can_be_renew"': service.product_category_id and service.product_category_id.can_be_renew and '"True"' or '"False"',
                    '"uom"': '\"' + (
                                service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name or (
                                    service.uom_id and service.uom_id.name or '')) + '\"',
                    '"id_domain_floor"': '\"' + (service.id_domain_floor or '') + '\"',
                    '"is_active"': '\"' + (service.is_active and 'True' or 'False') + '\"',
                    '"order_ssl_id"': service.order_ssl_id or 0,
                    '"price"': service.price or 0,
                    '"vps_code"': '\"' + (service.vps_code or '') + '\"',
                    '"os_template"': '\"' + (service.os_template or '') + '\"',
                    '"open"': '\"' + (service.open and 'True' or 'False') + '\"',
                    '"temp_open_date"': '\"' + (service.temp_open_date or '') + '\"',
                    '"is_addons"': '\"' + (service.product_category_id and service.product_category_id.is_addons
                                           and 'True' or 'False') + '\"',
                })
                data.append(item)
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except Exception as e:
            res['"msg"'] = '"Can not get services %s"' % (e.message or repr(e))
            return res
        return res

    @api.model
    def get_customer_code_by_service(self, product, email):
        service_id = self.env['sale.service'].search([('product_id.name', '=', product),
                                                      ('customer_id.email', '=', email)])
        if not service_id:
            return {'"code"': 0, '"msg"': '"Can not find service"'}
        customer_id = service_id.mapped('customer_id')
        return {'"code"': 1, '"msg"': '"Successfully"', '"customer_code"': ['"%s"' % cus.ref for cus in customer_id]}

