# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger
from datetime import datetime

class SaleService(models.Model):
    _inherit = 'sale.service'

    id_domain_floor = fields.Char('ID Domain Floor')
    is_active = fields.Boolean("Is Active", default=False)

    @api.model
    def update_id_domain_floor(self, service, id):
        if not id:
            return {'"code"': 0, '"msg"': '"ID could be not empty."'}
        if not service:
            return {'"code"': 0, '"msg"': '"Service could be not empty."'}
        service_id = self.env['sale.service'].search([('reference', '=', service)])
        if not service_id:
            return {'"code"': 0, '"msg"': '"Service not found."'}
        if len(service_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s services with code %s"' % (len(service_id), service)}
        try:
            service_id.id_domain_floor = id
            return {'"code"': 1, '"msg"': '"Updated Successfully."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Update error: %s"' % (e.message or repr(e))}

    @api.model
    def update_active_service(self, service, is_active=1, domain=''):
        _logger.info("****************** %s, %s ********************", is_active, type(is_active))
        if is_active != 0 and is_active != 1:
            return {'"code"': 0, '"msg"': '"Active could be not empty and Active must be 0 or 1."'}
        if not domain:
            return {'"code"': 0, '"msg"': '"Domain could be not empty."'}
        if not service:
            return {'"code"': 0, '"msg"': '"Service could be not empty."'}
        service_id = self.env['sale.service'].search([('reference', '=', service)])
        if not service_id:
            return {'"code"': 0, '"msg"': '"Service not found."'}
        if len(service_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s services with code %s"' % (len(service_id), service)}
        try:
            service_id.write({
                'is_active': True if is_active == 1 else False,
                'name': ' - '.join([service_id.reference or '', domain])
            })
            service_id.product_id.name = domain
            return {'"code"': 1, '"msg"': '"Updated Successfully."'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Update error: %s"' % (e.message or repr(e))}

    @api.model
    def get_service_to_register_addons(self, customer_code):
        if not customer_code:
            return {'"code"': 0, '"msg"': '"Customer Code could be not empty"'}
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code), ('customer', '=', True)])
        if not customer_id:
            return {'"code"': 0, '"msg"': '"Customer not found"'}
        if len(customer_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s customer with code %s"' % (len(customer_id), customer_code)}
        service_ids = self.env['sale.service'].search([('customer_id', '=', customer_id.id), ('status', '=', 'active')])
        data = []
        try:
            for service in service_ids:
                data.append({
                    '"name"': '"%s"' % service.name,
                    '"reference"': '"%s"' % (service.reference or ''),
                    '"product_name"': '"%s"'% (service.product_id and service.product_id.name or ''),
                    '"product_code"': '"%s"'% (service.product_id and service.product_id.default_code or ''),
                    '"product_id"': service.product_id and service.product_id.id or 0,
                    '"product_category_id"': service.product_category_id and service.product_category_id.id or 0,
                    '"product_category_code"': '"%s"' % (service.product_category_id and service.product_category_id.code or ''),
                    '"product_category_erm_code"': '"%s"' % (service.product_category_id and service.product_category_id.erm_code or ''),
                    '"product_category_name"': '"%s"' % (service.product_category_id and service.product_category_id.name or ''),
                    '"parent_product_category_id"': service.product_category_id and service.product_category_id.parent_id and service.product_category_id.parent_id.id or 0,
                    '"parent_product_category_code"': '"%s"' % (service.product_category_id and service.product_category_id.parent_id and service.product_category_id.parent_id.code or ''),
                    '"parent_product_category_erm_code"': '"%s"' % (service.product_category_id and service.product_category_id.parent_id and service.product_category_id.parent_id.erm_code or ''),
                    '"parent_product_category_name"': '"%s"' % (service.product_category_id and service.product_category_id.parent_id and service.product_category_id.parent_id.name or ''),
                    '"is_addons"': '"%s"' % (service.product_category_id and service.product_category_id.is_addons and 'True' or 'False'),
                    '"start_date"': '"%s"' % (service.start_date or ''),
                    '"end_date"': '"%s"' % (service.end_date or ''),
                    '"status"': '"%s"' % (service.status or ''),
                    '"reseller_code"': '"%s"' % (service.reseller_id and service.reseller_id.code or ''),
                })
            return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def check_po_active(self, service, po):
        if not service:
            return {'"code"': 1, '"data"': '"False"'}
        service_id = self.env['sale.service'].search([('reference', '=', service)])
        if not service_id:
            return {'"code"': 0, '"msg"': '"No Service"'}
        if len(service_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s service"' % len(service_id)}
        po_id = self.env['purchase.order'].search([('name', '=', po)])
        if not po_id:
            return {'"code"': 0, '"msg"': '"No PO"'}
        if len(po_id) > 1:
            return {'"code"': 0, '"msg"': '"Have %s PO"' % len(po_id)}
        # _logger.info("1111111111111 %s 11111111111111", po_id.create_date.replace(hour=0, minute=0, second=0))
        start_date = datetime.strptime(po_id.create_date, '%Y-%m-%d %H:%M:%S').date().strftime('%Y-%m-%d') + ' 00:00:00'
        end_date = datetime.strptime(po_id.create_date, '%Y-%m-%d %H:%M:%S').date().strftime('%Y-%m-%d') + ' 23:59:59'
        # _logger.info("0000000000000000 %s, %s 111111111111111111" , start_date, end_date)
        pol = self.env['purchase.order.line'].search_read([('product_id', '=', service_id.product_id.id),
                                                           ('order_id.is_active', '=', True),
                                                           ('order_id.create_date', '>=', start_date),
                                                           ('order_id.create_date', '<=', end_date)], ['name'], order='name desc', limit=1)
        if pol:
            return {'"code"': 1, '"data"': '"True"', '"name"': '\"' + (pol[0]['name'] or '') + '\"'}
        else:
            return {'"code"': 1, '"data"': '"False"'}

    @api.multi
    def view_service(self):
        """
            Open Service Form
        """
        service_form = self.env.ref('matbao_module.view_sale_service_form', False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'matbao_module.view_sale_service_form',
            'res_model': 'sale.service',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'self',
            'view_id': service_form.id,
        }

