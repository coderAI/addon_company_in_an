# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare

class ExternalProductCategory(models.AbstractModel):
    _description = 'Import Account for Product Category API'
    _name = 'external.product.category'

    @api.model
    def import_account_product_category(self, code, company_id, vals={}):
        res = {'"code"': 0, '"msg"': '""'}

        # Check type of data
        if not code:
            res['"msg"'] = '"Product Category Code could not be empty"'
            return res
        categ_id = self.env['product.category'].search([('code', '=', code)])
        if not categ_id:
            res['msg'] = "Product Category code not exists."
            return res
        if not company_id:
            res['"msg"'] = '"Company ID could not be empty"'
            return res
        if not self.env['res.company'].browse(company_id):
            res['msg'] = "Company not exists."
            return res
        if not vals:
            return {'"msg"': '"Values could not be empty"'}
        if type(vals) is not dict:
            return {'"msg"': '"Invalid Values"'}

        account_vals = {}
        # list_fields = ['property_account_income_categ_id', 'property_account_expense_categ_id', 'property_renew_account_income_categ_id',
        #                'property_renew_account_expense_categ_id', 'property_register_untaxed_account_income_categ_id', 'property_register_untaxed_account_expense_categ_id',
        #                'property_renew_untaxed_account_income_categ_id', 'property_renew_untaxed_account_expense_categ_id']
        # for field in list_fields:
        #     if not line.get(field):
        #         continue
        #     account_vals.update({field: line[field]})

        if vals.get('property_account_income_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_account_income_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_account_income_categ_id: %s not found."' % vals.get('property_account_income_categ_id', '')}
            account_vals.update({'property_account_income_categ_id': account.id})
        else:
            account_vals.update({'property_account_income_categ_id': False})

        if vals.get('property_account_expense_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_account_expense_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_account_expense_categ_id: %s not found."' % vals.get('property_account_expense_categ_id', '')}
            account_vals.update({'property_account_expense_categ_id': account.id})
        else:
            account_vals.update({'property_account_expense_categ_id': False})

        if vals.get('property_renew_account_income_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_renew_account_income_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_renew_account_income_categ_id: %s not found."' % vals.get('property_renew_account_income_categ_id', '')}
            account_vals.update({'property_renew_account_income_categ_id': account.id})
        else:
            account_vals.update({'property_renew_account_income_categ_id': False})

        if vals.get('property_renew_account_expense_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_renew_account_expense_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_renew_account_expense_categ_id: %s not found."' % vals.get('property_renew_account_expense_categ_id', '')}
            account_vals.update({'property_renew_account_expense_categ_id': account.id})
        else:
            account_vals.update({'property_renew_account_expense_categ_id': False})

        if vals.get('property_register_untaxed_account_income_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_register_untaxed_account_income_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_register_untaxed_account_income_categ_id: %s not found."' % vals.get('property_register_untaxed_account_income_categ_id', '')}
            account_vals.update({'property_register_untaxed_account_income_categ_id': account.id})
        else:
            account_vals.update({'property_register_untaxed_account_income_categ_id': False})

        if vals.get('property_register_untaxed_account_expense_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_register_untaxed_account_expense_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_register_untaxed_account_expense_categ_id: %s not found."' % vals.get('property_register_untaxed_account_expense_categ_id', '')}
            account_vals.update({'property_register_untaxed_account_expense_categ_id': account.id})
        else:
            account_vals.update({'property_register_untaxed_account_expense_categ_id': False})

        if vals.get('property_renew_untaxed_account_income_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_renew_untaxed_account_income_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_renew_untaxed_account_income_categ_id: %s not found."' % vals.get('property_renew_untaxed_account_income_categ_id', '')}
            account_vals.update({'property_renew_untaxed_account_income_categ_id': account.id})
        else:
            account_vals.update({'property_renew_untaxed_account_income_categ_id': False})

        if vals.get('property_renew_untaxed_account_expense_categ_id', ''):
            account = self.env['account.account'].search([('code', '=', vals.get('property_renew_untaxed_account_expense_categ_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"property_renew_untaxed_account_expense_categ_id: %s not found."' % vals.get('property_renew_untaxed_account_expense_categ_id', '')}
            account_vals.update({'property_renew_untaxed_account_expense_categ_id': account.id})
        else:
            account_vals.update({'property_renew_untaxed_account_expense_categ_id': False})

        # Update Analytic Account
        if vals.get('register_analytic_income_acc_id', ''):
            account = self.env['account.analytic.account'].with_context(force_company=company_id).search([('code', '=', vals.get('register_analytic_income_acc_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"register_analytic_income_acc_id: %s not found."' % vals.get('register_analytic_income_acc_id', '')}
            account_vals.update({'register_analytic_income_acc_id': account.id})
        else:
            account_vals.update({'register_analytic_income_acc_id': False})

        if vals.get('register_analytic_expense_acc_id', ''):
            account = self.env['account.analytic.account'].with_context(force_company=company_id).search([('code', '=', vals.get('register_analytic_expense_acc_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"register_analytic_expense_acc_id: %s not found."' % vals.get('register_analytic_expense_acc_id', '')}
            account_vals.update({'register_analytic_expense_acc_id': account.id})
        else:
            account_vals.update({'register_analytic_expense_acc_id': False})

        if vals.get('renew_analytic_income_account_id', ''):
            account = self.env['account.analytic.account'].with_context(force_company=company_id).search([('code', '=', vals.get('renew_analytic_income_account_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"renew_analytic_income_account_id: %s not found."' % vals.get('renew_analytic_income_account_id', '')}
            account_vals.update({'renew_analytic_income_account_id': account.id})
        else:
            account_vals.update({'renew_analytic_income_account_id': False})

        if vals.get('renew_analytic_expense_account_id', ''):
            account = self.env['account.analytic.account'].with_context(force_company=company_id).search([('code', '=', vals.get('renew_analytic_expense_account_id', '')), ('company_id', '=', company_id)])
            if not account:
                return {'"msg"': '"renew_analytic_expense_account_id: %s not found."' % vals.get('renew_analytic_expense_account_id', '')}
            account_vals.update({'renew_analytic_expense_account_id': account.id})
        else:
            account_vals.update({'renew_analytic_expense_account_id': False})

        # Update Account for Product Category
        categ_id.with_context(force_company=company_id).write(account_vals)
        res['"code"'] = 1
        return res

    @api.model
    def get_product_category(self, categ_id):
        res = {'"code"': 0, '"msg"': '""', '"data"': {}}
        ProductCategory = self.env['product.category']
        data = {}

        # Check partner
        if not categ_id or type(categ_id) is not int:
            res.update({'"msg"': '"Product Category ID could be not empty and it is number."'})
            return res
        product_category_id = ProductCategory.browse(categ_id)
        if not product_category_id:
            res.update({'"msg"': '"Product Category not found."'})
            return res

        # If arguments are ok
        try:
            data.update({
                '"code"': '\"' + (product_category_id.code or '') + '\"',
                '"name"': '\"' + (product_category_id.name or '') + '\"',
            })
            res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        except:
            res['msg'] = '"Can not get product category"'
            return res
        return res

    @api.model
    def get_product_category_all(self):
        res = {'"code"': 0, '"msg"': '""', '"data"': []}
        ProductCategory = self.env['product.category']
	product_category_ids = ProductCategory.search([])

        # If arguments are ok
        data = []
        for product_category_id in product_category_ids:
	    data.append({'"code"': '\"' + (product_category_id.code or '') + '\"', '"name"': '\"' + (product_category_id.name or '') + '\"', '"uom_name"': '\"' + (product_category_id.uom_id.name or '') + '\"', '"price_setup_vendor"': str(product_category_id.setup_price_vendor or 0), '"price_renew_vendor"': str(product_category_id.renew_price_vendor or 0), '"setup_price_mb"': str(product_category_id.setup_price_mb or 0), '"renew_price_mb"': str(product_category_id.renew_price_mb or 0), '"default_tax"': '\"' + (product_category_id.default_tax or '') + '\"', '"price_promotion_register"': str(product_category_id.promotion_register_price or 0), '"price_promotion_renew"': str(product_category_id.promotion_renew_price or 0) })
	    res.update({'"code"': 1, '"msg"': '"Successfully"', '"data"': data})
        return res
