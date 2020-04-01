# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api
from odoo.exceptions import Warning

class add_product_category_config(models.Model):
    _name = 'add.product.category.config'


    product_category_id = fields.Many2one('product.category',string="Product", required=True)
    product_category_ids = fields.Many2many('product.category', 'add_product_category_config_product_category_rel', 'add_product_category_config_id', 'product_category_id', string='Product List')
    active = fields.Boolean(string="Active" , default=True)

    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        res={}
        domain={}
        if self.product_category_id:
            domain['product_category_ids'] = [('id', '!=', self.product_category_id.id)]
            res = {'domain': domain}
        return res


    def check_product(self,product_category_id):
        if product_category_id:
            if self.search([('product_category_id','=',product_category_id)],limit=1).ids:
                raise Warning("You cannot configure an object twice")

    @api.model
    def create(self, vals):
        self.check_product(vals.get('product_category_id'))
        return super(add_product_category_config, self).create(vals)

    @api.multi
    def _write(self, vals):
        self.check_product(vals.get('product_category_id'))
        return super(add_product_category_config, self)._write(vals)