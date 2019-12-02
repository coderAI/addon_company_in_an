# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class reason_cancel(models.Model):
    _name = 'reason.cancel'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class store_info(models.Model):
    _name = 'store.info'
    _inherit = 'reason.cancel'


class market_place(models.Model):
    _name = 'market.place'
    _inherit = 'reason.cancel'


class delivery_method(models.Model):
    _name = 'delivery.method'
    _inherit = 'reason.cancel'


class platfrom_list(models.Model):
    _name = 'platfrom.list'
    _inherit = 'reason.cancel'


class work_order(models.Model):
    _name = "work.order"

    name = fields.Char('Work Order Name')
    create_order_time = fields.Datetime('Work Order Time', readonly=True)
    done_order_time = fields.Datetime('Work Order Done', readonly=True)
    work_order_code = fields.Char('Work Order Code')
    work_order_line_ids = fields.One2many('work.order.line', 'work_order_id')
    user_id = fields.Many2one('res.users', string='User', ondelete='cascade', default=lambda self: self._uid)
    picking_id = fields.Many2one('stock.picking', string='Piking')
    sale_order_ids = fields.Many2many('sale.order', 'work_order_sale_order_rel', 'work_order_id',
                                           'sale_order_id',
                                           string='Sale Order')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


    @api.multi
    def btn_map_sale_order(self):
        work_order_line_obj = self.env['work.order.line']
        for so in self.sale_order_ids:
            for sol in so.order_line:
                if sol.product_id.type == 'product':
                    for i in range(1,int(sol.product_uom_qty)):
                        work_order_line_obj.create({
                            'sale_order_line_id':sol.id,
                            'sale_order_id':so.id,
                            'work_order_id': self.id,
                            'name': (self.name or '')+(so.name or '')+str(i),
                        })
        self.state='in progress'

        return

class work_order_line(models.Model):
    _name = "work.order.line"

    name = fields.Char('Number Order item')
    bar_code = fields.Char('Barcode')
    work_order_id = fields.Many2one('work.order', string='Work Order')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    reason_cancel_id = fields.Many2one('reason.cancel', string='Sale Order')
    stock_move_line_ids = fields.Many2many('stock.move.line', 'stock_move_work_order_rel', 'work_order_id',
                                           'stock_move_id',
                                           string='Work Order')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


