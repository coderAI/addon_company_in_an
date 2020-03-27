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

from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
from ..sale.sale_order_line import REGISTER_TYPE
import re
from odoo.exceptions import UserError
import logging as _logger
import json


class ExternalAccountInvoice(models.AbstractModel):
    _description = 'External Account Invoice API'
    _name = 'external.account.invoice'

    @api.model
    def get_invoice_customer(self, user_code, inv_code='', limit=100, offset=0, order=None, sort='asc',
                        columns=['number', 'date_invoice', 'journal_id', 'account_id', 'origin', 'type', 'create_date', 'comment',
                                 'state', 'amount_untaxed', 'amount_tax', 'amount_total', 'residual', 'invoice_line_ids', 'id'], filter=''):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        AccountInvoice = self.env['account.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        data = []
        # Check data
        if not user_code:
            res.update({'"msg"': '"Username could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', user_code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Username not found."'})
            return res
        args = [('partner_id', '=', partner_id.id), ('type', 'in', ('out_invoice', 'out_refund')),
                ('account_id', '=', partner_id.with_context(force_company=partner_id.company_id.id).property_account_receivable_id.id),]
        if inv_code:
            args.append(('number', '=', inv_code))
        if filter:
            if filter not in ('draft', 'open', 'paid', 'cancel'):
                res.update({'"msg"': '"Filter must be in `draft`, `open`, `paid` or `cancel`"'})
                return res
            args.append(('state', '=', filter))
        order_fix = order
        if order:
            if sort:
                if sort not in ('asc', 'desc'):
                    res.update({'"msg"': '"Sort must be `asc` or `desc`"'})
                    return res
                order_fix += ' ' + sort
        if columns:
            for col in columns:
                if not col in AccountInvoice._fields:
                    res.update({'"msg"': '"Column {%s} not exists."' % col})
                    return res
        invoices = AccountInvoice.search_read(domain=args, fields=columns, limit=limit, offset=offset, order=order_fix)
        for inv in invoices:
            invoice_id = AccountInvoice.browse(inv['id'])
            if invoice_id.state <> 'paid' and any(l.register_type == 'upgrade' for l in invoice_id.invoice_line_ids):
                continue
            for key, value in inv.items():
                if not value:
                    del inv[key]
                    inv.update({'\"' + key + '\"': '""'})
                elif type(value) in (int, float):
                    del inv[key]
                    inv.update({'\"' + key + '\"': value or '""'})
                elif type(value) is tuple:
                    del inv[key]
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    inv.update({
                        '\"' + key + '\"': tuple(lst)
                    })
                elif key == 'invoice_line_ids':
                    del inv[key]
                    invoice_line_ids = []
                    for line in value:
                        inv_line = AccountInvoiceLine.browse(line)
                        invoice_line_ids.append({
                            '"register_type"': '\"' + (inv_line.register_type or '') + '\"',
                            '"product_id"': inv_line.product_id and inv_line.product_id.id or '""',
                            '"product_code"': '\"' + (inv_line.product_id and inv_line.product_id.default_code or '') + '\"',
                            '"product"': '\"' + (inv_line.product_id and inv_line.product_id.name or '') + '\"',
                            '"uom_id"': inv_line.uom_id and inv_line.uom_id.id or '""',
                            '"uom"': '\"' + (inv_line.uom_id and inv_line.uom_id.name or '') + '\"',
                            '"product_category_id"': inv_line.product_id and inv_line.product_id.categ_id and inv_line.product_id.categ_id.id or '""',
                            '"product_category_code"': '\"' + (inv_line.product_id and inv_line.product_id.categ_id and inv_line.product_id.categ_id.code or '') + '\"',
                            '"time"': inv_line.time or 0,
                            '"price_unit"': inv_line.price_unit or 0,
                            '"taxes_amount"': inv_line.taxes_amount or 0,
                            '"price_subtotal"': inv_line.price_subtotal or 0,
                        })
                    inv.update({'\"' + key + '\"': invoice_line_ids})
                else:
                    del inv[key]
                    inv.update({'\"' + key + '\"': '\"' + value + '\"'})
            data.append(inv)
        # data = invoices and invoices or data

        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_invoice_detail(self, inv_id, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        AccountInvoice = self.env['account.invoice']
        data = []
        # Check Invoice
        if not inv_id or type(inv_id) is not int:
            res.update({'"msg"': '"Invoice id could be not empty and must be integer"'})
            return res
        inv = AccountInvoice.browse(inv_id)
        if not inv:
            res.update({'"msg"': '"Invoice not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if inv.partner_id.ref <> cus_code:
            res.update({'"msg"': '"Invoice not belong customer %s."' % cus_code})
            return res
        order = inv.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
        inv_dict = {
            '"number"': '\"' + (inv.number or '') + '\"',
            '"date_invoice"': '\"' + (inv.date_invoice or '') + '\"',
            '"create_date"': '\"' + (inv.create_date or '') + '\"',
            '"user_id"': inv.user_id and inv.user_id.id or '""',
            '"team_id"': '\"' + (inv.team_id and inv.team_id.code or '') + '\"',
            '"journal_id"': inv.journal_id and inv.journal_id.id or '""',
            '"journal"': '\"' + (inv.journal_id and inv.journal_id.name or '') + '\"',
            '"account_id"': inv.account_id and inv.account_id.id or '""',
            '"account_code"': '\"' + (inv.account_id and inv.account_id.code or '') + '\"',
            '"origin"': '\"' + (inv.origin or '') + '\"',
            '"company_id"': inv.company_id and inv.company_id.id or '""',
            '"amount_untaxed"': inv.amount_untaxed and inv.amount_untaxed or 0,
            '"amount_tax"': inv.amount_tax and inv.amount_tax or 0,
            '"amount_total"': inv.amount_total and inv.amount_total or 0,
            '"residual"': inv.residual and inv.residual or 0,
            '"state"': '\"' + (inv.state or 'draft') + '\"',
            '"type"': '\"' + (inv.type or '') + '\"',
            '"comment"': '\"' + (inv.comment or '') + '\"',
            '"order_status"': '\"' + (order and order[0].state or '') + '\"',
        }
        invoice_line = []
        for line in inv.invoice_line_ids:
            inv_line = {}
            inv_line.update({
                '"register_type"': '\"' + (line.register_type or '') + '\"',
                '"product_id"': line.product_id and line.product_id.id or '',
                '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                '"uom_id"': line.uom_id and line.uom_id.id or '',
                '"uom"': '\"' + (line.uom_id and line.uom_id.name or '') + '\"',
                '"product_category_id"': line.product_id and line.product_id.categ_id and line.product_id.categ_id.id or '',
                '"product_category_code"': '\"' + (line.product_id and line.product_id.categ_id and line.product_id.categ_id.code or '') + '\"',
                '"product_category"': '\"' + (line.product_id and line.product_id.categ_id and line.product_id.categ_id.display_name or '') + '\"',
                '"time"': line.time or 0,
                '"price_unit"': line.price_unit or 0,
                '"taxes_amount"': line.taxes_amount or 0,
                '"price_subtotal"': line.price_subtotal or 0,
            })
            invoice_line.append(inv_line)
        inv_dict.update({
            '"invoice_line_ids"': invoice_line
        })
        data.append(inv_dict)
        res.update({'"code"': 1, '"msg"': '"Get Invoice %s Successfully"' % inv.number, '"data"': data})
        return res


class ExternalAccountPayment(models.AbstractModel):
    _description = 'External Account Payment API'
    _name = 'external.account.payment'

    @api.model
    def get_payment_customer(self, user_code, payment_code=None, limit=100, offset=0, order=None, sort='asc',
                        columns=['name', 'payment_date', 'partner_id', 'journal_id', 'amount', 'communication', 'company_id'], filter=''):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        AccountPayment = self.env['account.payment']
        data = []
        # Check data
        if not user_code:
            res.update({'"msg"': '"Username could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', user_code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Username not found."'})
            return res
        args = [('partner_id', '=', partner_id.id), ('receive_form', '=', True)]
        if payment_code:
            args.append(('name', '=', payment_code))
        if filter:
            if filter not in ('draft', 'posted', 'reconciled'):
                res.update({'"msg"': '"Filter must be in `draft`, `posted`, or `reconciled`"'})
                return res
            args.append(('state', '=', filter))
        order_fix = order
        if order:
            if sort:
                if sort not in ('asc', 'desc'):
                    res.update({'"msg"': '"Sort must be `asc` or `desc`"'})
                    return res
                order_fix += ' ' + sort
        if columns:
            for col in columns:
                if not col in AccountPayment._fields:
                    res.update({'"msg"': '"Column {%s} not exists."' % col})
                    return res
        payments = AccountPayment.search_read(domain=args, fields=columns, limit=limit, offset=offset, order=order_fix)
        for pay in payments:
            for key, value in pay.items():
                if not value:
                    del pay[key]
                    pay.update({'\"' + key + '\"': '""'})
                elif type(value) in (int, float):
                    del pay[key]
                    pay.update({'\"' + key + '\"': value or '""'})
                elif type(value) is tuple:
                    del pay[key]
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    pay.update({
                        '\"' + key + '\"': tuple(lst)
                    })
        data = payments and payments or data
        # data = json.dumps(data)

        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_payment_detail(self, payment_id, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        AccountPayment = self.env['account.payment']
        ResPartner = self.env['res.partner']
        # Check data
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty"'})
            return res
        customer_id = ResPartner.search([('ref', '=', cus_code)])
        if not customer_id:
            res.update({'"msg"': '"Customer not found."'})
            return res
        if not payment_id:
            res.update({'"msg"': '"Payment ID could be not empty"'})
            return res
        payment = AccountPayment.search([('id', '=', payment_id), ('partner_id', '=', customer_id.id)])
        if not payment:
            res.update({'"msg"': '"Payment not found."'})
            return res
        data = [{
            '"name"': '\"' + (payment.name or '') + '\"',
            '"payment_date"': '\"' + (payment.payment_date or '') + '\"',
            '"partner_id"': payment.partner_id and payment.partner_id.id or '""',
            '"partner"': '\"' + (payment.partner_id and payment.partner_id.name or '') + '\"',
            '"journal_id"': '\"' + (payment.journal_id and payment.journal_id.display_name or '') + '\"',
            '"amount"': payment.amount or 0,
            '"communication"': '\"' + (payment.communication or '') + '\"',
            '"company_id"': payment.company_id and payment.company_id.id or '""'
        }]
        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_move_line(self, id):
        AccountMoveLine = self.env['account.move.line']
        if not id:
            return {'"code"': 0, '"msg"': '"ID could be not empty"'}
        move_line_id = AccountMoveLine.browse(id)
        try:
            data = [{
                '"id"': move_line_id.id,
                '"journal"': '\"' + (move_line_id.move_id and move_line_id.move_id.name or '') + '\"',
                '"debit"': move_line_id.debit or 0,
                '"credit"': move_line_id.credit or 0,
                '"date"': '\"' + (move_line_id.move_id and move_line_id.move_id.date or '') + '\"',
                '"description"': '\"' + (move_line_id.name or '') + '\"',
                '"order_name"': '\"' + (move_line_id.invoice_id and move_line_id.invoice_id.origin or '') + '\"'
            }]
            return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Get data error: %s"' % (e.message or repr(e))}

    @api.model
    def get_transaction(self, code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        AccountMoveLine = self.env['account.move.line']
        data = []
        # Check data
        if not code:
            res.update({'"msg"': '"Customer Code could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', code)], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Customer not found."'})
            return res
        move_line_ids = AccountMoveLine.search([('account_id.internal_type', '=', 'receivable'),
                                                ('account_id', '=', partner_id.with_context(force_company=partner_id.company_id.id).property_account_receivable_id.id),
                                                ('partner_id', '=', partner_id.id),
                                                ('move_id.state', '=', 'posted')])
        for move in move_line_ids:
            dict = {}
            dict.update({
                # '"partner_id"': '\"' + (move.partner_id and (move.partner_id.ref + ' ' + move.partner_id.name) or '') + '\"',
                '"id"': move.id,
                '"journal"': '\"' + (move.move_id and move.move_id.name or '') + '\"',
                '"debit"': move.debit or 0,
                '"credit"': move.credit or 0,
                '"invoice_id"': move.invoice_id and move.invoice_id.id or '""',
                '"payment_id"': move.payment_id and move.payment_id.id or '""',
                '"date"': '\"' + (move.move_id and datetime.strptime(move.move_id.date,'%Y-%m-%d').strftime('%d/%m/%Y') or '') + '\"',
                '"description"': '\"' + (move.name or '') + '\"'
            })
            if move.invoice_id:
                invoice_line = []
                for line in move.invoice_id.invoice_line_ids:
                    inv_line = {}
                    inv_line.update({
                        '"register_type"': '\"' + (line.register_type or '') + '\"',
                        '"product_id"': line.product_id and line.product_id.id or '""',
                        '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                        '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                        '"uom_id"': line.uom_id and line.uom_id.id or '""',
                        '"uom"': '\"' + (line.uom_id and line.uom_id.name or '') + '\"',
                        '"product_category_id"': line.product_id and line.product_id.categ_id and line.product_id.categ_id.id or '""',
                        '"product_category_code"': '\"' + (line.product_id and line.product_id.categ_id and line.product_id.categ_id.code or '') + '\"',
                        '"product_category"': '\"' + (line.product_id and line.product_id.categ_id and line.product_id.categ_id.display_name or '') + '\"',
                        '"time"': line.time or 0,
                        '"price_unit"': line.price_unit or 0,
                        '"taxes_amount"': line.taxes_amount or 0,
                        '"price_subtotal"': line.price_subtotal or 0,
                    })
                    invoice_line.append(inv_line)
                dict.update({
                    '"invoice_line"': invoice_line
                })
            data.append(dict)
        return {'"code"': 1,
                '"msg"': '"Successfully"',
                '"data"': data}