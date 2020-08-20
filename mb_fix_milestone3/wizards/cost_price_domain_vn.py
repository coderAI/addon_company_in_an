# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools.float_utils import float_compare
from datetime import datetime, timedelta
import time
import logging as _logger
import json

class CostPriceDomain(models.TransientModel):
    _name = "cost.price.domain"

    date = fields.Date('Date From', default=time.strftime('2018-05-01'))
    date_to = fields.Date('Date To', default=time.strftime('2018-05-01'))
    line_ids = fields.Many2many('cost.price.domain.vn', string='Detail')

    @api.multi
    def get_po_run_cost_price(self):
        # order_ids = self.env['purchase.order.line'].sudo().search([('register_type', 'in', ('renew', 'transfer')),
        #                                                           ('order_id.date_order', '>=', self.date + ' 00:00:00'),
        #                                                           ('order_id.state', '=', 'purchase'),
        #                                                           ('product_id.categ_id.code', '=like', '.%'), '|',
        #                                                           ('product_id.categ_id.code', 'ilike', '.vn'),
        #                                                           ('product_id.categ_id.code', 'ilike', '.tmtv')]).mapped('order_id')
        cr = self.env.cr
        cr.execute("""  select po.id
                        from purchase_order po
                            join purchase_order_line pol on pol.order_id = po.id
                            join product_product pp on pp.id = pol.product_id
                            join product_template pt on pt.id = pp.product_tmpl_id
                            join product_category pc on pc.id = pt.categ_id
                        where pol.register_type in ('renew', 'transfer') 
                            and date_order::date >= %s
                            and date_order::date <= %s
                            and po.state = 'purchase'
                            and left(pc.code, 1) = '.'
                            and (right(pc.code, 3) = '.vn' or right(pc.code, 5) = '.tmtv')""",
                   (self.date, self.date_to))
        rsl = cr.dictfetchall()
        order_ids = False
        if rsl:
            order_ids = self.env['purchase.order'].browse([po['id'] for po in rsl])
        # _logger.info("9999999999999 %s 9999999999999" % order_ids)
        vals = []
        self.line_ids = False
        if order_ids:
            for order in order_ids:
                bill_ids = order.sudo().invoice_ids.sorted(lambda l: l.id)
                invoice_ids = self.env['account.invoice'].sudo().search([('origin', '=', order.name)])
                if not invoice_ids:
                    invoice_ids = self.env['account.invoice.line'].sudo().search([('product_id', '=', order.order_line and order.order_line[0].product_id and order.order_line[0].product_id.id or False),
                                                                                  ('partner_id', '=', order.company_id.partner_id.id),
                                                                                  ('invoice_id.amount_total', '=', bill_ids and bill_ids[0].amount_total)]).mapped('invoice_id')
                # _logger.info("888888888888888 %s, %s %%%%%%%%%%%%%%%%" % (bill_ids, invoice_ids))
                vals.append((0, 0, {
                    'order': order.name,
                    'company_id': order.company_id.id,
                    'bill': bill_ids and '; '.join([((bill.number or '') + ',' + str(bill.id)) for bill in bill_ids]) or '',
                    'invoice': invoice_ids and '; '.join([((inv.number or '') + ',' + str(inv.id)) for inv in invoice_ids]) or ''
                }))
        if vals:
            self.line_ids = vals

    @api.multi
    def rollback_run_po(self):
        if self.line_ids:
            for line in self.line_ids:
                invs = []
                order_id = self.env['purchase.order'].search([('name', '=', line.order), ('state', '=', 'purchase')])
                bills = line.bill and [int(bill[bill.find(',')+1:]) for bill in line.bill.split('; ')]
                bill_ids = bills and self.env['account.invoice'].browse(bills) or False
                for bill in bill_ids:
                    if bill.payment_move_line_ids:
                        for move_line in bill.payment_move_line_ids:
                            _logger.info("$$$$$$$$$$$$$$$ %s $$$$$$$$$$$$$$" % move_line)
                            move_line.with_context(invoice_id=bill.id).remove_move_reconcile()
                        self._cr.commit()
                    if bill.state == 'open':
                        _logger.info("4444444444444 %s 222222222222222", bill)
                        bill.action_invoice_cancel()
                        self._cr.commit()
                    if bill.state == 'cancel':
                        bill.action_invoice_draft()
                        self._cr.commit()
                    _logger.info("111111111111111111 %s %s 222222222222222222", bill, bill.state)
                    invs.append(bill.id)
                    # bill.unlink()
                if line.invoice:
                    invoices = line.invoice and [int(invoice[invoice.find(',')+1:]) for invoice in line.invoice.split('; ')]
                    invoice_ids = invoices and self.env['account.invoice'].browse(invoices) or False
                    for invoice in invoice_ids:
                        if invoice.payment_move_line_ids:
                            for move_line in invoice.payment_move_line_ids:
                                _logger.info("$$$$$$$$$$$$$$$ %s $$$$$$$$$$$$$$" % move_line)
                                move_line.with_context(invoice_id=invoice.id).remove_move_reconcile()
                            self._cr.commit()
                        if invoice.state == 'open':
                            invoice.action_invoice_cancel()
                            self._cr.commit()
                        if invoice.state == 'cancel':
                            invoice.action_invoice_draft()
                            self._cr.commit()
                        _logger.info("111111111111111111 %s %s 222222222222222222", invoice, invoice.state)
                        invs.append(invoice.id)
                        # invoice.unlink()
                if invs:
                    inv_ids = self.env['account.invoice'].browse(invs)
                    inv_ids.write({'move_name': False})
                    inv_ids.unlink()
                    self._cr.commit()
                # order_id.button_cancel()
                # order_id.button_draft()
                order_id.state = 'draft'
                self._cr.commit()

    @api.model
    def get_po_vn(self, date_from, date_to):
        # _logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        if not date_from:
            return {'"code"': 0, '"msg"': '"Date From could be not empty."'}
        if not date_to:
            return {'"code"': 0, '"msg"': '"Date To could be not empty."'}
        cr = self.env.cr
        cr.execute("""  select po.id
                                from purchase_order po
                                    join purchase_order_line pol on pol.order_id = po.id
                                    join product_product pp on pp.id = pol.product_id
                                    join product_template pt on pt.id = pp.product_tmpl_id
                                    join product_category pc on pc.id = pt.categ_id
                                where pol.register_type in ('renew', 'transfer') 
                                    and date_order::date >= %s
                                    and date_order::date <= %s
                                    and po.state = 'purchase'
                                    and left(pc.code, 1) = '.'
                                    and (right(pc.code, 3) = '.vn' or right(pc.code, 5) = '.tmtv')""",
                   (date_from, date_to))
        rsl = cr.dictfetchall()
        order_ids = False
        if rsl:
            order_ids = self.env['purchase.order'].browse([po['id'] for po in rsl])
        vals = []
        try:
            if order_ids:
                for order in order_ids:
                    bill_ids = order.sudo().invoice_ids.sorted(lambda l: l.id)
                    invoice_ids = self.env['account.invoice'].sudo().search([('origin', '=', order.name)])
                    if not invoice_ids:
                        invoice_ids = self.env['account.invoice.line'].sudo().search([('product_id', '=', order.order_line and order.order_line[0].product_id and order.order_line[0].product_id.id or False),
                                                                                      ('partner_id', '=', order.company_id.partner_id.id),
                                                                                      ('invoice_id.amount_total', '=', bill_ids and bill_ids[0].amount_total)]).mapped('invoice_id')
                    vals.append({
                        '"order"': '\"' + order.name + '\"',
                        '"company_id"': order.company_id.id or 0,
                        '"bill"': '\"' + (bill_ids and '; '.join([((bill.number or '') + ',' + str(bill.id)) for bill in bill_ids]) or '') + '\"',
                        '"invoice"': '\"' + (invoice_ids and '; '.join([((inv.number or '') + ',' + str(inv.id)) for inv in invoice_ids]) or '') + '\"'
                    })
            return {'"code"': 1, '"msg"': '"Get %s Successfully"' % len(vals), '"data"': vals}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

    @api.model
    def rollback_po(self, vals={}):
        if not vals or type(vals) is not dict:
            return {'"code"': 0, '"msg"': '"Vals not valid."'}
        if not vals.get('order'):
            return {'"code"': 0, '"msg"': '"Order can not found."'}
        if not vals.get('bill'):
            return {'"code"': 0, '"msg"': '"Bill can not found."'}
        try:
            invs = []
            order_id = self.env['purchase.order'].search([('name', '=', vals.get('order')), ('state', '=', 'purchase')])
            if not order_id:
                return {'"code"': 0, '"msg"': '"PO can not found."'}
            if len(order_id) > 1:
                return {'"code"': 0, '"msg"': '"Have %s PO."' % len(order_id)}
            bills = vals.get('bill') and [int(bill[bill.find(',') + 1:]) for bill in vals.get('bill').split('; ')]
            # _logger.info("@@@@@@@@@@@@@@@ %s , %s @@@@@@@@@@@@@@@@", vals.get('bill'), [int(bill[bill.find(',') + 1:]) for bill in vals.get('bill').split('; ')])
            bill_ids = bills and self.env['account.invoice'].browse(bills) or False
            for bill in bill_ids:
                # _logger.info("@@@@@@@@@@@@@@@ %s , %s @@@@@@@@@@@@@@@@", bill, bill.payment_move_line_ids)
                if bill.payment_move_line_ids:
                    for move_line in bill.payment_move_line_ids:
                        move_line.with_context(invoice_id=bill.id).remove_move_reconcile()
                    self._cr.commit()
                if bill.state == 'open':
                    # _logger.info("@@@@@@@@@@@@@@@$$$$$$$$$$$$$$$$$$$$@@@@@@@@@@@@@@@@")
                    bill.action_invoice_cancel()
                    self._cr.commit()
                if bill.state == 'cancel':
                    # _logger.info("@@@@@@@@@@@@@@@$$$$$$$$$$%%%%%%%%%%$$$$$$$$$$@@@@@@@@@@@@@@@@")
                    bill.action_invoice_draft()
                    self._cr.commit()
                invs.append(bill.id)
                # bill.unlink()
            # _logger.info("@@@@@@@@@@@@@@@$$$$$$$$$$ %s $$$$$$$$$$@@@@@@@@@@@@@@@@" % vals.get('invoice', ''))
            if vals.get('invoice', ''):
                invoices = vals.get('invoice', '') and [int(invoice[invoice.find(',') + 1:]) for invoice in vals.get('invoice', '').split('; ')]
                # _logger.info("@@@@@@@@@@@@@@@$$$$$$$$$$ %s $$$$$$$$$$@@@@@@@@@@@@@@@@" % invoices)
                invoice_ids = invoices and self.env['account.invoice'].browse(invoices) or False
                # _logger.info("@@@@@@@@@@@@@@@$$$$$$$$$$ %s $$$$$$$$$$@@@@@@@@@@@@@@@@" % invoice_ids)
                for invoice in invoice_ids:
                    if invoice.payment_move_line_ids:
                        for move_line in invoice.payment_move_line_ids:
                            # _logger.info("$$$$$$$$$$$$$$$ %s $$$$$$$$$$$$$$" % move_line)
                            move_line.with_context(invoice_id=invoice.id).remove_move_reconcile()
                        self._cr.commit()
                    if invoice.state == 'open':
                        invoice.action_invoice_cancel()
                        self._cr.commit()
                    if invoice.state == 'cancel':
                        invoice.action_invoice_draft()
                        self._cr.commit()
                    invs.append(invoice.id)
                    # invoice.unlink()
            if invs:
                inv_ids = self.env['account.invoice'].browse(invs)
                inv_ids.write({'move_name': False})
                inv_ids.unlink()
                self._cr.commit()
            order_id.state = 'draft'
            self._cr.commit()
            return {'"code"': 1, '"msg"': '"Rollback PO %s successfully"' % vals.get('order')}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}


class CostPriceDomainVN(models.TransientModel):
    _name = "cost.price.domain.vn"

    order = fields.Char('PO')
    company_id = fields.Integer('Company')
    bill = fields.Char('Vendor Bill')
    invoice = fields.Char('Customer Invoice')


