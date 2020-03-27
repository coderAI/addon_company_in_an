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
from odoo.tools.float_utils import float_compare
from lxml import etree
from odoo.exceptions import Warning


class OrderLinesWizard(models.TransientModel):
    _name = "order.lines.wizard"
    _description = "a sales order line in service.addon.order.lines.wizard"

    parent_id = fields.Many2one('service.addon.order.lines.wizard', 'Parent')
    test = fields.Boolean(string="test bool", default=False)
    is_service = fields.Boolean(string="is Service product")
    register_type = fields.Selection(
        string="Register Type",
        selection=[('register', 'Register'),
                   ('renew', 'Renew'),
                   ('transfer', 'Transfer')],
        required=True)
    product_category_id = fields.Many2one(
        'product.category', string="Product Category", required=True)
    product_id = fields.Many2one(
        "product.product", string="Product")
    product_name = fields.Char(
        string="Product Name")
    time = fields.Float(string="Time", required=True)
    product_uom_id = fields.Many2one('product.uom', string="UOM")
    parent_product_id = fields.Many2one(
        'product.product', string="Parent Service")
    template = fields.Char(string='Template',register_type={'renew': [('readonly', True)]})




    @api.onchange('register_type', 'product_category_id', 'product_id', 'time')
    def _onchange_product_id(self):
        self.ensure_one()
        prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        if self.product_category_id:
            self.product_uom_id = self.product_category_id.uom_id
            if self.product_id.categ_id.id != self.product_category_id.id:
                self.product_id = False
        if self.product_id:
            self.product_name = self.product_id.name
            this_sale_order = self.env['sale.order'].browse(self.env.context.get('order_id'))
            sale_service_data = self.env['sale.service'].search([('product_id','=',self.product_id.id),('customer_id','=',this_sale_order.partner_id.id)], limit=1)
            for i in sale_service_data:
                if i.license:
                    self.template = str(i.license)
                else:
                    self.template = '1'

        if self.register_type:
            min_qty = 0.0
            # Get Time from product category: 23/01/2018
            if self.register_type in ['register', 'transfer', 'upgrade'] and self.product_category_id:
                min_qty = self.product_category_id.minimum_register_time
            elif self.register_type != 'register' and self.product_id:
                min_qty = self.product_category_id.billing_cycle
            if float_compare(self.time, min_qty, prec) < 0:
                self.time = min_qty

