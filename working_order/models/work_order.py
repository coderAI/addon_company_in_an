# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class reason_cancel(models.Model):
    _name = 'reason.cancel'
    _description = 'Reason Cancel'
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
    _name = 'platform.list'
    _inherit = 'reason.cancel'


class work_order(models.Model):
    _name = "work.order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _get_wo_name(self):
        return self.env['ir.sequence'].next_by_code('work.order') or _('New')

    name = fields.Char('Work Order Name', default=_get_wo_name)
    create_order_time = fields.Datetime('Work Order Time', track_visibility='onchange', readonly=True,
                                        default=fields.Datetime.now)
    done_order_time = fields.Datetime('Work Order Done', track_visibility='onchange', readonly=True)
    work_order_code = fields.Char('Work Order Code', track_visibility='onchange')
    work_order_line_ids = fields.One2many('work.order.line', 'work_order_id')
    user_id = fields.Many2one('res.users', string='User', ondelete='cascade', track_visibility='onchange',
                              default=lambda self: self._uid)
    picking_id = fields.Many2one('stock.picking', track_visibility='onchange', string='Piking')
    sale_order_ids = fields.Many2many('sale.order', 'work_order_sale_order_rel', 'work_order_id',
                                      'sale_order_id', track_visibility='onchange',
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
                    for i in range(0, int(sol.product_uom_qty)):
                        work_order_line_obj.create({
                            'sale_order_line_id': sol.id,
                            'sale_order_id': so.id,
                            'work_order_id': self.id,
                            'name': (self.name or '') + (so.name or '') + str(i),
                        })
        self.state = 'in progress'
        return

    @api.model
    def create(self, vals):
        # if vals.get('name', _('New')) == _('New'):
        #     vals['name'] = self.env['ir.sequence'].next_by_code('work.order') or _('New')
        result = super(work_order, self).create(vals)
        return result

    @api.multi
    def button_open_loading_sale_order(self):
        view_id = self.env.ref('working_order.view_loading_sale_order_from').id
        return {'type': 'ir.actions.act_window',
                'name': _('Loading Data'),
                'res_model': 'loading.sale.order',
                'target': 'new',
                'view_mode': 'form',
                'context': {
                    'res_id': self.id,
                },
                'views': [[view_id, 'form']],
        }

class work_order_line(models.Model):
    _name = "work.order.line"

    name = fields.Char('Number Order item', track_visibility='onchange')
    bar_code = fields.Char('Barcode', track_visibility='onchange')
    work_order_id = fields.Many2one('work.order', track_visibility='onchange', string='Work Order')
    sale_order_id = fields.Many2one('sale.order', track_visibility='onchange', string='Sale Order')
    sale_order_line_id = fields.Many2one('sale.order.line', track_visibility='onchange', string='Sale Order Line')
    product_id = fields.Many2one('product.product', track_visibility='onchange', string='Product')
    reason_cancel_id = fields.Many2one('reason.cancel', string='Sale Order')
    stock_move_line_ids = fields.Many2many('stock.move.line', 'stock_move_work_order_rel', 'work_order_id',
                                           'stock_move_id', track_visibility='onchange',
                                           string='Work Order')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')



