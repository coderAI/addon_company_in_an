# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging as _logger

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def update_lot_serial_number(self):
        self.ensure_one()
        new_line = []
        for line in self.line_ids.filtered(lambda l: l.product_qty > 0 and not l.prod_lot_id and l.product_id.tracking <> 'none'):
            quantity = line.product_qty
            while quantity > 0:
                lot_id = self.env['stock.production.lot'].sudo().create({
                    'name': self.env['ir.sequence'].next_by_code('stock.lot.serial'),
                    'product_id': line.product_id and line.product_id.id,
                })
                new_line.append((0, 0, {
                    'product_id': line.product_id and line.product_id.id,
                    'product_uom_id': line.product_uom_id and line.product_uom_id.id,
                    'prod_lot_id': lot_id.id,
                    'location_id': line.location_id and line.location_id.id,
                    'product_qty': 1
                }))
                quantity -= 1
            line.sudo().unlink()
        if new_line:
            self.line_ids = new_line


