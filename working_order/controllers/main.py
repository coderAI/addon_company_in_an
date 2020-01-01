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
        # {
        #     "reference": "KH001",
        #     "journal_code": "BNK1",
        #     "user_id": 1,
        #     "team_id": 1,
        #     "store_id": 1,
        #     "market_place_id": 1,
        #     "platform_id": 1,
        #     "carrier_id": 1,
        #     "coupon_code": "your code",
        #     "payment_method": "bank payment code",
        #     "transaction_id": "bank payment transaction id",
        #     "order_ip": "your order ip",
        #     "tracking_number": "your Tracking Number",
        #     "order_shipping_location": "your Order Shipping Location",
        #     "order_line": [
        #         [0, 0, {"product_id": 3,
        #                 "qty": 2,
        #                 "tax_id": [[4, 1]],
        #                 "price_unit": 1000}],
        #
        #         [0, 0,
        #          {"product_id": 5,
        #           "qty": 4,
        #           "tax_id": [[4, 2]],
        #           "price_unit": 2000}]
        #
        #     ]}
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
        order_line = data.get('order_line', [])
        journal_code = data.get('journal_code', '')
        data_error = []
        data_product = []
        # Check data and update for data_error
        if not reference or not order_line or not journal_code:
            return {"result": False}
        partner = partner_obj.search([('reference', '=', reference)], limit=1)
        if not partner:
            data_error.append({'partner': 'No Customer with reference %s' % reference})

        journal = journal_obj.search([('code', '=', journal_code)], limit=1)
        if not journal:
            data_error.append({'journal': 'No journal with reference %s' % journal_code})
        data.update({
            'partner_id': partner.id,
        })
        _logger.info(data)
        del data['journal_code']
        del data['reference']
        _logger.info(data)
        so_id = sale_obj.create(data)
        if so_id:
            so_id.action_confirm()
            lst_invoice = so_id.action_invoice_create(final=True)
            for inv in request.env['account.invoice'].sudo().browse(lst_invoice):
                inv.action_invoice_open()
                inv.generate_payments(journal)
        return {"result": True, 'SO': so_id.name or '', 'INV': inv and inv.number or ''}
