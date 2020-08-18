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
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging as _logger
import json

class ExternalAccountInvoice(models.AbstractModel):
    _description = 'External VAT Invoice API'
    _name = 'external.vat.invoice'

    @api.model
    def get_vat_invoice_customer(self, user_code, limit=100, offset=0, order='', sort='asc', columns=[], filter=''):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        ResPartner = self.env['res.partner']
        VATInvoice = self.env['mb.export.invoice']
        AccountInvoiceLine = self.env['account.invoice.line']
        SaleOrderLine = self.env['sale.order.line']
        InvoiceNo = self.env['mb.invoice.no.line']
        data = []
        # Check data
        if not user_code:
            res.update({'"msg"': '"Customer Code could be not empty"'})
            return res
        partner_id = ResPartner.search([('ref', '=', user_code), ('company_type', '=', 'agency')], limit=1)
        if not partner_id:
            res.update({'"msg"': '"Customer not found or Customer is not agency."'})
            return res
        args = [('state', '!=', 'merge'), ('partner_id', '=', partner_id.id)]
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
                if not col in VATInvoice._fields:
                    res.update({'"msg"': '"Column {%s} not exists."' % col})
                    return res
        else:
            columns = ['name', 'partner_id', 'address', 'vat', 'req_date', 'state', 'amount_tax_receivable', 'invoice_no_ids', 'export_date', 'invoice_line_ids', 'order_line_ids']
        vats = VATInvoice.search_read(domain=args, fields=columns, limit=limit, offset=offset, order=order_fix)
        for vat in vats:
            for key, value in vat.items():
                if not value:
                    del vat[key]
                    vat.update({'\"' + key + '\"': '""'})
                elif type(value) in (int, float):
                    del vat[key]
                    vat.update({'\"' + key + '\"': value or '""'})
                elif type(value) is tuple:
                    del vat[key]
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    vat.update({
                        '\"' + key + '\"': tuple(lst)
                    })
                elif key == 'invoice_line_ids':
                    del vat[key]
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
                            '"product_category"': '\"' + (inv_line.product_id and inv_line.product_id.categ_id and inv_line.product_id.categ_id.display_name or '') + '\"',
                            '"time"': inv_line.time or 0,
                            '"price_unit"': inv_line.price_unit or 0,
                            '"taxes_amount"': inv_line.taxes_amount or 0,
                            '"price_subtotal"': inv_line.price_subtotal or 0,
                        })
                    vat.update({'\"' + key + '\"': invoice_line_ids})
                elif key == 'order_line_ids':
                    del vat[key]
                    order_line_ids = []
                    for line in value:
                        order_line = SaleOrderLine.browse(line)
                        order_line_ids.append({
                            '"register_type"': '\"' + (order_line.register_type or '') + '\"',
                            '"product_id"': order_line.product_id and order_line.product_id.id or '""',
                            '"product_code"': '\"' + (order_line.product_id and order_line.product_id.default_code or '') + '\"',
                            '"product"': '\"' + (order_line.product_id and order_line.product_id.name or '') + '\"',
                            '"product_uom"': order_line.product_uom and order_line.product_uom.id or '""',
                            '"uom"': '\"' + (order_line.product_uom and order_line.product_uom.name or '') + '\"',
                            '"product_category_id"': order_line.product_category_id and order_line.product_category_id.id or '""',
                            '"product_category_code"': '\"' + (order_line.product_category_id and order_line.product_category_id.code or '') + '\"',
                            '"product_category"': '\"' + (order_line.product_category_id and order_line.product_category_id.display_name or '') + '\"',
                            '"time"': order_line.time or 0,
                            '"register_untaxed_price"': order_line.register_untaxed_price or 0,
                            '"register_taxed_price"': order_line.register_taxed_price or 0,
                            '"renew_untaxed_price"': order_line.renew_untaxed_price or 0,
                            '"renew_taxed_price"': order_line.renew_taxed_price or 0,
                            '"price_tax"': order_line.price_tax or 0,
                            '"price_subtotal"': order_line.price_subtotal or 0,
                            '"price_total"': order_line.price_total or 0,
                        })
                    vat.update({'\"' + key + '\"': order_line_ids})
                elif key == 'invoice_no_ids':
                    del vat[key]
                    no_ids = InvoiceNo.browse(value)
                    vat.update({'\"' + key + '\"': '\"' + (value and ', '.join(no.name for no in no_ids) or '') + '\"'})
                else:
                    del vat[key]
                    vat.update({'\"' + key + '\"': '\"' + value + '\"'})
        data = vats and vats or data

        res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res

    @api.model
    def get_vat_invoice_detail(self, vat_id, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        VATInvoice = self.env['mb.export.invoice']
        data = []
        # Check Invoice
        if not vat_id or type(vat_id) is not int:
            res.update({'"msg"': '"VAT ID could be not empty and must be integer"'})
            return res
        vat = VATInvoice.browse(vat_id)
        if not vat:
            res.update({'"msg"': '"VAT not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if not vat.partner_id or (vat.partner_id and vat.partner_id.ref <> cus_code):
            res.update({'"msg"': '"VAT not belong customer %s."' % cus_code})
            return res
        inv_dict = {
            '"name"': '\"' + (vat.name or '') + '\"',
            '"partner_id"': vat.partner_id and vat.partner_id.id or '""',
            '"partner_code"': '\"' + (vat.partner_id and vat.partner_id.ref or '') + '\"',
            '"partner"': '\"' + (vat.partner_id and vat.partner_id.name or '') + '\"',
            '"address"': '\"' + (vat.address or '') + '\"',
            '"vat"': '\"' + (vat.vat or '') + '\"',
            '"req_date"': '\"' + (vat.req_date or '') + '\"',
            '"state"': '\"' + (vat.state or '') + '\"',
            '"export_date"': '\"' + (vat.export_date or '') + '\"',
            '"note"': '\"' + (vat.note or '') + '\"',
        }
        invoice_line = []
        for line in vat.invoice_line_ids:
            inv_line = {}
            order_id = line.mapped('sale_line_ids')
            if not order_id:
                inv = line.invoice_id.invoice_line_ids.filtered(
                    lambda inv: inv.product_category_id == line.product_category_id
                                and inv.product_id == line.product_id
                                and inv.mapped('sale_line_ids'))
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
                '"order_id"': order_id and order_id[0].id or (inv and inv.mapped('sale_line_ids')[0].id or '""'),
                '"invoice_id"': line.invoice_id.id
            })
            invoice_line.append(inv_line)
        inv_dict.update({
            '"invoice_line_ids"': invoice_line
        })
        order_line = []
        for line in vat.invoice_line_ids.mapped('sale_line_ids'):
            item = {}
            item.update({
                '"register_type"': '\"' + (line.register_type or '') + '\"',
                '"id"': line.id or '""',
                '"order_id"': '\"' + (line.order_id and line.order_id.name or '') + '\"',
                '"product_id"': line.product_id and line.product_id.id or '""',
                '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                '"product_uom"': line.product_uom and line.product_uom.id or '""',
                '"uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                '"product_category_code"': '\"' + (line.product_category_id and line.product_category_id.code or '') + '\"',
                '"product_category"': '\"' + (line.product_category_id and line.product_category_id.display_name or '') + '\"',
                '"time"': line.time or 0,
                '"register_untaxed_price"': line.register_untaxed_price or 0,
                '"register_taxed_price"': line.register_taxed_price or 0,
                '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                '"renew_taxed_price"': line.renew_taxed_price or 0,
                '"price_tax"': line.price_tax or 0,
                '"price_subtotal"': line.price_subtotal or 0,
                '"price_total"': line.price_total or 0,
            })
            order_line.append(item)
        inv_dict.update({
            '"order_line_ids"': order_line or '""'
        })
        inv_dict.update({'"invoice_no_ids"': '\"' + (vat.invoice_no_ids and ', '.join(no.name for no in vat.invoice_no_ids) or '') + '\"'})
        data.append(inv_dict)
        res.update({'"code"': 1, '"msg"': '"Get VAT %s Successfully"' % vat.name, '"data"': data})
        return res

    @api.model
    def send_request(self, vat_id, cus_code):
        res = {'"code"': 0, '"msg"': ''}
        VATInvoice = self.env['mb.export.invoice']
        # Check VAT
        if not vat_id or type(vat_id) is not int:
            res.update({'"msg"': '"VAT ID could be not empty and must be integer"'})
            return res
        vat = VATInvoice.browse(vat_id)
        if not vat:
            res.update({'"msg"': '"VAT not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if not vat.partner_id or (vat.partner_id and vat.partner_id.ref <> cus_code):
            res.update({'"msg"': '"VAT not belong customer %s."' % cus_code})
            return res
        try:
            if vat.state != 'new':
                return {'"code"': 0, '"msg"': '"VAT must be state New"'}
            vat.bt_hp_sent_request()
            return {'"code"': 1, '"msg"': '"Successfully"'}
        except Exception as e:
            _logger.error("Error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not send request."'}

    @api.model
    def get_order_line(self, cus_code):
        res = {'"code"': 0, '"msg"': '', '"data"': []}
        AccountInvoiceLine = self.env['account.invoice.line']
        ResPartner = self.env['res.partner']
        data = []
        # Check Customer
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        partner_id = ResPartner.search([('company_type', '=', 'agency'), ('ref', '=', cus_code)], limit =1)
        if not partner_id:
            res.update({'"msg"': '"Customer not found or have not agency"'})
            return res
        # invoice_lines = AccountInvoiceLine.search([('vat_status', 'not in', ('to_export', 'exported')), ('partner_id', '=', partner_id.id), ('invoice_id.state', '=', 'paid')]).filtered(lambda inv: (order.date_order >= (datetime.now() - timedelta(days=60)) for order in inv.mapped('sale_line_ids').mapped('order_id')))

        invoice_lines = AccountInvoiceLine.search([('vat_status', 'not in', ('to_export', 'exported')),
                                                   ('partner_id', '=', partner_id.id),
                                                   ('invoice_id.state', '=', 'paid'),
                                                   ('date_invoice', '>=',(date.today().replace(day=26)-relativedelta(months=+1)).strftime('%Y-%m-%d'))])
            #.filtered(lambda inv: (line.date_active >= (datetime.now() - timedelta(days=60)) for line in inv.mapped('sale_line_ids')))

        vat_dict = {}
        invoice_arr = []
        for line in invoice_lines:
            inv_line = {}
            order_id = line.mapped('sale_line_ids')
            if order_id.mapped('order_id').mapped('invoice_ids').filtered(lambda inv: inv.state == 'paid' and
                                                                                      inv.type == 'out_refund'):
                continue
            if not order_id:
                for i_tmp in line.invoice_id.invoice_line_ids:
                    if i_tmp.id != line.id and i_tmp.product_id.id == line.product_id.id:
                        inv = i_tmp

            inv_line.update({
                '"id"': line.id or '""',
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
                '"order_id"': order_id and order_id[0].id or '""'#(inv and inv.mapped('sale_line_ids')[0].id or '""')
            })
            invoice_arr.append(inv_line)
        vat_dict.update({
            '"invoice_line_ids"': invoice_arr
        })
        if invoice_lines:
            order_line = []
            for line in invoice_lines.mapped('sale_line_ids'):
                if line.order_id.invoice_ids.filtered(lambda inv: inv.state == 'paid' and inv.type == 'out_refund'):
                    continue
                if line.service_status != 'done':
                    continue
                item = {}
                item.update({
                    '"id"': line.id or '""',
                    '"order_id"': '\"' + (line.order_id and line.order_id.name or '') + '\"',
                    '"register_type"': '\"' + (line.register_type or '') + '\"',
                    '"product_id"': line.product_id and line.product_id.id or '""',
                    '"product_code"': '\"' + (line.product_id and line.product_id.default_code or '') + '\"',
                    '"product"': '\"' + (line.product_id and line.product_id.name or '') + '\"',
                    '"product_uom"': line.product_uom and line.product_uom.id or '""',
                    '"uom"': '\"' + (line.product_uom and line.product_uom.name or '') + '\"',
                    '"product_category_id"': line.product_category_id and line.product_category_id.id or '""',
                    '"product_category_code"': '\"' + (line.product_category_id and line.product_category_id.code or '') + '\"',
                    '"product_category"': '\"' + (line.product_category_id and line.product_category_id.display_name or '') + '\"',
                    '"time"': line.time or 0,
                    '"register_untaxed_price"': line.register_untaxed_price or 0,
                    '"register_taxed_price"': line.register_taxed_price or 0,
                    '"renew_untaxed_price"': line.renew_untaxed_price or 0,
                    '"renew_taxed_price"': line.renew_taxed_price or 0,
                    '"price_tax"': line.price_tax or 0,
                    '"price_subtotal"': line.price_subtotal or 0,
                    '"price_total"': line.price_total or 0,
                    '"date_active"': '\"' + (line.date_active or '') + '\"',
                })
                order_line.append(item)
            vat_dict.update({
                '"order_line_ids"': order_line
            })
        vat_dict.update({
            '"address"': '\"' + ((partner_id.street or '') + (partner_id.state_id and (', ' + partner_id.state_id.name) or '') + \
                                 (partner_id.country_id and (', ' + partner_id.country_id.name) or '')) + '\"',
            '"vat"': '\"' + (partner_id.vat or '') + '\"',
            '"partner_name"': '\"' + (partner_id.name or '') + '\"',
            '"partner_id"': partner_id and partner_id.id or '""'
        })
        data.append(vat_dict)
        return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}

    @api.model
    def create_vat_invoice(self, vals={}):
        res = {'"code"': 0, '"msg"': '""'}
        ResPartner = self.env['res.partner']
        VATInvoice = self.env['mb.export.invoice']
        args = [('state', 'in', ('to_export', 'exported')), ('is_agency', '=', True)]
        # Check type parameter
        if not vals or type(vals) is not dict:
            return {'"msg"': '"Vals could not be empty and must be dict"'}
        vat_dict = {'state': 'new', 'is_agency': True}
        # Check name
        vat_dict.update({
            'name': self.env['ir.sequence'].next_by_code('mb.export.invoice') or 'New'
        })
        # Check Customer
        if not vals.get('partner_id', ''):
            return {'"msg"': '"Customer could not be empty"'}
        customer_id = ResPartner.browse(vals.get('partner_id'))
        if customer_id:
            vat_dict.update({'partner_id': customer_id.id, 'company_id': customer_id.company_id and customer_id.company_id.id or 1})
            args += [('partner_id', '=', customer_id.id), ('company_id', '=', customer_id.company_id and customer_id.company_id.id or 1)]
        if not vals.get('req_date'):
            return {'"msg"': '"Request Date not found."'}
        vat_dict.update({
            'req_date': vals.get('req_date'),
            'req_user': customer_id.id
        })
        if vals.get('note'):
            vat_dict.update({'note': vals.get('note')})
        # Check Invoice Lines
        _logger.info("=== START:Delete all native states %s %s ===" % (vals.get('invoice_line_ids'), type(vals.get('invoice_line_ids'))))
        if not vals.get('invoice_line_ids'):
            return {'"msg"': '"Invoice Lines can`t empty."'}
        try:
            if len(vals.get('invoice_line_ids')) > 1:
                invoice_lines = map(int, vals.get('invoice_line_ids').split(','))
            else:
                invoice_lines = map(vals.get('invoice_line_ids'))
            inv_exported = self.env['mb.export.invoice'].search(args)
            for inv in invoice_lines:
                if inv_exported and inv_exported.mapped('invoice_line_ids') and  inv in inv_exported.mapped('invoice_line_ids').ids:
                    inv_id = self.env['account.invoice.line'].browse(inv)
                    return {'"code"': 0, '"msg"': '"Service {%s} of {%s} have exported vat invoice."' % (inv_id.product_id.name, inv_id.product_category_id.display_name)}
        except Exception as e:
            _logger.error("Can't get invoice lines: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not get invoice lines: %s"' % (e.message or repr(e))}

        vat_dict.update({'invoice_line_ids': [(6, 0, invoice_lines)]})
        vat = VATInvoice.with_context(force_company=customer_id.company_id.id, id_page=True).create(vat_dict)
        try:
            vat._get_amount()
        except ValueError:
            pass
        try:
            vat.bt_sent_request()
        except Exception as e:
            _logger.error("Can't send request exported vat invoice: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not send request: %s"' % (e.message or repr(e))}
        res['"msg"'] = '"Create VAT Invoice: %s successfully"' % vat.name
        res['"code"'] = 1
        res['"vat"'] = vat.id
        return res

    @api.model
    def write_vat_invoice(self, vat_id, cus_code, vals={}):
        res = {'"code"': 0, '"msg"': '""'}
        VATInvoice = self.env['mb.export.invoice']
        args = [('state', 'in', ('to_export', 'exported')), ('is_agency', '=', True)]
        # Check VAT
        if not vat_id or type(vat_id) is not int:
            res.update({'"msg"': '"VAT ID could be not empty and must be integer"'})
            return res
        vat = VATInvoice.browse(vat_id)
        if not vat:
            res.update({'"msg"': '"VAT not found."'})
            return res
        if not cus_code:
            res.update({'"msg"': '"Customer Code could be not empty."'})
            return res
        if not vat.partner_id or (vat.partner_id and vat.partner_id.ref <> cus_code):
            res.update({'"msg"': '"VAT not belong customer %s."' % cus_code})
            return res
        # Check type parameter
        if not vals or type(vals) is not dict:
            return {'"msg"': '"Vals could not be empty and must be dict"'}
        vat_dict = {'state': 'new'}

        if vals.get('req_date'):
            vat_dict.update({'req_date': vals.get('req_date'), 'req_user': vat.partner_id.id})
        if vals.get('note'):
            vat_dict.update({'note': vals.get('note')})
        # Check Invoice Lines
        _logger.info("=== START:Delete all native states %s %s ===" % (vals.get('invoice_line_ids'), type(vals.get('invoice_line_ids'))))
        if vals.get('invoice_line_ids'):
            try:
                if len(vals.get('invoice_line_ids')) > 1:
                    invoice_lines = map(int, vals.get('invoice_line_ids').split(','))
                else:
                    invoice_lines = map(vals.get('invoice_line_ids'))
                inv_exported = self.env['mb.export.invoice'].search(args)
                for inv in invoice_lines:
                    if inv_exported and inv_exported.mapped('invoice_line_ids') and  inv in inv_exported.mapped('invoice_line_ids').ids:
                        inv_id = self.env['account.invoice.line'].browse(inv)
                        return {'"code"': 0, '"msg"': '"Service {%s} of {%s} have exported vat invoice."' % (inv_id.product_id.name, inv_id.product_category_id.display_name)}
            except Exception as e:
                _logger.error("Can't get invoice lines: %s" % (e.message or repr(e)))
                return {'"code"': 0, '"msg"': '"Can not get invoice lines: %s"' % (e.message or repr(e))}
            vat_dict.update({'invoice_line_ids': [(6, 0, invoice_lines)]})
        if not vat_dict:
            return {'"msg"': '"No info to update."'}
        try:
            vat.write(vat_dict)
            vat.bt_sent_request()
        except Exception as e:
            _logger.error("Can't edit vat invoice: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can`t edit vat invoice: %s"' % (e.message or repr(e))}
        res['"msg"'] = '"Update VAT Invoice: %s successfully"' % vat.name
        res['"code"'] = 1
        return res