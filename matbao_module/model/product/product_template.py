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
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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
        'account.analytic.account', 'Register Analytic Income Account')
    register_analytic_expense_acc_id = fields.Many2one(
        'account.analytic.account', 'Register Analytic Expense Account')

    renew_analytic_income_account_id = fields.Many2one(
        'account.analytic.account',
        string='Renew/Transfer Analytic Income Account')
    renew_analytic_expense_account_id = fields.Many2one(
        'account.analytic.account',
        'Renew/Transfer Analytic Expense Account')

    @api.model
    def _get_default_minimum_register_time(self):
        """
            TO DO:
            - Get default Minimum Register Time from product category when
            create a new product
        """
        default_categ_id = self._get_default_category_id()
        if default_categ_id:
            return self.env['product.category'].browse(
                default_categ_id).minimum_register_time

    @api.model
    def _get_default_billing_cycle(self):
        """
            TO DO:
            - Get default billing cycle from product category when create
            a new product
        """
        default_categ_id = self._get_default_category_id()
        if default_categ_id:
            return self.env['product.category'].browse(
                default_categ_id).billing_cycle

    minimum_register_time = fields.Float(
        string='Minimum Register Time',
        help='Minimum time to register one service. For example, to register'
             ' a domain, the minimum time is one year.',
             default=_get_default_minimum_register_time)
    billing_cycle = fields.Float(
        string='Billing Cycle',
        default=_get_default_billing_cycle)

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        """
            TO DO:
            if is create new product:
                minimum_register_time = categ_id.minimum_register_time
                billing_cycle = categ_id.billing_cycle
        """
        if not self._origin.id and self.categ_id:
            self.minimum_register_time = self.categ_id.minimum_register_time
            self.billing_cycle = self.categ_id.billing_cycle
