# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning

from datetime import datetime
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

DATE_FORMAT = "%Y-%m-%d"
FIELDS_SERVICE_DATA= ['id','name','reference','ip_hosting','ip_email','start_date','end_date','write_date','is_stop','temp_stop_date','temp_un_stop_date','status','id_domain_floor','is_active','order_ssl_id','price','vps_code','os_template','open','temp_open_date']
FIELDS_PRODUCT_CATEGORY_DATA= ['id','name','reference','ip_hosting','ip_email','start_date','end_date','write_date','is_stop','temp_stop_date','temp_un_stop_date','status','id_domain_floor','is_active','order_ssl_id','price','vps_code','os_template','open','temp_open_date']

import logging
_logger = logging.getLogger(__name__)

class bank_transaction(models.Model):
    _inherit = 'bank.transaction'

    account_name = fields.Char(string='Account Name')
    account_number = fields.Char(string='Account Number')

class mb_money_transfer(models.Model):
    _inherit = 'mb.money.transfer'

    account_name = fields.Char(string='Account Name')
    account_number = fields.Char(string='Account Number')



    @api.model
    def create_money_transfer(self, obj):
        code=200
        messages='Successfully'
        transfer_count = self.search_count([('journal_id','=',obj.get('journal_id')),('code','=',obj.get('code'))])
        if transfer_count > 0:
            code= 300
            messages = 'Create Fail Duplicate data'
        else:
            self.create(obj)

        res = {'code': code, 'messages':messages}
        return json.dumps(res)





class product_template(models.Model):
    _inherit = "product.template"
    name = fields.Char('Name', index=True, required=True, translate=True, track_visibility='onchange')

class SaleService(models.Model):
    _inherit = 'sale.service'

    license = fields.Char(string='License')





    def caculate_refund_amount(self, sale_service_data, sale_order_line=None,new_oder_line_price=0):

        refund_amount = 0
        messages = 'Successfully'
        end_date = datetime.strptime(sale_service_data.end_date, DATE_FORMAT)
        if sale_order_line.id:
            if sale_order_line.product_uom.id == 21:
                start_date = end_date - relativedelta(months=int(sale_order_line.time))
            else:
                start_date = end_date - relativedelta(months=int(sale_order_line.time * 12))
            full_payed_date = end_date - start_date
            had_date = end_date - datetime.today()
            used_date = datetime.today() - start_date
            if had_date.days > 0:
                price_subtotal_once_day = int((sale_order_line.price_subtotal - sale_order_line.up_price) / full_payed_date.days)
                if had_date.days >= 0:

                    refund_amount = price_subtotal_once_day * had_date.days
                   #convert to vietnam money can used
                    refund_amount = int(refund_amount/10000)*10000

                    if refund_amount > new_oder_line_price:
                        refund_amount = new_oder_line_price

                else:
                    messages = 'please check again this serviec date'
            else:
                messages = 'please check again this serviec date'
        else:
            messages = 'No have sale order for this serviec'
        return refund_amount, messages


    @api.model
    def get_total_refund(self,ref,new_oder_line_price):
        data=0
        code=200
        sale_service_data = self.sudo().search([('reference','=',ref)],limit=1)
        if sale_service_data.id:
            end_date = datetime.strptime(sale_service_data.end_date, DATE_FORMAT)
            had_date =  end_date - datetime.today()
            sale_order_line_data = self.sudo().env['sale.order.line'].search([('order_partner_id', '=', sale_service_data.customer_id.id),
                                                                              ('company_id','=',sale_service_data.customer_id.company_id.id),
                                                                              ('product_id','=',sale_service_data.product_id.id),
                                                                              ('service_status','=','done'),
                                                                              ('fully_paid','=',True),
                                                                              ],order='create_date DESC',limit=1)

            data,messages = self.caculate_refund_amount(sale_service_data,sale_order_line_data,new_oder_line_price)
            if sale_order_line_data.id:
                if had_date.days > 0:
                    data,messages = self.caculate_refund_amount(sale_service_data,sale_order_line_data,new_oder_line_price)

                else:
                    # code = 401
                    messages = 'please check again this serviec date'
            else:
                # code = 401
                messages = 'No have sale order for this serviec'
        else:
            # code = 400
            messages='This service ref not correct'
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)




    @api.model
    def update_service_name(self,ref,new_name):
        data=''
        code=200
        messages = 'Successfully'
        sale_service_data = self.sudo().search([('reference','=',ref)],limit=1)
        if sale_service_data.id:
            sale_service_data.name = ref+' - '+new_name
            sale_service_data.product_id.product_tmpl_id.name = new_name
            product_id = sale_service_data.product_id.id
            customer_id = sale_service_data.customer_id.id
            # change name parent_product
            for i in self.sudo().search([('parent_product_id', '=', product_id),('customer_id','=',customer_id)]):
                i.name = i.reference + ' - ' + new_name
                i.product_id.product_tmpl_id.name = new_name
        else:
            code = 401
            messages='This service ref not correct'
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)

    @api.model
    def get_addon_list_status(self,ref):
        data=[]
        code=200
        messages = 'Successfully'
        sale_service_data = self.sudo().search([('reference','=',ref)],limit=1)
        if sale_service_data.id:

            for i in sale_service_data.addon_list_ids:
                addon={
                    'product_category_id_name':i.product_category_id.name,
                    'product_category_id_code':i.product_category_id.code,
                    'status':i.status
                }
                data.append(addon)
        else:
            code = 401
            messages='This service ref not correct'
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)




    @api.model
    def get_service_point(self,mb_customer):
        code=200

        messages='Successfully'

        mb = self.env['res.partner'].search([('ref', '=', mb_customer)], limit=1).ids
        data= self.search([('customer_id','=',mb[0])]).read(['name','reference', 'review','review_date','product_category_id','status'])
        field_convert = ['review', 'review_date']
        field_convert_sepcail = ['product_category_id']
        for i_data in data:
            if i_data:
                for i_field in field_convert_sepcail:
                    if i_data[i_field]:
                        categ_data = self.env['product.category'].browse(i_data[i_field][0])

                        categ_code = self.env['product.category'].get_parent_product_category(categ_data.parent_id)
                        if categ_code.code:
                            i_data[i_field] = categ_code.code
                        else:
                            i_data[i_field] = None
                for i_field in field_convert:

                    if i_data[i_field] == False:
                        i_data[i_field] = None
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)




    def search_parent(self,obj,add_list,last_list = []):
        if add_list !=[]:
            add_list = obj.search([('parent_id','in',add_list),('is_addons','=',False)]).ids
            last_list=self.search_parent(obj,add_list,last_list)+add_list
        return last_list

    def root_data_search(self,customer_code, product_category_code, check_root):
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit=1).ids
        product_category_obj = self.env['product.category']
        if check_root:
            parent_product_category = product_category_obj.search([('code','in',product_category_code),('is_addons','=',False)]).ids
            product_category_list = self.search_parent(product_category_obj,parent_product_category)
        else:
            product_category_list = product_category_obj.search([('code', 'in', product_category_code),('is_addons','=',False)]).ids

        return product_category_list,customer_id

    @api.model
    def get_count_service(self,customer_code,product_category_code,check_root = False):
        code=200
        messages='Successfully'
        product_category_list, customer_id = self.root_data_search(customer_code, product_category_code, check_root)
        today = datetime.now().date()
        service_count = self.search_count([('customer_id','=',customer_id[0]),
                                           ('product_category_id', 'in', product_category_list),
                                           '|',
                                           ('end_date','>=',today),
                                           ('end_date','=',False)])
        res = {'code': code, 'messages':messages,'data':service_count}
        return json.dumps(res)


    @api.model
    def get_service_data(self,customer_code,product_category_code,check_root = False):
        code=200
        messages='Successfully'
        product_category_list, customer_id = self.root_data_search(customer_code, product_category_code, check_root)
        today = datetime.now().date()
        service_data = self.search([('customer_id','=',customer_id[0]),
                                           ('product_category_id', 'in', product_category_list),
                                           '|',
                                           ('end_date','>=',today),
                                           ('end_date','=',False)])
        data=[]
        for i in service_data:
            data_tmp = i.read(FIELDS_SERVICE_DATA)[0]
            data_tmp.update({
            'product_id': i.product_id.default_code or '',
            'parent_product_id': i.parent_product_id.default_code or '',
            })
            if i.product_category_id.id:
                tmp_product_category_id = i.product_category_id
                product_category_code = tmp_product_category_id.code
                data_tmp.update({
                'product_category_id': tmp_product_category_id.id,
                'product_category_code': product_category_code,
                'product_category_name': tmp_product_category_id.name,
                'parent_product_category_code': tmp_product_category_id.parent_id and
                        tmp_product_category_id.parent_id.code or '',
                'sold': tmp_product_category_id.sold,
                'can_be_renew': tmp_product_category_id.can_be_renew,
                'is_addons': tmp_product_category_id.is_addons,
                'uom': tmp_product_category_id.uom_id and tmp_product_category_id.uom_id.name or (
                            i.uom_id and i.uom_id.name or None),
                'service_type': product_category_code,
                })
            else:
                data_tmp.update({
                    'product_category_id': None,
                    'product_category_code': None,
                    'product_category_name': None,
                    'parent_product_category_code': None,
                    'sold': None,
                    'can_be_renew': None,
                    'is_addons': None,
                    'uom': None,
                    'service_type': None,
                })
            if i.reseller_id.id:
                tmp_reseller_id = i.reseller_id
                data_tmp.update({
                'reseller_id': tmp_reseller_id.id,
                'reseller_code': tmp_reseller_id.code,
                'reseller_type': tmp_reseller_id.company_type,
                })
            else:
                data_tmp.update({
                    'reseller_id': None,
                    'reseller_code': None,
                    'reseller_type': None,
                })
            data.append(data_tmp)
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)




    def search_parent_code(self,obj,add_list,last_list = []):
        if add_list !=[]:
            add_list = obj.search([('parent_id','in',add_list)]).ids
            last_list=self.search_parent_code(obj,add_list,last_list)+add_list
        return last_list

    def search_parent_list_product_category(self,product_category_code):
        product_category_obj = self.env['product.category']
        parent_product_category = product_category_obj.search(
            [('code', '=', product_category_code)]).ids
        if parent_product_category !=[]:
            add_list = product_category_obj.search([('parent_id','in',parent_product_category)]).ids
            last_list=self.search_parent_code(product_category_obj,add_list)+add_list
        return last_list


    @api.model
    def get_service_datas(self, product_category_code = 'HDDT',active = True):
        code=200
        messages='Successfully'
        product_category_list = self.search_parent_list_product_category(product_category_code)

        service_data = self.search([
                                           ('product_category_id', 'in', product_category_list),
                                           ('status','=',active)])
        data=[]
        for i in service_data:
            data_tmp = i.read('name')[0]
            data_tmp.update({
            'customer_id': i.customer_id.id or None,
            'customer_ref': i.customer_id.ref or None,
            'customer_name': i.customer_id.name or None,
            'name': i.name,
            'product_id': i.product_id.id or None,
            'product_name': i.product_id.name or None,
            'product_code': i.product_id.default_code or None,
            'parent_product_id': i.parent_product_id.default_code or '',
            })
            if i.product_category_id.id:
                tmp_product_category_id = i.product_category_id
                product_category_code = tmp_product_category_id.code
                data_tmp.update({
                'product_category_id': tmp_product_category_id.id,
                'product_category_code': product_category_code,
                'product_category_name': tmp_product_category_id.name,


                })
            else:
                data_tmp.update({
                    'product_category_id': None,
                    'product_category_code': None,
                    'product_category_name': None,

                })

            data.append(data_tmp)
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)
