# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

class ExternalPO(models.AbstractModel):
    _inherit = 'external.po'


    def get_data_line(self,line,tenant_id):
        res={}
        service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)], limit=1)
        if len(service_id) > 1:
            return False
        for i_service in service_id:
            res = i_service.read(['reference', 'name'])[0]
        line_data = line.read(['id', 'qty', 'register_type', 'template'])

        res.update(line_data[0])


        res.update({
            'subscription_id':i_service.subscription_id or None,
            'start_date':i_service.start_date or None,
            'end_date':i_service.end_date or None,
            'product_code': line.product_id.default_code or None,
            'product_name': line.product_id.name or None,
            'uom': line.product_uom and line.product_uom.name or None,
            'category_code': line.product_id.categ_id.code or None,
            'category_name': line.product_id.categ_id.name or None,
            'is_addons': line.product_id.categ_id and line.product_id.categ_id.is_addons or False,
            'company_id': line.company_id and line.company_id.id or None,
            'customer_code': service_id.customer_id.ref,
            'customer_type': service_id.customer_id.company_type,
            'tenant_id':tenant_id
        })
        return res

    def get_data_po(self,po,service):
        res = {}
        po_data = po.read(['name', 'state'])
        res.update({
            'date_order': po.date_order or None,
            'sale_order_line_id': po.sale_order_line_id and po.sale_order_line_id.id or None,
            'dns': po.sale_order_line_id and po.sale_order_line_id.dns or None,
            'os_template': po.sale_order_line_id and po.sale_order_line_id.os_template or None,
            'SO': po.sale_order_line_id and po.sale_order_line_id.order_id.name or None,
            'customer_type': po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or None,
            'source': po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or None,
            'is_success': po.is_success or False,
            'verify': service and service.reseller_id and service.reseller_id.verify or False
        })

        res.update(po_data[0])

        po_order_line = []
        for line in po.order_line:
            data_line = self.get_data_line(line, (po.partner_id.microsoft_customer_id or None))
            if data_line:
                po_order_line.append(data_line)
        res.update({'dataline': po_order_line})
        return res

    @api.model
    def get_po_by_state_new(self, type, is_active, state=False, register_type=False, date_from=False,
                        date_to=False, limit=None, order='date_order'):
        code=200
        messages = 'Successful'
        data= []

        args = [('product_id.categ_id.manual_active', '=', False)]

        # Check Type
        if not type and type not in (1, 2, 3):
            messages='Type could not empty and must be in 1,2,3'


        # Check Is Active
        if not is_active and is_active not in (0, 1):
            messages='Type could not empty and must be in 0 or 1'

        if is_active == 0:
            args += [('is_active', '=', False)]
        else:
            args += [('is_active', '=', True)]

        # Check state
        invalid_states = ['draft', 'sent', 'to approve', 'purchase', 'done', 'cancel']
        if state and state not in invalid_states:
            messages = 'Invalid state, '
        if state:
            args += [('state', '=', state)]

        # Check Register Type
        if register_type and register_type not in ('register', 'renew', 'transfer', 'upgrade'):
            messages= 'Type could not empty and must be in `register`, `renew`, `upgrade` and `transfer`'

        # Check date from
        if date_from:
            try:
                system_date_from = self.env['ir.fields.converter']._str_to_datetime(None, None, str(date_from))
                args += [('date_order', '>=', system_date_from[0])]
            except ValueError:
                messages= 'Wrong DATE FROM format, '

        # Check Date to
        if date_to:
            try:
                system_date_to = self.env['ir.fields.converter']._str_to_datetime(None, None, str(date_to))
                args += [('date_order', '<=', system_date_to[0])]
            except ValueError:
                messages= 'Wrong DATE TO format, '

        # Check limit argument
        try:
            if limit:
                if not isinstance(limit, int) or int(limit) < 1:
                    messages= 'Invalid limit'
        except ValueError:
            messages= 'Invalid limit'

        # Return error
        if messages !='Successful':
            res = {'code': 502, 'messages': messages, 'data': data}
            return json.dumps(res)

        args += [('is_error', '!=', True), '|', ('retry_count', '=', 0), ('retry_count', '=', False)]
        try:
            po_recs = self.env['purchase.order'].search(args, limit=limit, order=order)
            # Parse data
            for po in po_recs:
                service = self.env['sale.service'].search([('product_id', '=', po.product_id.id)], limit=1)
                # Check domain .vn
                if type == 1:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(line.register_type == register_type for line in po.mapped('order_line'))) \
                            and categs and any(c.code and c.code.strip()[:1] == '.' and (c.code.strip()[-3:] == '.vn' or c.code.strip()[-5:] == '.tmtv') for c in categs):
                        data.append(self.get_data_po(po,service))
                # Check domain QT
                elif type == 2:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(
                            line.register_type == register_type for line in po.mapped('order_line'))) \
                            and categs and any(c.code and c.code.strip()[:1] == '.' and c.code.strip()[-3:] != '.vn' and c.code.strip()[-5:] != '.tmtv' for c in categs):
                        data.append(self.get_data_po(po,service))
                # Check hosting
                else:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(
                            line.register_type == register_type for line in po.mapped('order_line'))) and \
                            categs and any(c.code and c.code.strip()[:1] != '.' for c in categs):
                        data.append(self.get_data_po(po,service))

        except UserError as e:
            messages= e[0]
            code=402
        except ValueError as e:
            messages = e[0]
            code = 402
        except:
            messages = 'Unknown Error, '
            code = 402

        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)


    @api.model
    def get_po_by_state(self, type, is_active, state=False, register_type=False, date_from=False,
                        date_to=False, limit=None, order='date_order'):
        res = {'code': 0, 'msg': 'Process PO Successful!', 'data': []}
        error_msg = ''
        args = [('product_id.categ_id.manual_active', '=', False)]

        # Check Type
        if not type and type not in (1, 2, 3):
            res.update({'code': 0, 'msg': 'Type could not empty and must be in 1,2,3'})
            return res

        # Check Is Active
        if not is_active and is_active not in (0, 1):
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
            res.update(
                {'code': 0, 'msg': 'Type could not empty and must be in `register`, `renew`, `upgrade` and `transfer`'})
            return res

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

        args += [('is_error', '!=', True), '|', ('retry_count', '=', 0), ('retry_count', '=', False)]
        try:
            po_recs = self.env['purchase.order'].search(args, limit=limit, order=order)
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
                        data_append = [
                            'name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"',
                            'state: ' + '\"' + po.state + '\"',
                            'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                            'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                            'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                            'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                            'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                            'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                            'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                            'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                            'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""
                        ]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) > 1:
                                continue
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
                            po_line_append['subscription_id'] = '\"' + (service_id and service_id.subscription_id or '') + '\"'
                            po_line_append['tenant_id'] = '\"' + (po.partner_id.microsoft_customer_id or '') + '\"'
                            data_append.append([po_line_append])
                        data.append(data_append)
                # Check domain QT
                elif type == 2:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(
                            line.register_type == register_type for line in po.mapped('order_line'))) \
                            and categs and any(c.code and c.code.strip()[:1] == '.' and c.code.strip()[-3:] != '.vn' and c.code.strip()[-5:] != '.tmtv' for c in categs):
                        data_append = [
                            'name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"',
                            'state: ' + '\"' + po.state + '\"',
                            'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                            'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                            'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                            'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                            'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                            'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                            'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                            'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                            'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""
                        ]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) > 1:
                                continue
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
                            po_line_append['subscription_id'] = '\"' + (service_id and service_id.subscription_id or '') + '\"'
                            po_line_append['tenant_id'] = '\"' + (po.partner_id.microsoft_customer_id or '') + '\"'
                            data_append.append([po_line_append])
                        data.append(data_append)
                # Check hosting
                else:
                    categs = po.mapped('order_line').mapped('product_category_id')
                    if (not register_type or any(
                            line.register_type == register_type for line in po.mapped('order_line'))) and \
                            categs and any(c.code and c.code.strip()[:1] != '.' for c in categs):
                        data_append = [
                            'name: ' + '\"' + po.name + '\"', 'date_order: ' + '\"' + po.date_order + '\"',
                            'state: ' + '\"' + po.state + '\"',
                            'sale_order_line_id: ' + '\"' + (po.sale_order_line_id and str(po.sale_order_line_id.id) or '') + '\"',
                            'dns: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.dns or '') + '\"',
                            'os_template: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.os_template or '') + '\"',
                            'SO: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.name or '') + '\"',
                            'customer_type: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id and po.sale_order_line_id.order_id.partner_id.company_type or '') + '\"',
                            'source: ' + '\"' + (po.sale_order_line_id and po.sale_order_line_id.order_id.source_id and po.sale_order_line_id.order_id.source_id.name or '') + '\"',
                            'is_success: ' + '\"' + (po.is_success and 'True' or 'False') + "\"",
                            'verify: ' + '\"' + (service and service.reseller_id and service.reseller_id.verify and 'True' or 'False') + "\"",
                            'is_active: ' + '\"' + (po.is_active and 'True' or 'False') + "\""
                        ]
                        po_line_append = {}
                        for line in po.order_line:
                            service_id = self.env['sale.service'].search([('product_id', '=', line.product_id.id)])
                            if len(service_id) > 1:
                                continue
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
                            po_line_append['subscription_id'] = '\"' + (service_id and service_id.subscription_id or '') + '\"'
                            po_line_append['tenant_id'] = '\"' + (po.partner_id.microsoft_customer_id or '') + '\"'
                            data_append.append([po_line_append])
                        data.append(data_append)
            res.update({'code': 1, 'msg': "''", 'data': data})
        except UserError as e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except ValueError as e:
            error_msg += e[0]
            res['msg'] = error_msg
            return res
        except:
            error_msg += 'Unknown Error, '
            res['msg'] = error_msg
            return res
        return res
