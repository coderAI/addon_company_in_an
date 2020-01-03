# -*- coding: utf-8 -*-
import logging
import copy
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
                    # so.write({'state': 'to delivery'})
                    so.with_context(planned_picking=True).action_set_to_delivery()

        return True

    @http.route('/web/api/create-so', type='json', auth='none', methods=['post'], csrf=False)
    def api_create_so(self, **kw):
        # {
        #     "reference": "KH001",
        #     "customer_info":{
        #                         "name": "jack the Ripper",
        #                         "company_type": "person" or "company",
        #                         "vat": "e.g. BE0477472701",
        #                         "street": "Street 1...",
        #                         "street2": "Street 2...",
        #                         "city": "City ...",
        #                         "state_id": 2,
        #                         "zip": "00215",
        #                         "country_id": 1,
        #                         "phone": "+84 93xxxxx",
        #                         "mobile": "+01 415 xxx xxx",
        #                         "email": "sub@domain.com",
        #                         "title": 1,
        #                         "website": "www.facebook.com",
        #                         "customer": True,
        #                       }
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
        #         {"product_id": 3,
        #                 "qty": 2,
        #                 "tax_id": [[4, 1]],
        #                 "price_unit": 1000}
        #                 ,
        #          {"product_id": 5,
        #           "qty": 4,
        #           "tax_id": [[4, 2]],
        #           "price_unit": 2000}
        #
        #     ]}
        partner_obj = request.env['res.partner'].sudo()
        product_obj = request.env['product.product'].sudo()
        sale_obj = request.env['sale.order'].sudo()
        journal_obj = request.env['account.journal'].sudo()
        # Get data from request
        data = request.jsonrequest
        partner =False
        #check or create customer
        if data.get('reference'):
            partner = partner_obj.search([('reference', '=', data.get('reference'))], limit=1)
        if not partner:
            if data.get('customer_info'):

                customer_info = copy.deepcopy(data.get('customer_info'))
                customer_info.update({"customer":True})
                partner = partner_obj.create(customer_info)
                del data['customer_info']


        reference = data.get('reference', '')
        order_line = data.get('order_line', [])
        journal_code = data.get('journal_code', '')
        data_error = []

        # Check data and update for data_error
        if not order_line or not journal_code:
            return {"result": False}

        if not partner:
            data_error.append({'partner': 'No Customer with reference %s' % reference})

        journal = journal_obj.search([('code', '=', journal_code)], limit=1)
        if not journal:
            data_error.append({'journal': 'No journal with reference %s' % journal_code})
        data.update({
            'partner_id': partner.id,
        })
        order_line_convert =[]
        for i_line in data.get('order_line'):

            if i_line.get('tax_id'):
                i_line_copy = copy.deepcopy(i_line)
                i_line_copy.update({"tax_id":[4,i_line.get('tax_id')]})
                order_line_convert.append([0, 0,i_line_copy])
            else:
                order_line_convert.append([0, 0,i_line])
        data.update({'order_line':order_line_convert})

        del data['journal_code']
        if data.get('reference'):
            del data['reference']
        if data.get('customer_info'):
            del data['customer_info']
        _logger.info(data)
        so_id = sale_obj.create(data)
        if so_id:
            so_id.action_confirm()
            lst_invoice = so_id.action_invoice_create(final=True)
            for inv in request.env['account.invoice'].sudo().browse(lst_invoice):
                inv.action_invoice_open()
                inv.generate_payments(journal)
        return {"result": True, 'SO': so_id.name or '', 'INV': inv and inv.number or ''}
