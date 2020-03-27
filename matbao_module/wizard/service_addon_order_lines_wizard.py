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
from odoo.exceptions import Warning
import urllib2
import urllib
import json
from lxml import etree

class ServiceAddonOrderLinesWizard(models.TransientModel):
    _name = "service.addon.order.lines.wizard"
    _description = "Wizard to add services/addons to the current active SO"

    line_ids = fields.One2many(
        'order.lines.wizard', 'parent_id', string='Order Lines')





    def create_product_when_add_service(self,line,is_add_service):
        # ---------------------- Edit and add by Hai 16/10/2017 ---------------------#
        if line.get_parent_product_category(line.product_category_id).code == 'CHILI' and is_add_service:
            full_url = 'http://core.matbao.net/getdomainchili.aspx?domain=' + line.product_name.strip()
            res_data = urllib2.urlopen(full_url)
            res_data = res_data.read()
            line.product_name = res_data
        # ----------------------- end ------------------------#

        product_data = {
            'name': is_add_service and line.product_name.lower().strip() or line.parent_product_id.name.strip(),
            'type': 'service',
            'categ_id': line.product_category_id.id,
            'minimum_register_time': line.product_category_id.minimum_register_time,
            'billing_cycle': line.product_category_id.billing_cycle,
            'uom_id': line.product_category_id.uom_id.id,
            'uom_po_id': line.product_category_id.uom_id.id,
            'parent_product_id': is_add_service and False or line.parent_product_id.id
        }
        res =  self.env['product.product'].create(product_data)
        return res.id



    @api.multi
    def get_line_values(self, line):
        vals = {
            'register_type': line.register_type,
            'product_category_id': line.product_category_id.id,
            'time': line.time,
            'product_uom': line.product_category_id.uom_id.id,
            'template': line.template,
        }
        return vals

    @api.multi
    def write_service_orders(self):
        self.ensure_one()
        if self._context.get('active_model') != 'sale.order':
            return False

        order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(order_id)
        lines = []

        for line in self.line_ids:
            product_uom = line.product_category_id.uom_id.id
            if not product_uom:
                raise Warning(_("Please set UOM for Product Category!"))

            vals = self.get_line_values(line)

            # product_id = None
            # product_name = None
            is_add_service = self._context.get('service')
            if line.register_type in ['register', 'transfer']:
                if line.product_id.id:
                    product_id = line.product_id.id
                    product_name = line.product_id.name.strip()
                else:
                    product_id = self.create_product_when_add_service(line, is_add_service)
                    product_name = is_add_service and line.product_name.strip() or \
                                   line.parent_product_id.name.strip()
            else:
                product_id = line.product_id.id
                product_name = line.product_id.name.strip()
                this_sale_order = self.env['sale.order'].browse(line._context.get('sale_order_id',False))  #
                template ='1'
                if this_sale_order:
                    sale_service_data = self.env['sale.service'].search(
                        [('product_id', '=', product_id), ('customer_id', '=', this_sale_order.partner_id.id)],
                        limit=1)
                    for i in sale_service_data:
                        if i.license:
                            template= i.license or '1'

                vals.update({
                            'license': template
                        })

            vals.update({
                'product_id': product_id,

                'name': product_name.lower().strip(),
                'parent_product_id': is_add_service and False or line.parent_product_id.id
            })

            lines.append((0, 0, vals))
        if lines:
            order.write({'order_line': lines})
