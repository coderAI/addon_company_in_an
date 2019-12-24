# -*- coding: utf-8 -*-
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class APISaleOrder(http.Controller):

    @http.route('/web/api/create_so', type='json', auth='none', methods=['post'], csrf=False)
    def api_create_so(self, **kw):
        # data = {
        #   'reference':'KH001'  ,
        #   'order_lines':[{'product_code': 'sp1', 'qty': 2 },
        #                   {'product_code': 'sp2', 'qty': 4},
        #                   {'product_code': 'sp3', 'qty': 6},
        #   ],
        # }
        partner_obj = request.env['res.partner'].sudo()
        product_obj = request.env['product.product'].sudo()
        sale_obj = request.env['sale.order'].sudo()
        payments = request.env['account.payment'].sudo()
        params = request.params.copy()
        data = request.jsonrequest
        reference = data.get('reference', '')
        order_lines = data.get('order_lines', [])
        data_error = []
        data_product = []
        # Check data and update for data_error
        if not reference or not order_lines:
            return {"result": False}
        partner = partner_obj.search([('reference', '=', reference)], limit=1)
        if not partner:
            data_error.append({'partner': 'No Customer with reference %s' % reference})
        for line in order_lines:
            product = product_obj.search([('default_code', '=', line.get('product_code', ''))], limit=1)
            if not product:
                data_error.append({'product': 'No Product with default_code %s' % line.get('product_code', '')})
            else:
                line.update({'product': product})
                data_product.append((0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': line.get('qty', 0.0),
                    'product_uom': product.uom_id.id,
                }), )

        if data_error:
            return data_error

        so_id = sale_obj.create({'partner_id': partner.id,
                                 'order_line': data_product
                                 })
        if so_id:
            so_id.action_confirm()
            lst_invoice = so_id.action_invoice_create(final=True)
            for inv in request.env['account.invoice'].sudo().browse(lst_invoice):
                inv.action_invoice_open()
                inv.generate_payments()
        return {"result": True, }
