# -*- coding: utf-8 -*-
import logging
from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
import json
_logger = logging.getLogger(__name__)




class APISaleOrder(http.Controller):

    @http.route('/check-product-and-map-sale-order/call',
                type='http', auth='public', website=True)
    def start_check_product_and_map_so(self,**kw):
        work_order_data = request.env['check.product'].create({'user_id':SUPERUSER_ID})
        work_order_data.btn_map_sale_order_line()
        res={'code':200,'message':'successful','data':True}
        return json.dumps(res)


    @http.route('/template_barcode/<int:work_order_id>',
                type='http', auth='public', website=True)
    def edit_template_barcode(self,work_order_id=None,**post):
        work_order_data = request.env['work.order'].browse(work_order_id)
        vals = {'docs': [work_order_data]}
        return request.render('working_order.template_edit_report_work_order_barcode',vals)



    @http.route('/web/api/change-status-orders', type='json', auth='none', methods=['post'], csrf=False)
    def api_paid_so(self, **kw):
        # data = {
        #     'barcode' : '0000001'
        # }
        wol_obj = request.env['work.order.line'].sudo()
        # so_obj = request.env['sale.order'].sudo()
        # sol_obj = request.env['sale.order.line'].sudo()
        params = request.params.copy()
        data = request.jsonrequest
        barcode = data.get('barcode', '')
        for wol in wol_obj.search([('bar_code', '=', barcode)], limit=1):
            wol.write({'state': 'done'})
            wo = wol.work_order_id.sudo()
            check_wol_another_in_same_wo = wo.work_order_line_ids.filtered(lambda r: r.state == 'draft')
            if not check_wol_another_in_same_wo:
                wo.write({'state': 'done'})
            sol = wol.sale_order_line_id.sudo()
            check_wol_another_in_same_sol = wol_obj.search([('sale_order_line_id', '=', sol.id),
                                                            ('state', '=', 'draft'), ])
            if not check_wol_another_in_same_sol:
                sol.write({'state_new': 'done'})
                so = sol.order_id
                check_sol_in_same_so = so.order_line.filtered(lambda r: r.state_new in ['draft'])
                if not check_sol_in_same_so:
                    so.write({'state': 'to delivery'})

        return True

    @http.route('/web/api/create-so', type='json', auth='none', methods=['post'], csrf=False)
    def api_create_so(self, **kw):
        # data = {
        #   'reference':'KH001',
        #   'journal_code': 'BNK1',
        #   'tax_code': [],
        #   'order_lines':[{'product_code': 'SP01', 'qty': 2, 'price_unit': 1000 },
        #                   {'product_code': 'SP03', 'qty': 4, 'price_unit': 2000 },
        #                   {'product_code': 'SP04', 'qty': 6, 'price_unit': 3000 },
        #   ],
        # }
        partner_obj = request.env['res.partner'].sudo()
        product_obj = request.env['product.product'].sudo()
        sale_obj = request.env['sale.order'].sudo()
        payments = request.env['account.payment'].sudo()
        journal_obj = request.env['account.journal'].sudo()
        tax_obj = request.env['account.tax'].sudo()
        params = request.params.copy()
        data = request.jsonrequest
        # Get data from request
        reference = data.get('reference', '')
        order_lines = data.get('order_lines', [])
        journal_code = data.get('journal_code', '')


        data_error = []
        data_product = []
        # Check data and update for data_error
        if not reference or not order_lines or not journal_code:
            return {"result": False}
        partner = partner_obj.search([('reference', '=', reference)], limit=1)
        if not partner:
            data_error.append({'partner': 'No Customer with reference %s' % reference})

        journal = journal_obj.search([('code', '=', journal_code)], limit=1)
        if not journal:
            data_error.append({'journal': 'No journal with reference %s' % journal_code})

        tax_ids = False
        if 'tax_code' in data:
            tax_code = data.get('tax_code', '')
            if tax_code:
                tax = tax_obj.search([('code', '=', tax_code)], limit=1)
                if not tax:
                    data_error.append({'tax_code': 'No tax code with  %s' % journal_code})
            elif tax_code == '':
                tax_ids = []

        for line in order_lines:
            product = product_obj.search([('default_code', '=', line.get('product_code', ''))], limit=1)
            if not product:
                data_error.append({'product': 'No Product with default_code %s' % line.get('product_code', '')})
            else:
                line.update({'product': product})
                vals_product = {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': line.get('qty', 0.0),
                    'product_uom': product.uom_id.id,
                    'price_unit': line.get('price_unit', 0.0),
                }
                if tax_ids:
                    vals_product.update({'tax_id': [(6, 0, tax_ids)], })
                elif tax_ids == []:
                    vals_product.update({'tax_id': [(6, 0, [])], })
                data_product.append((0, 0, vals_product), )

        if data_error:
            return data_error
        inv = False
        so_id = sale_obj.create({'partner_id': partner.id,
                                 'order_line': data_product
                                 })
        if so_id:
            so_id.action_confirm()
            lst_invoice = so_id.action_invoice_create(final=True)
            for inv in request.env['account.invoice'].sudo().browse(lst_invoice):
                inv.action_invoice_open()
                inv.generate_payments(journal)
        return {"result": True, 'SO': so_id.name or '', 'INV': inv and inv.number or ''}
