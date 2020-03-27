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
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        ctx = self._context
        SaleService = self.env['sale.service']
        ProductCategory = self.env['product.category']
        SaleOrder = self.env['sale.order']

        if ctx.get('in_service'):
            _ids = []
            if ctx.get('order_id'):
                # Add services
                order = SaleOrder.browse(ctx['order_id'])
                domain = [('status', '=', 'active'),
                          ('customer_id', '=', order.partner_id.id)]

                if ctx.get('is_service') or ctx.get('is_parent'):
                    # Allow select services that active or same order line
                    domain += [('parent_product_id', '=', False)]
                    services = SaleService.search(domain)
                    _ids = services.mapped('product_id.id')
                    lines = order.order_line.filtered(lambda r:
                                                      not r.parent_product_id)
                    _ids += lines.mapped('product_id.id')
                    args += [('id', 'in', _ids)]
                else:
                    # Filter addons services that active
                    domain += [('parent_product_id', '!=', False)]
                    services = SaleService.search(domain)
                    _ids = services.mapped('product_id.id')
                    args += [('id', 'in', _ids)]

                # Filter by product categories
                prod_categ_id = ctx.get('product_category_id')
                if ctx.get('is_parent'):
                    # Add parent service
                    parent_categ_ids = ProductCategory.search([
                            ('id', 'parent_of', prod_categ_id)])
                    args += [('categ_id', 'child_of', parent_categ_ids.ids)]
                else:
                    args += [('categ_id', '=', prod_categ_id or [-1])]

            elif 'product_category_id' in ctx:
                if ctx.get('product_category_id'):
                    _ids = self.search(
                        [('categ_id', '=', ctx['product_category_id'])]).ids
                    args += [('id', 'in', _ids)]
                else:
                    args += [('id', 'in', [-1])]

        res = super(ProductProduct, self).name_search(name, args=args,
                                                      operator=operator,
                                                      limit=limit)
        return res

    @api.model
    def create(self, vals):
        IrSequence = self.env['ir.sequence']
        if not vals.get('default_code'):
            vals.update({
                'default_code': IrSequence.next_by_code('product.product')
            })
        return super(ProductProduct, self).create(vals)
