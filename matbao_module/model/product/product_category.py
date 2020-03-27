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
from odoo import api, models, fields
import logging
from odoo.exceptions import Warning


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.multi
    @api.depends('name', 'parent_id', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            category.complete_name = category.name_get()[0][1]

    minimum_register_time = fields.Float(
        string='Minimum Register Time',
        help='Minimum time to register one service. For example, to register'
             ' a domain, the minimum time is one year.')
    billing_cycle = fields.Float(string='Billing Cycle')
    uom_id = fields.Many2one("product.uom", string="UOM", required=True)
    code = fields.Char(string="product category code")
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    service_sequence_id = fields.Many2one(
        'ir.sequence', string="Service Sequence")
    to_be_renewed = fields.Boolean(string="To be Renewed")

    property_renew_account_income_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Renew/Transfer Taxed Income Account",
        domain=[('deprecated', '=', False)])
    property_renew_account_expense_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Renew/Transfer Taxed Expense Account",
        domain=[('deprecated', '=', False)])
    
    property_register_untaxed_account_income_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Register Untaxed Income Account",
        domain=[('deprecated', '=', False)])
    property_renew_untaxed_account_income_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Renew/Transfer Untaxed Income Account",
        domain=[('deprecated', '=', False)])
    property_register_untaxed_account_expense_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Register Untaxed Expense Account",
        domain=[('deprecated', '=', False)])
    property_renew_untaxed_account_expense_categ_id = fields.Many2one(
        'account.account', company_dependent=True,
        string="Renew/Transfer Untaxed Expense Account",
        domain=[('deprecated', '=', False)])            

    register_analytic_income_acc_id = fields.Many2one(
        'account.analytic.account', 'Register Analytic Income Account', company_dependent=True)
    register_analytic_expense_acc_id = fields.Many2one(
        'account.analytic.account', 'Register Analytic Expense Account', company_dependent=True)

    renew_analytic_income_account_id = fields.Many2one(
        'account.analytic.account',
        string='Renew/Transfer Analytic Income Account', company_dependent=True)
    renew_analytic_expense_account_id = fields.Many2one(
        'account.analytic.account',
        'Renew/Transfer Analytic Expense Account', company_dependent=True)
    

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        ctx = self._context
        if ctx.get('in_service'):
            category_ids = self.env['product.category'].search(
                [('child_id', '=', False)])
            if category_ids:
                args += [('id', 'in', category_ids.ids)]
            else:
                args += [('id', 'in', [-1])]

        res = super(ProductCategory, self).name_search(name, args=args,
                                                       operator=operator,
                                                       limit=limit)
        return res

    @api.model
    def create(self, vals):
        IrSequence = self.env['ir.sequence']
        if not vals.get('service_sequence_id'):
            new_service_sequence = IrSequence.create({'name': vals['name'],
                                                      'padding': '7'})
            vals['service_sequence_id'] = new_service_sequence.id
        return super(ProductCategory, self).create(vals)

    @api.multi
    def unlink(self):
        for record in self:
            redundant_sequence = record.service_sequence_id
            redundant_sequence.unlink()
        return super(ProductCategory, self).unlink()
