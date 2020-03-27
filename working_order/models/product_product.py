# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class product_product(models.Model):
    _inherit = "product.product"

    minimum_quantity = fields.Integer('Minimum quantity')

