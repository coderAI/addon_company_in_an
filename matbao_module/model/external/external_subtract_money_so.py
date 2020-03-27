# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError, Warning
from odoo.tools import float_is_zero, float_compare
import ast
import json
import logging as _logger

class ExternalSOAddFunds(models.AbstractModel):
    _description = 'External Subtract Money SO API'
    _name = 'external.subtract.money.so'

    @api.model
    def subtract_money_so(self, so_name):
        """
        TO DO:
            - Create New Invoice and Add funds in Odoo
        """
        # Objects
        SaleOrder = self.env['sale.order']

        if not so_name:
            return {'"code"': 0, '"msg"': '"Order name could not be empty"'}
        else:
            order = SaleOrder.search([('name', '=', so_name)], limit=1)
            if not order:
                return {'"code"': 0, '"msg"': '"Order name not exists"'}
        try:
            _logger.info('confirm SO %s ------------------------------' % order.name)
            if order.state == 'not_received':
                # order.button_got_it()
                order.write({'state': 'draft'})
            if order.state == 'draft':
                if order.order_line:
                    for line in order.order_line:
                        if not line.price_updated:
                            line.write({
                                'price_updated': True
                            })
                    order.action_confirm()
                else:
                    return {'"code"': 0, '"msg"': '"Sale Order: %s no have SO lines. Pls check again!!!"' % so_name}

            if order.state in ('sale', 'paid'):
                if order.fully_paid:
                    return {'"code"': 0, '"msg"': '"Sale Order %s have paid"' % so_name}
                if not order.invoice_ids or not any(inv.state <> 'cancel' for inv in order.invoice_ids):
                    try:
                        invoice = order.with_context(force_company=order.partner_id.company_id.id).action_invoice_create()
                    except Exception as e:
                        return {'"code"': 0, '"msg"': '"Can`t create Invoice for SO %s: %s"' % (so_name, (e.message or repr(e)))}
                    invoice_id = self.env['account.invoice'].browse(invoice)
                    if self.env.user.company_id <> order.partner_id.company_id:
                        domain = [
                            ('type', '=', 'sale'),
                            ('company_id', '=', order.partner_id.company_id.id),
                        ]
                        journal_id = self.env['account.journal'].search(domain, limit=1)
                        invoice_id.write({
                            'journal_id': journal_id.id,
                            'account_id': order.partner_id.property_account_receivable_id and order.partner_id.with_context(force_company=order.partner_id.company_id.id).property_account_receivable_id.id
                        })
                        if invoice_id.tax_line_ids:
                            for line in invoice_id.tax_line_ids:
                                tax = self.env['account.tax'].search([('amount_type', '=', line.tax_id.amount_type),
                                                                              ('amount', '=', line.tax_id.amount),
                                                                              ('type_tax_use', '=', 'sale'), ('company_id', '=', order.partner_id.company_id.id)], limit=1)
                                line.write({
                                    'account_id': tax.account_id.id
                                })
                    try:
                        invoice_id.with_context(force_company=order.partner_id.company_id.id).action_invoice_open()
                    except Exception as e:
                        return {'"code"': 0, '"msg"': '"Can`t validate Invoice (with SO %s): %s"' % (so_name, (e.message or repr(e)))}
                elif any(inv.state == 'draft' for inv in order.invoice_ids):
                    try:
                        invoice_id = order.invoice_ids.filtered(lambda inv: inv.state == 'draft')
                        invoice_id.with_context(force_company=order.partner_id.company_id.id).action_invoice_open()
                    except Exception as e:
                        return {'"code"': 0, '"msg"': '"Can`t validate Invoice (with SO %s): %s"' % (so_name, (e.message or repr(e)))}
                elif any(inv.state == 'open' for inv in order.invoice_ids):
                    invoice_id = order.invoice_ids.filtered(lambda inv: inv.state == 'open')
                else:
                    return {'"code"': 0, '"msg"': '"(%s)Invoice have paid"' % so_name}
                if invoice_id.state == 'paid':
                    return {'"code"': 1, '"msg"': '"Subtract Money Successful!"'}
                if not invoice_id.outstanding_credits_debits_widget:
                    return {'"code"': 0, '"msg"': '"%s: No have payment to add funds!!!"' % so_name}
                try:
                    if invoice_id.outstanding_credits_debits_widget:
                        outstanding = json.loads(invoice_id.outstanding_credits_debits_widget)
                        if outstanding:
                            for move in outstanding.get('content'):
                                if invoice_id.state == 'paid':
                                    break
                                invoice_id.assign_outstanding_credit(move.get('id'))
                            return {'"code"': 1, '"msg"': '"Subtract Money Successful!"'}
                        else:
                            return {'"code"': 1, '"msg"': '"Subtract Money Successful!"'}
                    else:
                        return {'"code"': 0, '"msg"': '"No money!"'}
                except Exception as e:
                    return {'"code"': 0, '"msg"': '"Subtract Money Fail!: %s"' % (e.message or repr(e))}
            else:
                return {'"code"': 0, '"msg"': '"Sale Order have fully paid, can`t add funds!"'}
        except ValueError:
            return {'"code"': 0, '"msg"': '"Unknow Error!"'}