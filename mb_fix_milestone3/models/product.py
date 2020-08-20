# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging as _logger

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.multi
    def get_parent_product_category(self, categ_id):
        # self.ensure_one()
        if categ_id and categ_id.parent_id:
            return self.get_parent_product_category(categ_id.parent_id)
        else:
            return categ_id

    @api.model
    def get_list_addons_idpage(self):
        addons_ids = self.search([('is_addons', '=', True), ('sold', '=', True)])
        if not addons_ids:
            return {'"code"': 0, '"msg"': '"No data"'}
        data = []
        try:
            for addon in addons_ids:
                parent = self.get_parent_product_category(addon)
                if parent and parent.code <> 'CHILI':
                    data.append({
                        '"name"': '"%s"' % addon.name,
                        '"code"': '"%s"' % (addon.code or ''),
                        '"erm_code"': '"%s"' % (addon.erm_code or ''),
                        '"minimum_register_time"': addon.minimum_register_time or 0,
                        '"billing_cycle"': addon.billing_cycle or 0,
                        '"to_be_renewed"': '"%s"' % (addon.to_be_renewed and 'True' or 'False'),
                        '"uom"': '"%s"' % (addon.uom_id and addon.uom_id.name or ''),
                        '"parent_id"': '"%s"' % (addon.parent_id and addon.parent_id.name or ''),
                    })
            return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Error: %s"' % (e.message or repr(e))}

