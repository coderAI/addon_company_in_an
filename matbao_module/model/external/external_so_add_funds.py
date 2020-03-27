# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError, Warning
from odoo.tools import float_is_zero, float_compare
import ast
import json

class ExternalSOAddFunds(models.AbstractModel):
    _description = 'External SO Add Funds API'
    _name = 'external.so.add.funds'

    @api.model
    def add_funds_so(self, so_name):
        """
        TO DO:
            - Create New Invoice and Add funds in Odoo
        """

        # Objects
        SaleOrder = self.env['sale.order']

        if not so_name:
            return {'code': 0, 'msg': 'Order name could not be empty'}
        else:
            order = SaleOrder.search([('name', '=', so_name)], limit=1)
            if not order:
                return {'code': 0, 'msg': 'Order name not exists'}
        try:
            if order.state == 'not_received':
                order.button_got_it()
            if order.state == 'draft':
                if order.order_line:
                    for line in order.order_line:
                        if not line.price_updated:
                            line.write({
                                'price_updated': True
                            })
                    order.action_confirm()
                else:
                    return {'code': 0, 'msg': "Sale Order: %s no have SO lines. Pls check again!!!" % so_name}
            if order.state in ('sale', 'paid'):
                if order.fully_paid:
                    return {'code': 0, 'msg': "Sale Order %s have paid" % so_name}
                if not order.invoice_ids or not any(inv.state <> 'cancel' for inv in order.invoice_ids):
                    invoice = order.action_invoice_create()
                    invoice_id = self.env['account.invoice'].browse(invoice)
                    invoice_id.action_invoice_open()
                elif any(inv.state == 'draft' for inv in order.invoice_ids):
                    invoice_id = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                    invoice_id.action_invoice_open()
                elif any(inv.state == 'open' for inv in order.invoice_ids):
                    invoice_id = order.invoice_ids.filtered(lambda inv: inv.state == 'open')
                else:
                    return {'code': 0, 'msg': "(%s)Invoice have paid" % so_name}
                if not invoice_id.outstanding_credits_debits_widget:
                    return {'code': 0, 'msg': "%s: No have payment to add funds!!!" % so_name}

                outstanding = json.loads(invoice_id.outstanding_credits_debits_widget)
                for move in outstanding.get('content'):
                    if invoice_id.state == 'paid':
                        break
                    invoice_id.assign_outstanding_credit(move.get('id'))
                return {'code': 1, 'msg': "Add Funds Successful!"}
            else:
                return {'code': 0, 'msg': "Sale Order have fully paid, can't add funds!"}
        except ValueError:
            return {'code': 0, 'msg': 'Unknow Error!'}