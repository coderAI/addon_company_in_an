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

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.addons.mail.models.mail_template import format_tz


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def unlink(self):
        try:
            ctx = self._context
        except:
            return super(AccountInvoice, self).unlink()
        if ctx.get('force_unlink'):
            for invoice in self:
                if invoice.state not in ('draft', 'cancel'):
                    raise UserError(_(""" You cannot delete an invoice which is
                     not draft or cancelled. You should refund it instead."""))
            return super(models.Model, self).unlink()
        return super(AccountInvoice, self).unlink()

    @api.multi
    def action_invoice_open(self):
        # for inv in self:
        #     if inv.type == 'out_invoice' and inv.partner_id.main_account < inv.amount_total:
        #         raise UserError(_("Main Account %s not enough to validate invoice (%s)" % (inv.partner_id.main_account, inv.amount_total)))
        res = super(AccountInvoice, self).action_invoice_open()
        for inv in self:
            if inv.type == 'out_invoice':
                sale_ids = inv.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    sale_ids.write({'invisible_match_payment': True})
        return res

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if vals.get('state') == 'paid':
                sale_ids = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
                if sale_ids:
                    for order in sale_ids:
                        order.write({
                            'fully_paid': True
                        })

                        import logging
                        logging.info("------------------------------------------------")
                        logging.info("check")
                        logging.info("------------------------------------------------")
                        logging.info("------------------------------------------------")


                        if sale_ids.opportunity_id and self.type == 'out_invoice':
                            aff_program = sale_ids.opportunity_id.aff_user_id.aff_program_id
                            if aff_program:
                                company_account_obj = self.env['affilicate.company.account']
                                refund_account_tmp = company_account_obj.search(
                                    [('company_id', '=', sale_ids.partner_id.company_id.id)], limit=1)
                                if refund_account_tmp:
                                    refund_account_id = refund_account_tmp.account_id.id
                                else:
                                    raise Warning(_(
                                        "Refund account is not config for this company " + sale_ids.partner_id.company_id.name + "!!!"))
                                # Create Account Invoice Refunds

                                so_line = self.env['sale.order.line'].search([('order_id', '=', sale_ids.id)])
                                refund_inv_line = self.env['account.invoice.line']
                                invoice_line_ids = []
                                for soline in so_line:
                                    if soline.product_category_id.id in aff_program.product_category_ids.ids:
                                        invoice_line_ids.append((0, 0, {
                                            'product_id': soline.product_id.id,
                                            'quantity': soline.product_uom_qty,
                                            'price_unit': soline.aff_refunds,
                                            'company_id': sale_ids.partner_id.company_id.id,
                                            'name': 'Affiliate Refund - ' + sale_ids.name + ' - ' + sale_ids.opportunity_id.aff_user_id.name,
                                            'account_id': soline.product_category_id.property_renew_account_income_categ_id and
                                                          soline.product_category_id.property_renew_account_income_categ_id.id,
                                            'account_analytic_id': soline.product_category_id.renew_analytic_income_account_id and
                                                                   soline.product_category_id.renew_analytic_income_account_id.id,
                                            'origin': sale_ids.name,
                                            'register_type': 'renew',
                                            'type': 'out_refund',
                                            'state': 'draft'
                                        }))

                                refund_inv = self.env['account.invoice'].create({
                                    'partner_id': sale_ids.opportunity_id.aff_user_id.partner_id.id,
                                    'reference_type': 'none',
                                    'name': 'Affiliate Refund - ' + sale_ids.name + ' - ' + sale_ids.opportunity_id.aff_user_id.name,
                                    'type': 'out_refund',
                                    'account_id': refund_account_id,
                                    'company_id': sale_ids.partner_id.company_id.id,
                                    'user_id': sale_ids.user_id.id,
                                    'team_id': sale_ids.team_id.id,
                                    'refund_invoice_id': self.id,
                                    'invoice_line_ids': invoice_line_ids,
                                    'state': 'draft',
                                    'date_invoice': datetime.now().date(),
                                    'date_due': datetime.now().date(),
                                    'origin': sale_ids.name
                                })


                        if not order.order_line.filtered(lambda line: line.service_status == 'draft'):
                            order.write({
                                'state': 'completed'
                            })
                        # if order.date_order and self.date_invoice and (datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').month <> datetime.strptime(self.date_invoice, '%Y-%m-%d').month \
                        #     or datetime.strptime(order.date_order, '%Y-%m-%d %H:%M:%S').year <> datetime.strptime(self.date_invoice, '%Y-%m-%d').year):
                        # order.write({'date_order': self.date_invoice and format_tz(self.env, (self.date_invoice + ' ' + datetime.now().strftime('%H:%M:%S')), tz=self.env.user.tz, format='%Y%m%dT%H%M%SZ') or datetime.now()})
        return super(AccountInvoice, self).write(vals)
