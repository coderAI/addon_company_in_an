# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
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

from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare
import json
import logging
logging.basicConfig(filename='E:\\log.txt',level=logging.DEBUG)
_logger = logging.getLogger(__name__)

class ExternalPO(models.AbstractModel):
    _description = 'External PO API'
    _name = 'external.po'

    def _convert_str(self, value):
        if type(value) is str:
            return (unicode(value, "utf-8")).strip()
        else:
            return value

    @api.model
    def get_po_detail(self, name):
        res = {'code': 0, 'msg': '', 'data': []}
        PurchaseOrder = self.env['purchase.order']
        # Check PO
        if not name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(name)
            return res
        elif po.state != 'draft':
            res['msg'] = "Status of Purchase Order '{}' must be draft".format(name)
            return res

        # If arguments are ok
        try:
            # Parse data
            data = []
            data += ['name: ' + '\"' + po.name + '\"',
                     'date_order: ' + '\"' + po.date_order + '\"',
                     'state: ' + '\"' + po.state + '\"',
                     'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                     'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                     'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                     'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                     'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""]
            po_line_append = {}
            data_append = []
            for line in po.order_line:
                service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                start_date = service_id and service_id[0].start_date or datetime.now().date().strftime('%Y-%m-%d')
                end_date = service_id and service_id[0].end_date or datetime.now().date().strftime('%Y-%m-%d')
                po_line_append['poline_id'] = '\"' + str(line.id) + '\"'
                po_line_append['product_code'] = '\"' + (line.product_id.default_code or '') + '\"'
                po_line_append['product_name'] = '\"' + (line.product_id.name or '') + '\"'
                po_line_append['qty'] = '\"' + str(int(line.product_qty)) + '\"'
                po_line_append['uom'] = '\"' + (line.product_uom.name or '') + '\"'
                po_line_append['register_type'] = '\"' + (line.register_type or '') + '\"'
                po_line_append['category_code'] = '\"' + (line.product_id.categ_id.code or '') + '\"'
                po_line_append['start_date'] = '\"' + start_date + '\"'
                po_line_append['end_date'] = '\"' + end_date + '\"'
                po_line_append['company_id'] = '\"' + (line.company_id and str(line.company_id.id) or '0') + '\"'
                po_line_append['template'] = '\"' + (line.template or '') + '\"'
                po_line_append['service_code'] = '\"' + (service_id and service_id.reference or '') + '\"'
                po_line_append['customer_code'] = '\"' + (service_id and service_id.customer_id.ref or '') + '\"'
                po_line_append['company_type'] = '\"' + (service_id and service_id.customer_id.company_type or '') + '\"'
                data_append.append(po_line_append)
            data.append(data_append)
            res.update({'code': 1, 'msg': "'Get PO %s successfully!'" % name, 'data': data})
        except:
            res['msg'] = "Can't get PO"
            return res
        return res

    @api.model
    def get_po_by_state(self, type, is_active, state=False, register_type=False, date_from=False, date_to=False, limit=None, order='date_order'):
        """
            TO DO:
            - Get Purchase  Order from Odoo by state
        """
        res = {'code': 0, 'msg': 'Process PO Successful!', 'data': []}
        PurchaseOrder = self.env['purchase.order']
        error_msg = ''
        args = [('product_id.categ_id.manual_active', '=', False)]

        # Check Type
        if not type and type not in (1,2,3):
            res.update({'code': 0, 'msg': 'Type could not empty and must be in 1,2,3'})
            return res

        # Check Is Active
        if not is_active and is_active not in (0,1):
            res.update({'code': 0, 'msg': 'Type could not empty and must be in 0 or 1'})
            return res
        if is_active == 0:
            args += [('is_active', '=', False)]
        else:
            args += [('is_active', '=', True)]

        # Check state
        invalid_states = ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']
        if state and state not in invalid_states:
            error_msg += 'Invalid state, '
        if state and not error_msg:
            args += [('state', '=', state)]

        # Check Register Type
        if register_type and register_type not in ('register', 'renew', 'transfer', 'upgrade'):
            res.update({'code': 0, 'msg': 'Type could not empty and must be in `register`, `renew`, `upgrade` and `transfer`'})
            return res

        # Check date from
        if date_from:
            try:
                system_date_from = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_from))
                args += [('date_order', '>=', system_date_from[0])]
            except ValueError:
                error_msg += 'Wrong DATE FROM format, '

        # Check Date to
        if date_to:
            try:
                system_date_to = \
                    self.env['ir.fields.converter']._str_to_datetime(
                        None, None, str(date_to))
                args += [('date_order', '<=', system_date_to[0])]
            except ValueError:
                error_msg += 'Wrong DATE TO format, '

        # Check limit argument
        try:
            if limit:
                if not isinstance(limit, int) or int(limit) < 1:
                    error_msg += 'Invalid limit'
        except ValueError:
            error_msg += 'Invalid limit'

        # Return error
        if error_msg:
            res.update({'msg': error_msg})
            return res

        args += [('is_error', '!=', True), '|', ('retry_count', '=', 0), ('retry_count', '=', False)]
        # _logger.info("\n--------------------------- %s -------------------------- " % args)
        # If arguments are ok
        try:
            po_recs = PurchaseOrder.search(args, limit=limit, order=order)
            if not po_recs:
                res.update({'code': 1, 'msg': '', 'data': []})
                return res

            # Parse data
            data = []
            for po in po_recs:
                service = self.env['sale.service'].search([('product_id', '=', po.product_id.id)], limit=1)
                # Check domain .vn
                if type == 1:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(line.register_type == register_type for line in po.mapped('order_line'))) \
                            and categs and any(c.code and c.code.strip()[:1] == '.' and (c.code.strip()[-3:] == '.vn' or c.code.strip()[-5:] == '.tmtv') for c in categs):
                        data_append = ['name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"', 'state: ' + '\"' + po.state + '\"',
                                       'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                                       'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                                       'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                                       'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                                       'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                                       'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                                       'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                                       'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                                       'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) == 1:
                                start_date = service_id and service_id[0].start_date or datetime.now().date().strftime('%Y-%m-%d')
                                end_date = service_id and service_id[0].end_date or datetime.now().date().strftime('%Y-%m-%d')
                                po_line_append['poline_id'] = '\"' + str(line.id) + '\"'
                                po_line_append['product_code'] = '\"' + (line.product_id.default_code or '') + '\"'
                                po_line_append['product_name'] = '\"' + (line.product_id.name or '') + '\"'
                                po_line_append['qty'] = '\"' + str(int(line.product_qty)) + '\"'
                                po_line_append['uom'] = '\"' + (line.product_uom.name or '') + '\"'
                                po_line_append['register_type'] = '\"' + (line.register_type or '') + '\"'
                                po_line_append['category_code'] = '\"' + (line.product_id.categ_id.code or '') + '\"'
                                po_line_append['category_name'] = '\"' + (line.product_id.categ_id.name or '') + '\"'
                                po_line_append['is_addons'] = '\"' + (line.product_id.categ_id and line.product_id.categ_id.is_addons and 'True' or 'False') + '\"'
                                po_line_append['start_date'] = '\"' + start_date + '\"'
                                po_line_append['end_date'] = '\"' + end_date + '\"'
                                po_line_append['company_id'] = '\"' + (line.company_id and str(line.company_id.id) or '0') + '\"'
                                po_line_append['template'] = '\"' + (line.template or '') + '\"'
                                po_line_append['service_code'] = '\"' + (service_id and service_id.reference or '') + '\"'
                                po_line_append['service_name'] = '\"' + (service_id and service_id.name or '') + '\"'
                                po_line_append['customer_code'] = '\"' + (service_id and service_id.customer_id.ref or '') + '\"'
                                po_line_append['company_type'] = '\"' + (service_id and service_id.customer_id.company_type or '') + '\"'
                                data_append.append([po_line_append])
                            else:
                                data_append.append([{
                                    'poline_id': '""',
                                    'product_code': '""',
                                    'product_name': '""',
                                    'qty': '""',
                                    'uom': '""',
                                    'register_type': '""',
                                    'category_code': '""',
                                    'category_name': '""',
                                    'is_addons': '""',
                                    'start_date': '""',
                                    'end_date': '""',
                                    'company_id': '""',
                                    'template': '""',
                                    'service_code': '""',
                                    'service_name': '""',
                                    'customer_code': '""',
                                    'company_type': '""',
                                }])
                        data.append(data_append)
                # Check domain QT
                elif type == 2:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(line.register_type == register_type for line in po.mapped('order_line'))) \
                            and categs and any(c.code and c.code.strip()[:1] == '.' and c.code.strip()[-3:] <> '.vn' and c.code.strip()[-5:] <> '.tmtv' for c in categs):
                        data_append = ['name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"', 'state: ' + '\"' + po.state + '\"',
                                       'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                                       'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                                       'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                                       'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                                       'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                                       'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                                       'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                                       'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                                       'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) == 1:
                                start_date = service_id and service_id[0].start_date or datetime.now().date().strftime('%Y-%m-%d')
                                end_date = service_id and service_id[0].end_date or datetime.now().date().strftime('%Y-%m-%d')
                                po_line_append['poline_id'] = '\"' + str(line.id) + '\"'
                                po_line_append['product_code'] = '\"' + (line.product_id.default_code or '') + '\"'
                                po_line_append['product_name'] = '\"' + (line.product_id.name or '') + '\"'
                                po_line_append['qty'] = '\"' + str(int(line.product_qty)) + '\"'
                                po_line_append['uom'] = '\"' + (line.product_uom.name or '') + '\"'
                                po_line_append['register_type'] = '\"' + (line.register_type or '') + '\"'
                                po_line_append['category_code'] = '\"' + (line.product_id.categ_id.code or '') + '\"'
                                po_line_append['category_name'] = '\"' + (line.product_id.categ_id.name or '') + '\"'
                                po_line_append['is_addons'] = '\"' + (line.product_id.categ_id and line.product_id.categ_id.is_addons and 'True' or 'False') + '\"'
                                po_line_append['start_date'] = '\"' + start_date + '\"'
                                po_line_append['end_date'] = '\"' + end_date + '\"'
                                po_line_append['company_id'] = '\"' + (line.company_id and str(line.company_id.id) or '0') + '\"'
                                po_line_append['template'] = '\"' + (line.template or '') + '\"'
                                po_line_append['service_code'] = '\"' + (service_id and service_id.reference or '') + '\"'
                                po_line_append['service_name'] = '\"' + (service_id and service_id.name or '') + '\"'
                                po_line_append['customer_code'] = '\"' + (service_id and service_id.customer_id.ref or '') + '\"'
                                po_line_append['company_type'] = '\"' + (service_id and service_id.customer_id.company_type or '') + '\"'
                                data_append.append([po_line_append])
                            else:
                                data_append.append([{
                                    'poline_id': '""',
                                    'product_code': '""',
                                    'product_name': '""',
                                    'qty': '""',
                                    'uom': '""',
                                    'register_type': '""',
                                    'category_code': '""',
                                    'category_name': '""',
                                    'is_addons': '""',
                                    'start_date': '""',
                                    'end_date': '""',
                                    'company_id': '""',
                                    'template': '""',
                                    'service_code': '""',
                                    'service_name': '""',
                                    'customer_code': '""',
                                    'company_type': '""',
                                }])
                        data.append(data_append)
                # Check hosting
                else:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(line.register_type == register_type for line in po.mapped('order_line'))) and \
                            categs and any(c.code and c.code.strip()[:1] <> '.' for c in categs):
                        data_append = ['name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"', 'state: ' + '\"' + po.state + '\"',
                                       'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                                       'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                                       'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                                       'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                                       'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                                       'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                                       'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                                       'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                                       'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) == 1:
                                start_date = service_id and service_id[0].start_date or datetime.now().date().strftime('%Y-%m-%d')
                                end_date = service_id and service_id[0].end_date or datetime.now().date().strftime('%Y-%m-%d')
                                po_line_append['poline_id'] = '\"' + str(line.id) + '\"'
                                po_line_append['product_code'] = '\"' + (line.product_id.default_code or '') + '\"'
                                po_line_append['product_name'] = '\"' + (line.product_id.name or '') + '\"'
                                po_line_append['qty'] = '\"' + str(int(line.product_qty)) + '\"'
                                po_line_append['uom'] = '\"' + (line.product_uom.name or '') + '\"'
                                po_line_append['register_type'] = '\"' + (line.register_type or '') + '\"'
                                po_line_append['category_code'] = '\"' + (line.product_id.categ_id.code or '') + '\"'
                                po_line_append['category_name'] = '\"' + (line.product_id.categ_id.name or '') + '\"'
                                po_line_append['is_addons'] = '\"' + (line.product_id.categ_id and line.product_id.categ_id.is_addons and 'True' or 'False') + '\"'
                                po_line_append['start_date'] = '\"' + start_date + '\"'
                                po_line_append['end_date'] = '\"' + end_date + '\"'
                                po_line_append['company_id'] = '\"' + (line.company_id and str(line.company_id.id) or '0') + '\"'
                                po_line_append['template'] = '\"' + (line.template or '') + '\"'
                                po_line_append['service_code'] = '\"' + (service_id and service_id.reference or '') + '\"'
                                po_line_append['service_name'] = '\"' + (service_id and service_id.name or '') + '\"'
                                po_line_append['customer_code'] = '\"' + (service_id and service_id.customer_id.ref or '') + '\"'
                                po_line_append['company_type'] = '\"' + (service_id and service_id.customer_id.company_type or '') + '\"'
                                data_append.append([po_line_append])
                            else:
                                data_append.append([{
                                    'poline_id': '""',
                                    'product_code': '""',
                                    'product_name': '""',
                                    'qty': '""',
                                    'uom': '""',
                                    'register_type': '""',
                                    'category_code': '""',
                                    'category_name': '""',
                                    'is_addons': '""',
                                    'start_date': '""',
                                    'end_date': '""',
                                    'company_id': '""',
                                    'template': '""',
                                    'service_code': '""',
                                    'service_name': '""',
                                    'customer_code': '""',
                                    'company_type': '""',
                                }])
                        data.append(data_append)
            res.update({'code': 1, 'msg': "''", 'data': data})
        except UserError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except ValueError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except:
            error_msg += 'Unknow Error, '
            res['msg'] = error_msg
            return res
        return res

    # @api.model
    # def process_po(
    #         self, name, result, vendor_code,
    #         ip_hosting, ip_email, start_date, end_date, memo=False, vals={}):
    #     res = {'code': 0, 'msg': ''}
    #     ResPartner = self.env['res.partner']
    #     PurchaseOrder = self.env['purchase.order']
    #     SaleService = self.env['sale.service']
    #     ProductProduct = self.env['product.product']
    #     PurchaseOrderLine = self.env['purchase.order.line']
    #     AccountInvoice = self.env['account.invoice']
    #     AccountTax = self.env['account.tax']
    #
    #     # Validate data before process
    #     if not name:
    #         res['msg'] = "Purchase order name could not be empty"
    #         return res
    #     po = PurchaseOrder.search([('name', '=', name)], limit=1)
    #     if not po:
    #         res['msg'] = "Purchase order '{}' is not found".format(name)
    #         return res
    #     elif po.state != 'draft':
    #         res['msg'] = \
    #             "Status of Purchase Order '{}' must be draft".format(name)
    #         return res
    #     if not result:
    #         res['msg'] = "Fail to register"
    #     if not vendor_code:
    #         res['msg'] = "Vendor code could not be empty"
    #         return res
    #     vendor = ResPartner.search([('ref', '=', vendor_code),
    #                                 ('supplier', '=', True)], limit=1)
    #     if not vendor:
    #         res['msg'] = "Vendor '{}' is not found".format(vendor_code)
    #         return res
    #     if not start_date:
    #         res['msg'] = "Start date could not be empty"
    #         return res
    #     if not end_date:
    #         res['msg'] = "End date could not be empty"
    #         return res
    #
    #     try:
    #         system_start_date = self.env[
    #             'ir.fields.converter']._str_to_date(
    #             None, None, start_date)
    #     except ValueError:
    #         res['msg'] = 'Wrong start date format'
    #         return res
    #
    #     try:
    #         system_end_date = self.env[
    #             'ir.fields.converter']._str_to_date(
    #             None, None, end_date)
    #     except ValueError:
    #         res['msg'] = 'Wrong end date format'
    #         return res
    #
    #     if not po.sale_order_line_id:
    #         res['msg'] = 'Purchase order does not have related sale order line'
    #         return res
    #     service = SaleService.search(
    #         [('so_line_id', '=', po.sale_order_line_id.id)], limit=1)
    #     if not service:
    #         res['msg'] = \
    #             "Service of purchase order '{}' is not found".format(name)
    #         return res
    #
    #     if not vals.get('price_unit'):
    #         res['msg'] = "Vals does not have price unit"
    #         return res
    #
    #     tax_id = False
    #     if vals.get('tax'):
    #         tax_id = AccountTax.search([
    #             ('amount', '=', float(vals['tax']))], limit=1)
    #         if not tax_id:
    #             res['msg'] = "### Can't find Tax"
    #             return res
    #
    #     if vals.get('poline_id'):
    #         po_line = PurchaseOrderLine.browse(vals['poline_id'])
    #         if not po_line:
    #             res['msg'] = "Purchase order line '{}' is not found".format(
    #                 vals['poline_id'])
    #             return res
    #     else:
    #         if not vals.get('product_code'):
    #             res['msg'] = "Vals does not have product code"
    #             return res
    #         if not vals.get('product_name'):
    #             res['msg'] = "Vals does not have product name"
    #             return res
    #         product_code = self._convert_str(vals['product_code'])
    #         product_name = self._convert_str(vals['product_name'])
    #         product = ProductProduct.search(
    #             [('name', '=', product_name),
    #              ('default_code', '=', product_code)])
    #         if not product:
    #             res['msg'] = \
    #                 "Product with name and code is not found"
    #             return res
    #         po_line = PurchaseOrderLine.search(
    #             [('product_id', '=', product.id),
    #              ('order_id', '=', po.id)], limit=1)
    #         if not po_line:
    #             res['msg'] = \
    #                 "Purchase order line of given product is not found"
    #             return res
    #
    #     if result:
    #         # Confirm Purchase Order
    #         po.partner_id = vendor
    #         po_line.write({'price_unit': vals['price_unit'],
    #                        'taxes_id': [(6, 0, tax_id and [tax_id.id] or [])]})
    #         po_line._compute_amount()
    #         po._amount_all()
    #         po.button_confirm()
    #         po.button_done()
    #
    #         # Update Sales Order line
    #         po.sale_order_line_id.write({
    #             'service_status': 'done'
    #         })
    #
    #         # Create Vendor Bill
    #         data = po.action_view_invoice()
    #         if 'default_journal_id' in data['context']:
    #             data['context'].pop('default_journal_id')
    #         fields = [field for field in AccountInvoice._fields]
    #         default_bill_vals = AccountInvoice.with_context(
    #             data['context']).default_get(fields)
    #
    #         vendor_bill = AccountInvoice.new(default_bill_vals)
    #         vendor_bill.purchase_id = data['context']['default_purchase_id']
    #         vendor_bill.purchase_order_change()
    #
    #         bill_vals = AccountInvoice._convert_to_write(vendor_bill._cache)
    #         bill_vals.update({
    #             'purchase_id': data['context']['default_purchase_id'],
    #             'origin': po.name})
    #
    #         vendor_bill = AccountInvoice.create(bill_vals)
    #         vendor_bill.invoice_line_ids.write(
    #             {'price_unit': po_line.price_unit,
    #              'register_type': po_line.register_type})
    #         vendor_bill.compute_taxes()
    #         vendor_bill.action_invoice_open()
    #
    #         # Match Payments
    #         payment_vals = json.loads(
    #             vendor_bill.outstanding_credits_debits_widget)
    #         paid_amount = 0.0
    #
    #         if payment_vals and payment_vals.get('content'):
    #             for line in payment_vals['content']:
    #                 paid_amount += line['amount']
    #
    #         if not vendor_bill.has_outstanding or \
    #                         float_compare(paid_amount, vendor_bill.amount_total,
    #                                       precision_digits=2) < 0:
    #             self._cr.rollback()
    #             res['msg'] = \
    #                 "Vendor Bill cannot be reconciled"
    #             return res
    #         else:
    #             balance_amount = vendor_bill.amount_total
    #             for line in payment_vals['content']:
    #                 if float_compare(
    #                         balance_amount, 0, precision_digits=2) <= 0:
    #                     # fully paid
    #                     break
    #                 vendor_bill.assign_outstanding_credit(line['id'])
    #                 balance_amount -= line['amount']
    #
    #         # Update Service
    #         service.write({'start_date': system_start_date[0],
    #                        'end_date': system_end_date[0],
    #                        'ip_hosting': ip_hosting,
    #                        'ip_email': ip_email,
    #                        'status': 'active'})
    #
    #         res['code'] = 1
    #     else:
    #         # cancel purchase order
    #         po.button_cancel()
    #
    #         # Update Sales Order line
    #         po.sale_order_line_id.write({
    #             'service_status': 'refused'
    #         })
    #
    #         # Update Service
    #         service.write({
    #             'status': 'refused'})
    #
    #         res['code'] = 1
    #     return res

    @api.model
    def process_po(self, name, result, vendor_code, ip_hosting, ip_email, start_date, end_date, memo=False, vals={}):
        res = {'code': 0, 'msg': ''}
        ResPartner = self.env['res.partner']
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        ProductProduct = self.env['product.product']
        PurchaseOrderLine = self.env['purchase.order.line']
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        AccountTax = self.env['account.tax']

        # Validate data before process

        # _logger.info("\n--------------------------- Start Process PO %s -------------------------- " % name)
        # _logger.info("\n--------------------------- Check data -------------------------- ")
        if not name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(name)
            return res
        elif po.state != 'draft':
            
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(name)
            return res
        if not result:
            
            res['msg'] = "Fail to register"
            return res
        if not vendor_code:
            
            res['msg'] = "Vendor code could not be empty"
            return res
        vendor = ResPartner.search([('ref', '=', vendor_code), ('supplier', '=', True)], limit=1)
        if not vendor:
            
            res['msg'] = "Vendor '{}' is not found".format(vendor_code)
            return res
        if not start_date:
            
            res['msg'] = "Start date could not be empty"
            return res
        if not end_date:
            
            res['msg'] = "End date could not be empty"
            return res

        try:
            system_start_date = self.env['ir.fields.converter']._str_to_date(None, None, start_date)
        except ValueError:
            
            res['msg'] = 'Wrong start date format'
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
        # service = SaleService.search([('so_line_id', '=', po.sale_order_line_id.id)], limit=1)
        # service = SaleService.search([('sales_order_ids', 'in', po.sale_order_line_id and po.sale_order_line_id.order_id.id)], limit=1)
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and
                                       po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(name)
            return res

        # if not vals.get('price_unit'):
        #     res['msg'] = "Vals does not have price unit"
        #     return res

        tax_id = False
        if vals.get('tax'):
            tax_id = AccountTax.search([
                ('amount', '=', float(vals['tax']))], limit=1)
            if not tax_id:
                
                res['msg'] = "### Can't find Tax"
                return res

        if vals.get('poline_id'):
            po_line = PurchaseOrderLine.browse(vals['poline_id'])
            if not po_line:
                
                res['msg'] = "Purchase order line '{}' is not found".format(
                    vals['poline_id'])
                return res
        else:
            if not vals.get('product_code'):
                
                res['msg'] = "Vals does not have product code"
                return res
            if not vals.get('product_name'):
                
                res['msg'] = "Vals does not have product name"
                return res
            product_code = self._convert_str(vals['product_code'])
            product_name = self._convert_str(vals['product_name'])
            product = ProductProduct.search(
                [('name', '=', product_name),
                 ('default_code', '=', product_code)])
            if not product:
                
                res['msg'] = \
                    "Product with name and code is not found"
                return res
            po_line = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('order_id', '=', po.id)], limit=1)
            if not po_line:
                
                res['msg'] = \
                    "Purchase order line of given product is not found"
                return res
        # _logger.info("\n--------------------------- Completed check data -------------------------- ")
        if result:
            # Confirm Purchase Order
            # _logger.info("\n--------------------------- Confirm Purchase Order -------------------------- ")

            po.partner_id = vendor
            po_line.write({
                # 'price_unit': vals.get('price_unit1', 0) and (vals.get('price_unit', 0) + vals.get('price_unit1', 0)) or vals.get('price_unit', 0),
                'taxes_id': [(6, 0, tax_id and [tax_id.id] or [])]
            })
            po_line._compute_amount()
            po._amount_all()
            po.button_confirm()
            po.button_done()

            # Update Sales Order line
            # _logger.info("\n--------------------------- Update Sales Order line -------------------------- ")
            po.sale_order_line_id.write({
                'service_status': 'done'
            })
            if vals.get('price_unit', 0) > 0 or vals.get('price_unit1', 0) > 0:
                # Create Vendor Bill
                data = po.action_view_invoice()
                if 'default_journal_id' in data['context']:
                    data['context'].pop('default_journal_id')
                fields = [field for field in AccountInvoice._fields]
                default_bill_vals = AccountInvoice.with_context(data['context']).default_get(fields)

                vendor_bill = AccountInvoice.new(default_bill_vals)
                vendor_bill.purchase_id = data['context']['default_purchase_id']
                vendor_bill.purchase_order_change()
                bill_vals = AccountInvoice._convert_to_write(vendor_bill._cache)
                bill_vals.update({
                    'purchase_id': data['context']['default_purchase_id'],
                    'origin': po.name})
                bill_vals1 = dict(bill_vals)

                domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', vendor.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                if vals.get('price_unit', 0) > 0:
                    try:
                        # _logger.info("\n--------------------------- Create Vendor Bill (register) to Vendor %s --------------------------" % vendor.name)
                        
                        vendor_bill = AccountInvoice.with_context(force_company=vendor.company_id.id).create(bill_vals)
                        # _logger.info("\n--------------------------- Create Vendor Bill (register) successfully --------------------------")
                        # _logger.info("\n--------------------------- Write Vendor Bill (register): journal = %s, company_id = %s, account = %s -------------------------- " %
                        #               (journal_id.name, vendor.company_id.name, vendor.with_context(force_company=vendor.company_id.id).property_account_payable_id.code))
                        
                        vendor_bill.write({
                            'company_id': vendor.company_id.id,
                            'journal_id': journal_id.id,
                            'account_id': vendor.property_account_payable_id and vendor.with_context(force_company=vendor.company_id.id).property_account_payable_id.id,
                        })
                        # _logger.info("\n--------------------------- Write Vendor Bill Lines: price_unit = %s, quantity = %s, register_type = %s -------------------------- " %
                        #               (vals['price_unit'], po_line.register_type == 'renew' and po_line.product_qty or 1, po_line.register_type))
                        
                        vendor_bill.invoice_line_ids.write(
                            {'price_unit': vals['price_unit'],
                             'quantity': po_line.register_type == 'renew' and po_line.product_qty or 1,
                             'register_type': po_line.register_type})
                        for line in vendor_bill.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=vendor.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })
                                # _logger.info("\n--------------------------- Write Vendor Bill Lines: account = %s -------------------------- " % account)

                            # analytic = AccountInvoiceLine.with_context(force_company=vendor.company_id.id).get_account_analytic_id(
                            #     line.product_id, 'in_invoice', line.register_type)
                            # if analytic:
                            #     line.write({
                            #         'account_analytic_id': analytic
                            #     })
                        vendor_bill.with_context(force_company=vendor.company_id.id).compute_taxes()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill 1"
                        return res
                    try:
                        # _logger.info("\n--------------------------- Validate Vendor Bill (register) -------------------------- ")

                        vendor_bill.with_context(force_company=vendor.company_id.id).action_invoice_open()
                        # _logger.info("\n--------------------------- Validate Vendor Bill (register) successfully -------------------------- ")
                    except:
                        res['msg'] = "Can't validate Vendor Bill 1"
                        return res
                    try:
                        # Match Payments
                        _logger.info("\n--------------------------- Match Payments -------------------------- ")

                        payment_vals = json.loads(
                            vendor_bill.with_context(force_company=vendor.company_id.id).outstanding_credits_debits_widget)
                        _logger.info("\n--------------------------- Check Payments: %s -------------------------- " % payment_vals)

                        paid_amount = 0.0

                        if payment_vals and payment_vals.get('content'):
                            for line in payment_vals['content']:
                                paid_amount += line['amount']

                        if not vendor_bill.has_outstanding or \
                                        float_compare(paid_amount, vendor_bill.amount_total,
                                                      precision_digits=2) < 0:
                            # self._cr.rollback()
                            res['msg'] = \
                                "Vendor Bill cannot be reconciled"
                            return res
                        else:
                            balance_amount = vendor_bill.amount_total
                            for line in payment_vals['content']:
                                if float_compare(
                                        balance_amount, 0, precision_digits=2) <= 0:
                                    # fully paid
                                    break
                                _logger.info("\n--------------------------- Subtract Payments: %s -------------------------- " % line['id'])
                                
                                vendor_bill.with_context(force_company=vendor.company_id.id).assign_outstanding_credit(line['id'])
                                balance_amount -= line['amount']
                                
                    except:
                        res['msg'] = "Can't reconcile Vendor Bill 1"
                        return res

                if vals.get('price_unit1', 0) > 0:
                    try:
                        vendor_bill1 = AccountInvoice.with_context(force_company=vendor.company_id.id).create(bill_vals1)
                        vendor_bill1.write({
                            'company_id': vendor.company_id.id,
                            'journal_id': journal_id.id,
                            'account_id': vendor.property_account_payable_id and vendor.with_context(force_company=vendor.company_id.id).property_account_payable_id.id,
                        })
                        vendor_bill1.invoice_line_ids.write(
                            {'price_unit': vals['price_unit1'],
                             'quantity': po_line.product_qty,
                             'register_type': 'renew'})
                        for line in vendor_bill1.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=vendor.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill 2"
                        return res
                    vendor_bill1.with_context(force_company=vendor.company_id.id).compute_taxes()
                    try:
                        vendor_bill1.with_context(force_company=vendor.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't validate Vendor Bill 2"
                        return res

                    # Match Payment
                    try:
                        payment_vals1 = json.loads(vendor_bill1.outstanding_credits_debits_widget)
                        paid_amount = 0.0
                        if payment_vals1 and payment_vals1.get('content'):
                            for line in payment_vals1['content']:
                                paid_amount += line['amount']
                        if not vendor_bill1.has_outstanding or \
                                        float_compare(paid_amount, vendor_bill1.amount_total,
                                                      precision_digits=2) < 0:
                            self._cr.rollback()
                            res['msg'] = \
                                "Vendor Bill 2 cannot be reconciled"
                            return res
                        else:
                            balance_amount = vendor_bill1.amount_total
                            for line in payment_vals1['content']:
                                if float_compare(
                                        balance_amount, 0, precision_digits=2) <= 0:
                                    # fully paid
                                    break
                                vendor_bill1.with_context(force_company=vendor.company_id.id).assign_outstanding_credit(line['id'])
                                balance_amount -= line['amount']
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't reconcile Vendor Bill 2"
                        return res

            # Update PO
            po.write({
                'is_success': True
            })
            # Update Service
            service.write({
                            # 'start_date': system_start_date[0],
                           # 'end_date': system_end_date[0], # khong cap nhat end date cho dich vu
                           'ip_hosting': ip_hosting,
                           'ip_email': ip_email,
                           'status': 'active'})

            res['code'] = 1
        else:
            # cancel purchase order
            po.button_cancel()

            # # Update Sales Order line
            # po.sale_order_line_id.write({
            #     'service_status': 'refused'
            # })
            #
            # # Update Service
            # service.write({
            #     'status': 'refused'})

            res['code'] = 1

        return res

    @api.model
    def update_po_company(self, name, account1, cus_code1, account2, cus_code2, account3, cus_code3, result, vendor_code, ip_hosting, ip_email, start_date, end_date, vals={}):
        res = {'code': 0, 'msg': ''}
        ResPartner = self.env['res.partner']
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        ProductProduct = self.env['product.product']
        PurchaseOrderLine = self.env['purchase.order.line']
        AccountInvoice = self.env['account.invoice']
        AccountTax = self.env['account.tax']
        AccountAccount = self.env['account.account']
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line']
        # Validate data before process
        if not name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(name)
            return res
        elif po.state != 'draft':
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(name)
            return res
        if not result:
            res['msg'] = "Fail to register"
        if not vendor_code:
            res['msg'] = "Vendor code could not be empty"
            return res
        vendor = ResPartner.search([('ref', '=', vendor_code), ('supplier', '=', True)], limit=1)
        if not vendor:
            res['msg'] = "Vendor '{}' is not found".format(vendor_code)
            return res
        if not start_date:
            res['msg'] = "Start date could not be empty"
            return res
        if not end_date:
            res['msg'] = "End date could not be empty"
            return res

        try:
            system_start_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, start_date)
        except ValueError:
            res['msg'] = 'Wrong start date format'
            return res

        try:
            system_end_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, end_date)
        except ValueError:
            res['msg'] = 'Wrong end date format'
            return res

        if not po.sale_order_line_id:
            res['msg'] = 'Purchase order does not have related sale order line'
            return res
        # service = SaleService.search([('so_line_id', '=', po.sale_order_line_id.id)], limit=1)
        # service = SaleService.search([('sales_order_ids', 'in', po.sale_order_line_id and po.sale_order_line_id.order_id.id)], limit=1)
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and
                                       po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(name)
            return res
        if not vals.get('price_unit'):
            res['msg'] = "Vals %s does not have price unit" % vals
            return res

        tax_id = False
        if vals.get('tax'):
            tax_id = AccountTax.search([
                ('amount', '=', float(vals['tax']))], limit=1)
            if not tax_id:
                res['msg'] = "### Can't find Tax"
                return res

        if vals.get('poline_id'):
            po_line = PurchaseOrderLine.browse(vals['poline_id'])
            if not po_line:
                res['msg'] = "Purchase order line '{}' is not found".format(
                    vals['poline_id'])
                return res
        else:
            if not vals.get('product_code'):
                res['msg'] = "Vals does not have product code"
                return res
            if not vals.get('product_name'):
                res['msg'] = "Vals does not have product name"
                return res
            product_code = self._convert_str(vals['product_code'])
            product_name = self._convert_str(vals['product_name'])
            product = ProductProduct.search(
                [('name', '=', product_name),
                 ('default_code', '=', product_code)])
            if not product:
                res['msg'] = \
                    "Product with name and code is not found"
                return res
            po_line = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('order_id', '=', po.id)], limit=1)
            if not po_line:
                res['msg'] = \
                    "Purchase order line of given product is not found"
                return res
        if not account1 or not account2 or not account3:
            res['msg'] = "Account1, Account2, Account could be not empty"
            return res

        if result:
            # Confirm Purchase Order
            po.partner_id = vendor
            po_line.write({'price_unit': vals['price_unit1'] and vals['price_unit'] + vals['price_unit1'] or vals['price_unit'],
                           'taxes_id': [(6, 0, tax_id and [tax_id.id] or [])]})
            po_line._compute_amount()
            po._amount_all()
            po.button_confirm()
            po.button_done()

            # Update Sales Order line
            po.sale_order_line_id.write({
                'service_status': 'done'
            })

            # Create Vendor Bill
            data = po.action_view_invoice()
            if 'default_journal_id' in data['context']:
                data['context'].pop('default_journal_id')
            fields = [field for field in AccountInvoice._fields]
            default_bill_vals = AccountInvoice.with_context(
                data['context']).default_get(fields)

            vendor_bill = AccountInvoice.new(default_bill_vals)
            vendor_bill.purchase_id = data['context']['default_purchase_id']
            vendor_bill.purchase_order_change()
            bill_vals = AccountInvoice._convert_to_write(vendor_bill._cache)
            bill_vals.update({
                'purchase_id': data['context']['default_purchase_id'],
                'origin': po.name})
            bill_vals1 = dict(bill_vals)

            account1_id = AccountAccount.search([('code', '=', account1)], limit=1)
            if not cus_code1:
                res['msg'] = "Customer 1 could be not empty"
                return res
            cus1_id = ResPartner.search([('ref', '=', cus_code1)])
            if not cus1_id:
                res['msg'] = "Customer 1 not exists"
                return res
            if not account1_id:
                res['msg'] = "Account1 not exists"
                return res

            if vals.get('price_unit1'):
                vendor_bill1 = AccountInvoice.new(default_bill_vals)
                vendor_bill1.purchase_id = data['context']['default_purchase_id']
                vendor_bill1.purchase_order_change()
            vendor_bill = AccountInvoice.create(bill_vals)
            vendor_bill.write({
                'partner_id': cus1_id.id,
                'company_id': po.company_id.id
            })
            vendor_bill.invoice_line_ids.write(
                {'price_unit': vals['price_unit'],
                 'quantity': 1,
                 'register_type': po_line.register_type})
            vendor_bill.compute_taxes()
            vendor_bill.account_id = account1_id.id
            vendor_bill.action_invoice_open()
            if vendor_bill.move_id:
                for line in vendor_bill.move_id.line_ids:
                    if line.credit > 0:
                        line.partner_id = cus1_id.id
                    if line.debit > 0:
                        line.partner_id = False

            if vals.get('price_unit1'):
                vendor_bill1 = AccountInvoice.create(bill_vals1)
                vendor_bill1.write({
                    'partner_id': cus1_id.id,
                })
                vendor_bill1.invoice_line_ids.write(
                    {'price_unit': vals['price_unit1'],
                     'quantity': 1,
                     'partner_id': cus1_id.id,
                     'register_type': 'renew'})
                vendor_bill1.compute_taxes()
                vendor_bill1.account_id = account1_id.id
                vendor_bill1.action_invoice_open()
                if vendor_bill1.move_id:
                    for line in vendor_bill1.move_id.line_ids:
                        if line.credit > 0:
                            line.partner_id = cus1_id.id
                        if line.debit > 0:
                            line.partner_id = False

            # Create Moves
            if not cus_code2:
                res['msg'] = "Customer 2 could be not empty"
                return res
            cus2_id = ResPartner.search([('ref', '=', cus_code2)])
            if not cus2_id:
                res['msg'] = "Customer 2 not exists"
                return res
            if not cus_code3:
                res['msg'] = "Customer 3 could be not empty"
                return res
            cus3_id = ResPartner.search([('ref', '=', cus_code3)])
            if not cus3_id:
                res['msg'] = "Customer 3 not exists"
                return res
            account2_id = AccountAccount.search([('code', '=', account2)], limit=1)
            if not account2_id:
                res['msg'] = "Account2 not exists"
                return res
            account3_id = AccountAccount.search([('code', '=', account3)], limit=1)
            if not account3_id:
                res['msg'] = "Account3 not exists"
                return res
            move_vals = {
                'date': datetime.now().date(),
                'journal_id': vendor_bill.journal_id.id,
                # 'name': 'Công nợ',
                'line_ids': [(0, 0, {
                    'account_id': account2_id.id,
                    'debit': vals.get('price_unit'),
                    'credit': 0,
                    'name': 'Công nợ',
                    'partner_id': cus2_id.id,
                }), (0, 0, {
                    'account_id': account3_id.id,
                    'debit': 0,
                    'credit': vals.get('price_unit'),
                    'date': datetime.now().date(),
                    'name': 'Phải trả nhà cung cấp',
                    'partner_id': cus3_id.id,
                })],
                'company_id': account3_id.company_id.id,
            }
            move = AccountMove.with_context(apply_taxes=True).create(move_vals)
            move.update({
                'company_id': account3_id.company_id.id
            })
            if move.line_ids:
                move.line_ids.write({
                    'company_id': account3_id.company_id.id
                })

            domain = [('account_id', '=', account3_id.id),
                      ('partner_id', '=', cus3_id.id),
                      ('reconciled', '=', False),
                      ('amount_residual', '!=', 0.0),
                      ('credit', '=', 0), ('debit', '>', 0)]
            lines = self.env['account.move.line'].search(domain)
            if not lines:
                self._cr.rollback()
                res['msg'] = "Journal Entries can't reconcile."
                return res
            move.post()
            move_lines_filtered = move.line_ids.filtered(lambda aml: not aml.reconciled and aml.account_id.internal_type in ('payable', 'receivable') and aml.account_id == account3_id)

            if move_lines_filtered:
                (move_lines_filtered + lines).reconcile()

            if vals.get('price_unit1') > 0:
                move_vals1 = {
                    'date': datetime.now().date(),
                    'journal_id': vendor_bill1.journal_id.id,
                    # 'name': 'Công nợ',
                    'line_ids': [(0, 0, {
                        'account_id': account2_id.id,
                        'debit': vals.get('price_unit1'),
                        'credit': 0,
                        'name': 'Công nợ',
                        'partner_id': cus2_id.id,
                    }), (0, 0, {
                        'account_id': account3_id.id,
                        'debit': 0,
                        'credit': vals.get('price_unit1'),
                        'date': datetime.now().date(),
                        'name': 'Phải trả nhà cung cấp',
                        'partner_id': cus3_id.id,
                    })],
                    'company_id': account3_id.company_id.id,
                }
                move1 = AccountMove.with_context(apply_taxes=True).create(move_vals1)
                move1.update({
                    'company_id': account3_id.company_id.id
                })
                if move1.line_ids:
                    move1.line_ids.write({
                        'company_id': account3_id.company_id.id
                    })

                domain1 = [('account_id', '=', account3_id.id),
                          ('partner_id', '=', cus3_id.id),
                          ('reconciled', '=', False),
                          ('amount_residual', '!=', 0.0),
                          ('credit', '=', 0), ('debit', '>', 0)]
                lines1 = self.env['account.move.line'].search(domain1)
                if not lines1:
                    self._cr.rollback()
                    res['msg'] = "Journal Entries 1 can't reconcile."
                    return res
                move1.post()
                move_lines_filtered1 = move1.line_ids.filtered(
                    lambda aml: not aml.reconciled and aml.account_id.internal_type in (
                    'payable', 'receivable') and aml.account_id == account3_id)

                if move_lines_filtered1:
                    (move_lines_filtered1 + lines1).reconcile()

            # Update Service
            service.write({
                # 'start_date': system_start_date[0],
                #            'end_date': system_end_date[0],
                           'ip_hosting': ip_hosting,
                           'ip_email': ip_email,
                           'status': 'active'})

            res['code'] = 1
        else:
            # cancel purchase order
            po.button_cancel()

            # Update Sales Order line
            po.sale_order_line_id.write({
                'service_status': 'refused'
            })

            # Update Service
            service.write({
                'status': 'refused'})

            res['code'] = 1
        return res

    @api.model
    def update_po_final(self, name, cus_code1, cus_code2, cus_code3, result, vendor_code, ip_hosting, ip_email, start_date, end_date, vals={}):
        res = {'code': 0, 'msg': ''}
        ResPartner = self.env['res.partner']
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        ProductProduct = self.env['product.product']
        PurchaseOrderLine = self.env['purchase.order.line']
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        AccountTax = self.env['account.tax']
        AccountAccount = self.env['account.account']
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line']
        # Validate data before process
        if not name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(name)
            return res
        elif po.state != 'draft':
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(name)
            return res
        if not result:
            res['msg'] = "Fail to register"
        if not vendor_code:
            res['msg'] = "Vendor code could not be empty"
            return res
        vendor = ResPartner.search([('ref', '=', vendor_code), ('supplier', '=', True)], limit=1)
        if not vendor:
            res['msg'] = "Vendor '{}' is not found".format(vendor_code)
            return res
        if not start_date:
            res['msg'] = "Start date could not be empty"
            return res
        if not end_date:
            res['msg'] = "End date could not be empty"
            return res
        try:
            system_start_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, start_date)
        except ValueError:
            res['msg'] = 'Wrong start date format'
            return res
        try:
            system_end_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, end_date)
        except ValueError:
            res['msg'] = 'Wrong end date format'
            return res

        if not po.sale_order_line_id:
            res['msg'] = 'Purchase order does not have related sale order line'
            return res
        # service = SaleService.search([('sales_order_ids', 'in', po.sale_order_line_id and po.sale_order_line_id.order_id.id)], limit=1)
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and
                                       po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(name)
            return res
        # if not vals.get('price_unit'):
        #     res['msg'] = "Vals %s does not have price unit" % vals
        #     return res

	    _logger.info('666666666666666666')
        tax_id = False
        if 'tax' in vals:
            tax_id = AccountTax.search([
                ('amount', '=', float(vals['tax']))], limit=1)
            if not tax_id:
                res['msg'] = "### Can't find Tax"
                return res
        _logger.info('666666666666xxxxxxxxxxxx666666')
        if vals.get('poline_id'):
            _logger.info('666666666666xxxxxx999999999999999xxxxxx666666 %s' % vals.get('poline_id') )
            po_line = PurchaseOrderLine.browse(vals['poline_id'])
            _logger.info('666666666666xxxxxx999999999999999xxxxxx666666 %s' % po_line )
            if not po_line:
                res['msg'] = "Purchase order line '{}' is not found".format(
                    vals['poline_id'])
                return res
        else:
            _logger.info('666666666666x55555555555555xxxxxxxxxxxx666666')
            if not vals.get('product_code'):
                res['msg'] = "Vals does not have product code"
                return res
            if not vals.get('product_name'):
                res['msg'] = "Vals does not have product name"
                return res
            product_code = self._convert_str(vals['product_code'])
            product_name = self._convert_str(vals['product_name'])
            product = ProductProduct.search(
                [('name', '=', product_name),
                 ('default_code', '=', product_code)])
            if not product:
                res['msg'] = \
                    "Product with name and code is not found"
                return res
            po_line = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('order_id', '=', po.id)], limit=1)
            if not po_line:
                res['msg'] = \
                    "Purchase order line of given product is not found"
                return res
        _logger.info('666666666666x55555xxxxxxxxxxxxxxxxx555555555xxxxxxxxxxxx666666')
        if result:
            if not cus_code1 or not cus_code2 or not cus_code3:
                res['msg'] = "Customer 1, Customer 2 and Customer 3 could be not empty"
                return res
            cus1_id = ResPartner.search([('ref', '=', cus_code1)])
            if not cus1_id:
                res['msg'] = "Customer 1 not exists"
                return res
            cus2_id = ResPartner.search([('ref', '=', cus_code2)])
            if not cus2_id:
                res['msg'] = "Customer 2 not exists"
                return res
            cus3_id = ResPartner.search([('ref', '=', cus_code3)])
            if not cus3_id:
                res['msg'] = "Customer 3 not exists"
                return res
            # Confirm Purchase Order
            po.partner_id = vendor
            po_line.write({
                # 'price_unit': vals.get('price_unit', 0) + vals.get('price_unit1', 0),
                'taxes_id': [(6, 0, tax_id and [tax_id.id] or [])]
            })
            po_line._compute_amount()
            po._amount_all()
            po.button_confirm()
            po.button_done()


            # Update Sales Order line
            po.sale_order_line_id.write({
                'service_status': 'done'
            })
            if vals.get('price_unit', 0) > 0 or vals.get('price_unit1',0) > 0:
                # ===================================== Create Vendor Bill ======================================#
                data = po.action_view_invoice()
                _logger.info('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                if 'default_journal_id' in data['context']:
                    data['context'].pop('default_journal_id')
                fields = [field for field in AccountInvoice._fields]
                default_bill_vals = AccountInvoice.with_context(
                    data['context']).default_get(fields)

                vendor_bill = AccountInvoice.new(default_bill_vals)
                vendor_bill.purchase_id = data['context']['default_purchase_id']
                vendor_bill.purchase_order_change()
                bill_vals = AccountInvoice._convert_to_write(vendor_bill._cache)
                domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', cus1_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                bill_vals.update({
                    'purchase_id': data['context']['default_purchase_id'],
                    'origin': po.name,
                })
                bill_vals1 = dict(bill_vals)

                line_vals = bill_vals.get('invoice_line_ids')
                if vals.get('price_unit', 0) > 0:
                    try:
                        vendor_bill = AccountInvoice.with_context(force_company=cus1_id.company_id.id).create(bill_vals)

                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (register) for %s." % cus2_id.name
                        return res
                    vendor_bill.write({
                        'partner_id': cus2_id.id,
                        'company_id': cus1_id.company_id.id,
                        'journal_id': journal_id.id,
                        'account_id': cus1_id.property_account_payable_id and cus1_id.with_context(force_company=cus1_id.company_id.id).property_account_payable_id.id,
                    })
                    vendor_bill.invoice_line_ids.write(
                        {'price_unit': vals['price_unit'],
                         'quantity': po_line.register_type == 'renew' and po_line.product_qty or 1,
                         'register_type': po_line.register_type})
                    for line in vendor_bill.invoice_line_ids:
                        account = AccountInvoiceLine.with_context(force_company=cus1_id.company_id.id).get_account_id(line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                        # fpos = vendor_bill.with_context(force_company=cus1_id.company_id.id).fiscal_position_id
                        # account = line.get_invoice_line_account('in_invoice', line.product_id.with_context(force_company=cus1_id.company_id.id), fpos, cus1_id.company_id)
                        if account:
                            line.write({
                                'account_id': type(account).__name__ == 'int' and account or account.id
                            })
                        analytic = AccountInvoiceLine.with_context(force_company=cus1_id.company_id.id).get_account_analytic_id(
                            line.product_id, 'in_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })
                    vendor_bill.with_context(force_company=cus1_id.company_id.id).compute_taxes()
                    try:
                        vendor_bill.with_context(force_company=cus1_id.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill (register) can't validate."

                        return res
                    if vendor_bill.move_id:
                        for line in vendor_bill.move_id.line_ids:
                            if line.credit > 0:
                                line.partner_id = cus2_id.id
                            if line.debit > 0:
                                line.partner_id = False

                if vals.get('price_unit1', 0) > 0:
                    _logger.info('YYYYYYYYYYYYYYYYYY111111111111111YYYYYYYYYYYYYYYYY')
                    vendor_bill1 = AccountInvoice.new(default_bill_vals)
                    vendor_bill1.purchase_id = data['context']['default_purchase_id']
                    vendor_bill1.purchase_order_change()
                    _logger.info('YYYYYYYYYYYYYYYYYY22222222222222227777777777777777772222222YYYYYYYYYYYYYYYYY' )
                    try:
                        
                        
                        _logger.info('YYYYYYYYYYYYYYYYYY2222222222222222yyyyyyyyyyyyyyyyy2222222YYYYYYYYYYYYYYYYY' )
                        _logger.info('YYYYYYYYYYYYYYYYYY2222222222222999999999999992222222222YYYYYYYYYYYYYYYYY %s ' % bill_vals1 )
                        vendor_bill1 = AccountInvoice.with_context(force_company=cus1_id.company_id.id).create(bill_vals1)
                    except:
                        _logger.info('YYYYYYYYYYYYYYYYYY222222222222223333333333333222222222YYYYYYYYYYYYYYYYY %s ' % bill_vals1 )
                        _logger.info('YYYYYYYYYYYYYYYYYY22222222222222222222222YYYYYYYYYYYYYYYYY %s ' % cus1_id.company_id.id)
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (renew)."
                        return res
		    
                    vendor_bill1.write({
                        'partner_id': cus2_id.id,
                        'company_id': cus1_id.company_id.id,
                        'journal_id': journal_id.id,
                        'account_id': cus1_id.property_account_payable_id and cus1_id.with_context(force_company=cus1_id.company_id.id).property_account_payable_id.id,
                    })
                    vendor_bill1.invoice_line_ids.write(
                        {'price_unit': vals['price_unit1'],
                         # 'quantity': 1,
                         'partner_id': cus2_id.id,
                         'register_type': 'renew'})
                    for line in vendor_bill1.invoice_line_ids:
                        account = AccountInvoiceLine.with_context(force_company=cus1_id.company_id.id).get_account_id(
                            line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                        if account:
                            line.write({
                                'account_id': type(account).__name__ == 'int' and account or account.id
                            })
                        analytic = AccountInvoiceLine.with_context(force_company=cus1_id.company_id.id).get_account_analytic_id(
                            line.product_id, 'in_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })

                    vendor_bill1.with_context(force_company=cus1_id.company_id.id).compute_taxes()
                    try:

                        vendor_bill1.with_context(force_company=cus1_id.company_id.id).action_invoice_open()

                    except:
                        _logger.info('8888888888888888888888888888 %s ' % cus1_id.company_id.id)
                        self._cr.rollback()
                        res['msg'] = "Can't validate Vendor Bill (renew) 1"

                        return res
                    if vendor_bill1.move_id:
                        for line in vendor_bill1.move_id.line_ids:
                            if line.credit > 0:
                                line.partner_id = cus2_id.id
                            if line.debit > 0:
                                line.partner_id = False

                # ==================================== Create Customer Invoice ==================================#
                default_invoice_vals = AccountInvoice.default_get(fields)
                customer_invoice = AccountInvoice.new(default_invoice_vals)
                cus_vals = AccountInvoice._convert_to_write(customer_invoice._cache)
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', cus2_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                cus_vals.update({
                    'partner_id': cus1_id.id,
                })
                try:

                    customer_invoice = AccountInvoice.with_context(force_company=cus2_id.company_id.id).create(cus_vals)

                    customer_invoice.write({
                        'journal_id': journal_id.id,
                        'account_id': cus2_id.property_account_receivable_id and cus2_id.with_context(force_company=cus2_id.company_id.id).property_account_receivable_id.id,
                        'company_id': cus2_id.company_id.id
                    })
                    cus_line_vals = []
                    if line_vals:
                        if vals.get('price_unit', 0) > 0 and line_vals[1]:
                            cus_line_vals.append(line_vals[1])
                        if vals.get('price_unit1', 0) > 0 and line_vals[1]:
                            cus_line_vals.append(line_vals[1])
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).write({
                        'invoice_line_ids': cus_line_vals
                    })
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).invoice_line_ids.write({
                        'price_unit': vals['price_unit'],
                        'company_id': cus2_id.company_id.id,
                        'quantity': 1,
                        'time': po_line.register_type == 'renew' and po_line.product_qty or 1,
                        'register_type': po_line.register_type,
                        'purchase_line_id': False
                     })
                    if vals.get('price_unit1', 0) > 0 and customer_invoice.invoice_line_ids:
                        for line in customer_invoice.invoice_line_ids:
                            if line == customer_invoice.invoice_line_ids[-1]:
                                line.write({
                                    'register_type': 'renew',
                                    'price_unit': vals.get('price_unit1'),
                                    'time': po_line.product_qty,
                                    'quantity': po_line.product_qty
                                })
                            else:
                                line.write({
                                    'register_type': po_line.register_type,
                                    'time': po_line.register_type == 'renew' and po_line.product_qty or 1
                                })

                    for line in customer_invoice.invoice_line_ids:
                        account_id = AccountInvoiceLine.with_context(force_company=cus2_id.company_id.id).get_account_id(
                            line.product_id, 'out_invoice', line.register_type, line.invoice_line_tax_ids)
                        if account_id:
                            line.write({
                                'account_id': type(account_id).__name__ == 'int' and account_id or account_id.id
                            })

                        analytic = AccountInvoiceLine.with_context(force_company=cus2_id.company_id.id).get_account_analytic_id(
                            line.product_id, 'out_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })
                except:
                    self._cr.rollback()
                    res['msg'] = "Can't create Customer Invoice"

                    return res

                try:
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).action_invoice_open()
                except:
                    self._cr.rollback()
                    res['msg'] = "Customer Invoice can't validate."

                    return res

                # ====================================== Create Vendor Bill =======================================#
                default_vendor_vals_ncc = AccountInvoice.with_context(type='in_invoice', journal_type='purchase').default_get(fields)
                vendor_bill_ncc = AccountInvoice.new(default_vendor_vals_ncc)
                bill_vals_ncc = AccountInvoice._convert_to_write(vendor_bill_ncc._cache)
                domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', cus3_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                bill_vals_ncc.update({
                    'partner_id': cus3_id.id,
                })
                bill_vals1_ncc = dict(bill_vals_ncc)
                if vals.get('price_unit', 0) > 0:
                    try:

                        vendor_bill_ncc = AccountInvoice.with_context(force_company=cus3_id.company_id.id).create(bill_vals_ncc)

                        vendor_bill_ncc.write({
                            'journal_id': journal_id.id,
                            'account_id': cus3_id.property_account_payable_id and cus3_id.with_context(
                                force_company=cus3_id.company_id.id).property_account_payable_id.id,
                            'company_id': cus3_id.company_id.id
                        })
                        vendor_bill_ncc.write({
                            'invoice_line_ids': line_vals
                        })
                        vendor_bill_ncc.invoice_line_ids.write({
                            'price_unit': vals['price_unit'],
                            'company_id': cus3_id.company_id.id,
                            'register_type': po_line.register_type,
                            'quantity': po_line.register_type == 'renew' and po_line.product_qty or 1,
                            'purchase_line_id': False
                        })
                        for line in vendor_bill_ncc.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })

                            analytic = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_analytic_id(
                                line.product_id, 'in_invoice', line.register_type)
                            if analytic:
                                line.write({
                                    'account_analytic_id': analytic
                                })

                        vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).compute_taxes()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill for Vendor"

                        return res
                    try:
                        vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill (register) for %s can't validate." % cus3_id.name
                        return res
                    # Match Payments

                    payment_vals = json.loads(
                        vendor_bill_ncc.with_context(
                            force_company=cus3_id.company_id.id).outstanding_credits_debits_widget)

                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill_ncc.has_outstanding or \
                                    float_compare(paid_amount, vendor_bill_ncc.amount_total,
                                                  precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = \
                            "Vendor Bill cannot be reconciled"

                        return res
                    else:
                        balance_amount = vendor_bill_ncc.amount_total
                        for line in payment_vals['content']:
                            if float_compare(
                                    balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break

                            vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

                if vals.get('price_unit1', 0) > 0:
                    try:

                        vendor_bill1_ncc = AccountInvoice.with_context(force_company=cus3_id.company_id.id).create(bill_vals1_ncc)
                        vendor_bill1_ncc.write({
                            'partner_id': cus3_id.id,
                            'company_id': cus3_id.company_id.id,
                            'journal_id': journal_id.id,
                            'account_id': cus3_id.property_account_payable_id and cus3_id.with_context(force_company=cus3_id.company_id.id).property_account_payable_id.id,
                        })
                        vendor_bill1_ncc.write({
                            'invoice_line_ids': line_vals
                        })
                        vendor_bill1_ncc.invoice_line_ids.write({
                            'price_unit': vals['price_unit1'],
                            'partner_id': cus3_id.id,
                            'register_type': 'renew',
                            'purchase_line_id': False
                        })
                        for line in vendor_bill1_ncc.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })

                            analytic = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_analytic_id(
                                line.product_id, 'in_invoice', line.register_type)
                            if analytic:
                                line.write({
                                    'account_analytic_id': analytic
                                })

                        vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).compute_taxes()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (renew) for Vendor."
                        return res
                    try:
                        vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't validate Vendor Bill (renew) for Vendor."
                        return res
                    # Match Payment
                    payment_vals = json.loads(
                        vendor_bill1_ncc.with_context(
                            force_company=cus3_id.company_id.id).outstanding_credits_debits_widget)
                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill1_ncc.has_outstanding or \
                                    float_compare(paid_amount, vendor_bill1_ncc.amount_total,
                                                  precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = \
                            "Vendor Bill cannot be reconciled"


                        return res
                    else:
                        balance_amount = vendor_bill1_ncc.amount_total
                        for line in payment_vals['content']:
                            if float_compare(
                                    balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break

                            vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

            # Update PO
            po.write({
                'is_success': True
            })
            # Update Service
            service.write({
                            # 'start_date': system_start_date[0],
                           # 'end_date': system_end_date[0],
                           'ip_hosting': ip_hosting,
                           'ip_email': ip_email,
                           'status': 'active'})

            res['code'] = 1
        else:
            # cancel purchase order
            po.button_cancel()

            # # Update Sales Order line
            # po.sale_order_line_id.write({
            #     'service_status': 'refused'
            # })
            #
            # # Update Service
            # service.write({
            #     'status': 'refused'})

            res['code'] = 1

        return res

    @api.model
    def update_po_prepay(self, name, cus_code1, cus_code2, cus_code3, result, vendor_code, ip_hosting, ip_email, start_date, end_date, vals={}):
        res = {'code': 0, 'msg': ''}
        ResPartner = self.env['res.partner']
        PurchaseOrder = self.env['purchase.order']
        SaleService = self.env['sale.service']
        ProductProduct = self.env['product.product']
        PurchaseOrderLine = self.env['purchase.order.line']
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        AccountTax = self.env['account.tax']
        AccountAccount = self.env['account.account']
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line']
        # Validate data before process
        if not name:
            res['msg'] = "Purchase order name could not be empty"
            return res
        po = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po:
            res['msg'] = "Purchase order '{}' is not found".format(name)
            return res
        elif po.state != 'draft':
            res['msg'] = \
                "Status of Purchase Order '{}' must be draft".format(name)
            return res
        if not result:
            res['msg'] = "Fail to register"
        if not vendor_code:
            res['msg'] = "Vendor code could not be empty"
            return res
        vendor = ResPartner.search([('ref', '=', vendor_code), ('supplier', '=', True)], limit=1)
        if not vendor:
            res['msg'] = "Vendor '{}' is not found".format(vendor_code)
            return res
        if not start_date:
            res['msg'] = "Start date could not be empty"
            return res
        if not end_date:
            res['msg'] = "End date could not be empty"
            return res
        try:
            system_start_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, start_date)
        except ValueError:
            res['msg'] = 'Wrong start date format'
            return res
        try:
            system_end_date = self.env[
                'ir.fields.converter']._str_to_date(
                None, None, end_date)
        except ValueError:
            res['msg'] = 'Wrong end date format'
            return res

        if not po.sale_order_line_id:
            res['msg'] = 'Purchase order does not have related sale order line'
            return res
        # service = SaleService.search([('sales_order_ids', 'in', po.sale_order_line_id and po.sale_order_line_id.order_id.id)], limit=1)
        service = SaleService.search([('product_id', '=', po.order_line and po.order_line.mapped('product_id') and
                                       po.order_line.mapped('product_id')[0].id)], limit=1)
        if not service:
            res['msg'] = \
                "Service of purchase order '{}' is not found".format(name)
            return res
        # if not vals.get('price_unit'):
        #     res['msg'] = "Vals %s does not have price unit" % vals
        #     return res

        tax_id = False
        if 'tax' in vals:
            tax_id = AccountTax.search([
                ('amount', '=', float(vals['tax']))], limit=1)
            if not tax_id:
                res['msg'] = "### Can't find Tax"
                return res
        if vals.get('poline_id'):
            po_line = PurchaseOrderLine.browse(vals['poline_id'])
            if not po_line:
                res['msg'] = "Purchase order line '{}' is not found".format(
                    vals['poline_id'])
                return res
        else:
            if not vals.get('product_code'):
                res['msg'] = "Vals does not have product code"
                return res
            if not vals.get('product_name'):
                res['msg'] = "Vals does not have product name"
                return res
            product_code = self._convert_str(vals['product_code'])
            product_name = self._convert_str(vals['product_name'])
            product = ProductProduct.search(
                [('name', '=', product_name),
                 ('default_code', '=', product_code)])
            if not product:
                res['msg'] = \
                    "Product with name and code is not found"
                return res
            po_line = PurchaseOrderLine.search(
                [('product_id', '=', product.id),
                 ('order_id', '=', po.id)], limit=1)
            if not po_line:
                res['msg'] = \
                    "Purchase order line of given product is not found"
                return res
        if result:
            if not cus_code1 or not cus_code2 or not cus_code3:
                res['msg'] = "Customer 1, Customer 2 and Customer 3 could be not empty"
                return res
            cus1_id = ResPartner.search([('ref', '=', cus_code1)])
            if not cus1_id:
                res['msg'] = "Customer 1 not exists"
                return res
            cus2_id = ResPartner.search([('ref', '=', cus_code2)])
            if not cus2_id:
                res['msg'] = "Customer 2 not exists"
                return res
            cus3_id = ResPartner.search([('ref', '=', cus_code3)])
            if not cus3_id:
                res['msg'] = "Customer 3 not exists"
                return res
            # Confirm Purchase Order
            po.partner_id = vendor
            po_line.write({
                'taxes_id': [(6, 0, tax_id and [tax_id.id] or [])]
            })
            po_line._compute_amount()
            po._amount_all()
            po.button_confirm()
            po.button_done()

            # Update Sales Order line
            po.sale_order_line_id.write({
                'service_status': 'done'
            })
            po.write({
                'partner_id': cus2_id.id
            })
            if vals.get('price_unit', 0) > 0 or vals.get('price_unit1',0) > 0:
                # ===================================== Create Vendor Bill 1 ======================================#
                data = po.action_view_invoice()
                if 'default_journal_id' in data['context']:
                    data['context'].pop('default_journal_id')
                fields = [field for field in AccountInvoice._fields]
                default_bill_vals = AccountInvoice.with_context(
                    data['context']).default_get(fields)

                vendor_bill = AccountInvoice.new(default_bill_vals)
                vendor_bill.purchase_id = data['context']['default_purchase_id']
                vendor_bill.purchase_order_change()
                bill_vals = AccountInvoice._convert_to_write(vendor_bill._cache)
                domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', po.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                bill_vals.update({
                    'purchase_id': data['context']['default_purchase_id'],
                    'origin': po.name,
                })
                bill_vals1 = dict(bill_vals)

                line_vals = bill_vals.get('invoice_line_ids')
                if vals.get('price_unit', 0) > 0:
                    try:
                        vendor_bill = AccountInvoice.with_context(force_company=po.company_id.id).create(bill_vals)

                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (register) for %s." % cus2_id.name
                        return res
                    vendor_bill.write({
                        'partner_id': cus2_id.id,
                        'company_id': po.company_id.id,
                        'journal_id': journal_id.id,
                        'account_id': cus1_id.property_account_payable_id and cus1_id.with_context(force_company=po.company_id.id).property_account_payable_id.id,
                    })
                    vendor_bill.invoice_line_ids.write(
                        {'price_unit': vals['price_unit'],
                         'quantity': po_line.register_type == 'renew' and po_line.product_qty or 1,
                         'register_type': po_line.register_type})
                    for line in vendor_bill.invoice_line_ids:
                        account = AccountInvoiceLine.with_context(force_company=po.company_id.id).get_account_id(line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                        # fpos = vendor_bill.with_context(force_company=po.company_id.id).fiscal_position_id
                        # account = line.get_invoice_line_account('in_invoice', line.product_id.with_context(force_company=po.company_id.id), fpos, cus1_id.company_id)
                        if account:
                            line.write({
                                'account_id': type(account).__name__ == 'int' and account or account.id
                            })
                        analytic = AccountInvoiceLine.with_context(force_company=po.company_id.id).get_account_analytic_id(
                            line.product_id, 'in_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })
                    vendor_bill.with_context(force_company=po.company_id.id).compute_taxes()
                    try:
                        vendor_bill.with_context(force_company=po.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill (register) can't validate."

                        return res
                    if vendor_bill.move_id:
                        for line in vendor_bill.move_id.line_ids:
                            if line.credit > 0:
                                line.partner_id = cus2_id.id
                            if line.debit > 0:
                                line.partner_id = False
                    # Match Payments
                    payment_vals = json.loads(vendor_bill.with_context(force_company=po.company_id.id).outstanding_credits_debits_widget)
                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill.has_outstanding or float_compare(paid_amount, vendor_bill.amount_total, precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill 1 cannot be reconciled"

                        return res
                    else:
                        balance_amount = vendor_bill.amount_total
                        for line in payment_vals['content']:
                            if float_compare(balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break
                            vendor_bill.with_context(force_company=po.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

                if vals.get('price_unit1', 0) > 0:
                    _logger.info('YYYYYYYYYYYYYYYYYY111111111111111YYYYYYYYYYYYYYYYY')
                    vendor_bill1 = AccountInvoice.new(default_bill_vals)
                    vendor_bill1.purchase_id = data['context']['default_purchase_id']
                    vendor_bill1.purchase_order_change()
                    _logger.info('YYYYYYYYYYYYYYYYYY22222222222222227777777777777777772222222YYYYYYYYYYYYYYYYY' )
                    try:


                        _logger.info('YYYYYYYYYYYYYYYYYY2222222222222222yyyyyyyyyyyyyyyyy2222222YYYYYYYYYYYYYYYYY' )
                        _logger.info('YYYYYYYYYYYYYYYYYY2222222222222999999999999992222222222YYYYYYYYYYYYYYYYY %s ' % bill_vals1 )
                        vendor_bill1 = AccountInvoice.with_context(force_company=po.company_id.id).create(bill_vals1)
                    except:
                        _logger.info('YYYYYYYYYYYYYYYYYY222222222222223333333333333222222222YYYYYYYYYYYYYYYYY %s ' % bill_vals1 )
                        _logger.info('YYYYYYYYYYYYYYYYYY22222222222222222222222YYYYYYYYYYYYYYYYY %s ' % po.company_id.id)
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (renew)."
                        return res

                    vendor_bill1.write({
                        'partner_id': cus2_id.id,
                        'company_id': po.company_id.id,
                        'journal_id': journal_id.id,
                        'account_id': cus1_id.property_account_payable_id and cus1_id.with_context(force_company=po.company_id.id).property_account_payable_id.id,
                    })
                    vendor_bill1.invoice_line_ids.write(
                        {'price_unit': vals['price_unit1'],
                         # 'quantity': 1,
                         'partner_id': cus2_id.id,
                         'register_type': 'renew'})
                    for line in vendor_bill1.invoice_line_ids:
                        account = AccountInvoiceLine.with_context(force_company=po.company_id.id).get_account_id(
                            line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                        if account:
                            line.write({
                                'account_id': type(account).__name__ == 'int' and account or account.id
                            })
                        analytic = AccountInvoiceLine.with_context(force_company=po.company_id.id).get_account_analytic_id(
                            line.product_id, 'in_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })

                    vendor_bill1.with_context(force_company=po.company_id.id).compute_taxes()
                    try:

                        vendor_bill1.with_context(force_company=po.company_id.id).action_invoice_open()

                    except:
                        _logger.info('8888888888888888888888888888 %s ' % po.company_id.id)
                        self._cr.rollback()
                        res['msg'] = "Can't validate Vendor Bill (renew) 1"

                        return res
                    if vendor_bill1.move_id:
                        for line in vendor_bill1.move_id.line_ids:
                            if line.credit > 0:
                                line.partner_id = cus2_id.id
                            if line.debit > 0:
                                line.partner_id = False
                    # Match Payments
                    payment_vals = json.loads(vendor_bill1.with_context(force_company=po.company_id.id).outstanding_credits_debits_widget)
                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill1.has_outstanding or float_compare(paid_amount, vendor_bill1.amount_total, precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill 1 (renew) cannot be reconciled"
                        return res
                    else:
                        balance_amount = vendor_bill1.amount_total
                        for line in payment_vals['content']:
                            if float_compare(balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break
                            vendor_bill1.with_context(force_company=po.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

                # ==================================== Create Customer Invoice ==================================#
                default_invoice_vals = AccountInvoice.default_get(fields)
                customer_invoice = AccountInvoice.new(default_invoice_vals)
                cus_vals = AccountInvoice._convert_to_write(customer_invoice._cache)
                domain = [
                    ('type', '=', 'sale'),
                    ('company_id', '=', cus2_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                cus_vals.update({
                    'partner_id': cus1_id.id,
                })
                try:
                    customer_invoice = AccountInvoice.with_context(force_company=cus2_id.company_id.id).create(cus_vals)
                    customer_invoice.write({
                        'journal_id': journal_id.id,
                        'account_id': cus2_id.property_account_receivable_id and cus2_id.with_context(force_company=cus2_id.company_id.id).property_account_receivable_id.id,
                        'company_id': cus2_id.company_id.id
                    })
                    cus_line_vals = []
                    if line_vals:
                        if vals.get('price_unit', 0) > 0 and line_vals[1]:
                            cus_line_vals.append(line_vals[1])
                        if vals.get('price_unit1', 0) > 0 and line_vals[1]:
                            cus_line_vals.append(line_vals[1])
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).write({
                        'invoice_line_ids': cus_line_vals
                    })
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).invoice_line_ids.write({
                        'price_unit': vals['price_unit'],
                        'company_id': cus2_id.company_id.id,
                        'quantity': 1,
                        'time': po_line.register_type == 'renew' and po_line.product_qty or 1,
                        'register_type': po_line.register_type,
                        'purchase_line_id': False
                     })
                    if vals.get('price_unit1', 0) > 0 and customer_invoice.invoice_line_ids:
                        for line in customer_invoice.invoice_line_ids:
                            if line == customer_invoice.invoice_line_ids[-1]:
                                line.write({
                                    'register_type': 'renew',
                                    'price_unit': vals.get('price_unit1'),
                                    'time': po_line.product_qty,
                                    'quantity': po_line.product_qty
                                })
                            else:
                                line.write({
                                    'register_type': po_line.register_type,
                                    'time': po_line.register_type == 'renew' and po_line.product_qty or 1
                                })

                    for line in customer_invoice.invoice_line_ids:
                        account_id = AccountInvoiceLine.with_context(force_company=cus2_id.company_id.id).get_account_id(
                            line.product_id, 'out_invoice', line.register_type, line.invoice_line_tax_ids)
                        if account_id:
                            line.write({
                                'account_id': type(account_id).__name__ == 'int' and account_id or account_id.id
                            })

                        analytic = AccountInvoiceLine.with_context(force_company=cus2_id.company_id.id).get_account_analytic_id(
                            line.product_id, 'out_invoice', line.register_type)
                        if analytic:
                            line.write({
                                'account_analytic_id': analytic
                            })
                except:
                    self._cr.rollback()
                    res['msg'] = "Can't create Customer Invoice"
                    return res
                try:
                    customer_invoice.with_context(force_company=cus2_id.company_id.id).action_invoice_open()
                except:
                    self._cr.rollback()
                    res['msg'] = "Customer Invoice can't validate."

                    return res
                # Match Payments
                payment_vals = json.loads(customer_invoice.with_context(force_company=cus2_id.company_id.id).outstanding_credits_debits_widget)
                paid_amount = 0.0
                if payment_vals and payment_vals.get('content'):
                    for line in payment_vals['content']:
                        paid_amount += line['amount']

                if not customer_invoice.has_outstanding or float_compare(paid_amount, customer_invoice.amount_total, precision_digits=2) < 0:
                    self._cr.rollback()
                    res['msg'] = "Customer Invoice cannot be reconciled"
                    return res
                else:
                    balance_amount = customer_invoice.amount_total
                    for line in payment_vals['content']:
                        if float_compare(balance_amount, 0, precision_digits=2) <= 0:
                            # fully paid
                            break
                        customer_invoice.with_context(force_company=cus2_id.company_id.id).assign_outstanding_credit(line['id'])
                        balance_amount -= line['amount']

                # ====================================== Create Vendor Bill 2 =======================================#
                default_vendor_vals_ncc = AccountInvoice.with_context(type='in_invoice', journal_type='purchase').default_get(fields)
                vendor_bill_ncc = AccountInvoice.new(default_vendor_vals_ncc)
                bill_vals_ncc = AccountInvoice._convert_to_write(vendor_bill_ncc._cache)
                domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', cus3_id.company_id.id),
                ]
                journal_id = self.env['account.journal'].search(domain, limit=1)
                bill_vals_ncc.update({
                    'partner_id': cus3_id.id,
                })
                bill_vals1_ncc = dict(bill_vals_ncc)
                if vals.get('price_unit', 0) > 0:
                    try:

                        vendor_bill_ncc = AccountInvoice.with_context(force_company=cus3_id.company_id.id).create(bill_vals_ncc)

                        vendor_bill_ncc.write({
                            'journal_id': journal_id.id,
                            'account_id': cus3_id.property_account_payable_id and cus3_id.with_context(
                                force_company=cus3_id.company_id.id).property_account_payable_id.id,
                            'company_id': cus3_id.company_id.id
                        })
                        vendor_bill_ncc.write({
                            'invoice_line_ids': line_vals
                        })
                        vendor_bill_ncc.invoice_line_ids.write({
                            'price_unit': vals['price_unit'],
                            'company_id': cus3_id.company_id.id,
                            'register_type': po_line.register_type,
                            'quantity': po_line.register_type == 'renew' and po_line.product_qty or 1,
                            'purchase_line_id': False
                        })
                        for line in vendor_bill_ncc.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })

                            analytic = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_analytic_id(
                                line.product_id, 'in_invoice', line.register_type)
                            if analytic:
                                line.write({
                                    'account_analytic_id': analytic
                                })

                        vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).compute_taxes()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill for Vendor"
                        return res
                    try:
                        vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Vendor Bill (register) for %s can't validate." % cus3_id.name
                        return res
                    # Match Payments
                    payment_vals = json.loads(
                        vendor_bill_ncc.with_context(
                            force_company=cus3_id.company_id.id).outstanding_credits_debits_widget)

                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill_ncc.has_outstanding or \
                                    float_compare(paid_amount, vendor_bill_ncc.amount_total,
                                                  precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = \
                            "Vendor Bill cannot be reconciled"

                        return res
                    else:
                        balance_amount = vendor_bill_ncc.amount_total
                        for line in payment_vals['content']:
                            if float_compare(
                                    balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break

                            vendor_bill_ncc.with_context(force_company=cus3_id.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

                if vals.get('price_unit1', 0) > 0:
                    try:

                        vendor_bill1_ncc = AccountInvoice.with_context(force_company=cus3_id.company_id.id).create(bill_vals1_ncc)
                        vendor_bill1_ncc.write({
                            'partner_id': cus3_id.id,
                            'company_id': cus3_id.company_id.id,
                            'journal_id': journal_id.id,
                            'account_id': cus3_id.property_account_payable_id and cus3_id.with_context(force_company=cus3_id.company_id.id).property_account_payable_id.id,
                        })
                        vendor_bill1_ncc.write({
                            'invoice_line_ids': line_vals
                        })
                        vendor_bill1_ncc.invoice_line_ids.write({
                            'price_unit': vals['price_unit1'],
                            'partner_id': cus3_id.id,
                            'register_type': 'renew',
                            'purchase_line_id': False
                        })
                        for line in vendor_bill1_ncc.invoice_line_ids:
                            account = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_id(
                                line.product_id, 'in_invoice', line.register_type, line.invoice_line_tax_ids)
                            if account:
                                line.write({
                                    'account_id': type(account).__name__ == 'int' and account or account.id
                                })

                            analytic = AccountInvoiceLine.with_context(force_company=cus3_id.company_id.id).get_account_analytic_id(
                                line.product_id, 'in_invoice', line.register_type)
                            if analytic:
                                line.write({
                                    'account_analytic_id': analytic
                                })

                        vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).compute_taxes()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't create Vendor Bill (renew) for Vendor."
                        return res
                    try:
                        vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).action_invoice_open()
                    except:
                        self._cr.rollback()
                        res['msg'] = "Can't validate Vendor Bill (renew) for Vendor."
                        return res
                    # Match Payment
                    payment_vals = json.loads(
                        vendor_bill1_ncc.with_context(
                            force_company=cus3_id.company_id.id).outstanding_credits_debits_widget)
                    paid_amount = 0.0
                    if payment_vals and payment_vals.get('content'):
                        for line in payment_vals['content']:
                            paid_amount += line['amount']

                    if not vendor_bill1_ncc.has_outstanding or \
                                    float_compare(paid_amount, vendor_bill1_ncc.amount_total,
                                                  precision_digits=2) < 0:
                        self._cr.rollback()
                        res['msg'] = \
                            "Vendor Bill cannot be reconciled"
                        return res
                    else:
                        balance_amount = vendor_bill1_ncc.amount_total
                        for line in payment_vals['content']:
                            if float_compare(
                                    balance_amount, 0, precision_digits=2) <= 0:
                                # fully paid
                                break

                            vendor_bill1_ncc.with_context(force_company=cus3_id.company_id.id).assign_outstanding_credit(line['id'])
                            balance_amount -= line['amount']

            # Update PO
            po.write({
                'is_success': True
            })
            # Update Service
            service.write({
                            # 'start_date': system_start_date[0],
                           # 'end_date': system_end_date[0],
                           'ip_hosting': ip_hosting,
                           'ip_email': ip_email,
                           'status': 'active'})

            res['code'] = 1
        else:
            # cancel purchase order
            po.button_cancel()

            # # Update Sales Order line
            # po.sale_order_line_id.write({
            #     'service_status': 'refused'
            # })
            #
            # # Update Service
            # service.write({
            #     'status': 'refused'})

            res['code'] = 1

        return res

    @api.model
    def update_field_po(self, po_name, vals={}):
        res = {'"code"': 0, '"msg"': '""'}
        PurchaseOrder = self.env['purchase.order']

        # Check type of data
        if not po_name:
            return {'"msg"': '"PO name could not be empty"'}
        po_id = PurchaseOrder.search([('name', '=', po_name)], limit=1)
        if not po_id:
            return {'"msg"': '"PO name not found!"'}
        if not vals:
            return {'"msg"': '"Vals could not be empty"'}
        if type(vals) is not dict:
            return {'"msg"': '"Invalid ValsEntity"'}
        args = {}
        if vals.get('retry_count'):
            if type(vals.get('retry_count')) is not int or  vals.get('retry_count') < 0:
                return {'"msg"': '"Retry must be number and larger or equal 0"'}
            args.update({'retry_count': vals.get('retry_count')})
        if 'is_success' in vals:
            if vals.get('is_success') not in (1,0):
                return {'"msg"': '"Is Sucess must be in 0 or 1"'}
            args.update({'is_success': vals.get('is_success') == 1 and True or False})
        if vals.get('partner_id'):
            partner_id = self.env['res.partner'].search([('ref', '=', vals.get('partner_id'))], limit=1)
            if not partner_id:
                return {'"msg"': '"Partner not found"'}
            args.update({'partner_id': partner_id})
        if args:
            po_id.update(args)
            res['"code"'] = 1
        else:
            return {'"msg"': '"Can`t update PO"'}
        return res

    @api.model
    def update_po_error(self, name, body):
        res = {'code': 0, 'msg': ''}
        PurchaseOrder = self.env['purchase.order']
        # Check type of data
        if not name:
            return {'msg': 'PO name could not be empty'}
        po_id = PurchaseOrder.search([('name', '=', name)], limit=1)
        if not po_id:
            return {'msg': 'PO name not found!"'}
        # if not body:
        #     return {'msg': ' could not be empty'}
        try:
            po_id.write({'is_error': True})
            po_id.message_post(body=body or 'No content return', subtype="mt_comment")
            res['msg'] = "Update Successfully"
        except:
            return {'msg': "Can't update PO."}
        res['code'] = 1
        return res

    @api.model
    def get_po_no_process(self, limit=1000, date_from='', date_to='', order='date_order'):
        """
            TO DO:
            - Get Purchase  Order from Odoo by state
        """
        res = {'code': 0, 'msg': 'Process PO Successful!', 'data': []}
        PurchaseOrder = self.env['purchase.order']
        error_msg = ''
        args = []
        # Check date from
        if date_from:
            try:
                system_date_from = self.env['ir.fields.converter']._str_to_datetime(None, None, str(date_from))
                args += [('date_order', '>=', system_date_from[0])]
            except ValueError:
                error_msg += 'Wrong DATE FROM format, '

        # Check Date to
        if date_to:
            try:
                system_date_to = self.env['ir.fields.converter']._str_to_datetime(None, None, str(date_to))
                args += [('date_order', '<=', system_date_to[0])]
            except ValueError:
                error_msg += 'Wrong DATE TO format, '

        # Check limit argument
        try:
            if limit:
                if not isinstance(limit, int) or int(limit) < 1:
                    error_msg += 'Invalid limit'
        except ValueError:
            error_msg += 'Invalid limit'

        # Return error
        if error_msg:
            res.update({'msg': error_msg})
            return res

        categ_chili = self.env['product.category'].search([('code', '=', 'CHILI')])
        if categ_chili:
            categ_chili = self.env['product.category'].search([('id', 'child_of', categ_chili.ids)])
            args += [('is_error', '=', False), ('retry_count', '=', 0), ('is_active', '=', False), ('product_category_id', 'not in', categ_chili.ids)]
        else:
            args += [('is_error', '=', False), ('retry_count', '=', 0), ('is_active', '=', False)]
        # If arguments are ok
        try:
            po_recs = PurchaseOrder.search(args, limit=limit, order=order)
            if not po_recs:
                res.update({'code': 1, 'msg': '', 'data': []})
                return res

            # Parse data
            data = []
            for po in po_recs:
                data_append = ['name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"',
                               'state: ' + '\"' + po.state + '\"',
                               'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                               'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                               'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                               'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                               'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""]
                po_line_append = {}
                for line in po.order_line:
                    service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                    start_date = service_id and service_id[0].start_date or datetime.now().date().strftime('%Y-%m-%d')
                    end_date = service_id and service_id[0].end_date or datetime.now().date().strftime('%Y-%m-%d')
                    po_line_append['poline_id'] = '\"' + str(line.id) + '\"'
                    po_line_append['product_code'] = '\"' + (line.product_id.default_code or '') + '\"'
                    po_line_append['product_name'] = '\"' + (line.product_id.name or '') + '\"'
                    po_line_append['qty'] = '\"' + str(int(line.product_qty)) + '\"'
                    po_line_append['uom'] = '\"' + (line.product_uom.name or '') + '\"'
                    po_line_append['register_type'] = '\"' + (line.register_type or '') + '\"'
                    po_line_append['category_code'] = '\"' + (line.product_id.categ_id.code or '') + '\"'
                    po_line_append['start_date'] = '\"' + start_date + '\"'
                    po_line_append['end_date'] = '\"' + end_date + '\"'
                    po_line_append['company_id'] = '\"' + (
                    line.company_id and str(line.company_id.id) or '0') + '\"'
                    po_line_append['template'] = '\"' + (line.template or '') + '\"'
                    po_line_append['service_code'] = '\"' + (service_id and service_id.reference or '') + '\"'
                    po_line_append['customer_code'] = '\"' + (
                    service_id and service_id.customer_id.ref or '') + '\"'
                    po_line_append['company_type'] = '\"' + (
                    service_id and service_id.customer_id.company_type or '') + '\"'
                    data_append.append([po_line_append])
                data.append(data_append)
            res.update({'code': 1, 'msg': "''", 'data': data})
        except UserError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except ValueError, e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except:
            error_msg += 'Unknow Error, '
            res['msg'] = error_msg
            return res
        return res
