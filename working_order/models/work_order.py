# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import Warning

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

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)], limit=1)
        if not types:
            types = type_obj.search([('code', '=', 'internal'), ('warehouse_id', '=', False)])
        return types[:1]

    name = fields.Char('Work Order Name', default=_get_wo_name)
    create_order_time = fields.Datetime('Work Order Time', track_visibility='onchange', readonly=True,
                                        default=fields.Datetime.now)
    done_order_time = fields.Datetime('Work Order Done', track_visibility='onchange', readonly=True)
    work_order_code = fields.Char('Work Order Code', track_visibility='onchange')
    work_order_line_ids = fields.One2many('work.order.line', 'work_order_id')
    user_id = fields.Many2one('res.users', string='User', ondelete='cascade', track_visibility='onchange',
                              default=lambda self: self._uid)
    reason_cancel_id = fields.Many2one('reason.cancel', string='Reason Cancel')
    picking_ids = fields.Many2many('stock.picking', 'work_order_picking_rel', 'work_order_id',
                                      'picking_id', track_visibility='onchange',
                                      string='Picking')
    picking_count = fields.Integer(compute='_compute_picking_count', string="Picking Computation Details")
    sale_order_ids = fields.Many2many('sale.order', 'work_order_sale_order_rel', 'work_order_id',
                                      'sale_order_id', track_visibility='onchange',
                                      string='Sale Order')
    sale_order_line_ids = fields.Many2many('sale.order.line', 'work_order_sale_order_line_rel', 'work_order_id',
                                      'sale_order_line_id', track_visibility='onchange',
                                      string='Sale Order Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    # for create picking
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
                                      default=_default_picking_type,
                                      help="This will determine picking type of incoming shipment")
    @api.multi
    def _compute_picking_count(self):
        for wo in self:
            wo.picking_count = len(wo.picking_ids)

    @api.multi
    def btn_map_sale_order(self):
        work_order_line_obj = self.env['work.order.line']
        for so in self.sale_order_ids:
            for sol in so.order_line:
                if sol.product_id.type == 'product':
                    sol.state_new = 'in progress'
                    for i in range(0, int(sol.product_uom_qty)):
                        work_order_line_obj.create({
                            'sale_order_line_id': sol.id,
                            'sale_order_id': so.id,
                            'work_order_id': self.id,
                            'name': (self.name or '') + (so.name or '') + str(i),
                        })
					
        
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
        old_work_order_line_ids = []
        for i in self.work_order_line_ids:
            old_work_order_line_ids.append(i.sale_order_line_id.id)
        return {'type': 'ir.actions.act_window',
                'name': _('Loading Data'),
                'res_model': 'loading.sale.order',
                'target': 'new',
                'view_mode': 'form',
                'context': {
                    'res_id': self.id,
                    'old_work_order_line_ids': old_work_order_line_ids,
                },
                'views': [[view_id, 'form']],
        }





    @api.multi
    def create_picking(self):
        for wo in self:
            # Get data line
            product_val = {}
            for wol in wo.work_order_line_ids.filtered(lambda r: r.state != 'cancel'):#.mapped('sale_order_line_id'):
                product_id = wol.product_id.id
                if product_id not in product_val:
                    product_val.update({product_id: 1})
                else:
                    product_val[product_id] += 1
            # Create picking
            company_id = wo.company_id.id
            pick = {
                'picking_type_id': wo.picking_type_id.id,
                'origin': wo.name,
                'location_dest_id': wo.picking_type_id.default_location_dest_id.id,
                'location_id': wo.picking_type_id.default_location_src_id.id,
                'company_id': company_id,
            }
            picking = self.env['stock.picking'].create(pick)
            wo.picking_ids =  [(6, 0, [picking.id])]

            product_obj = self.env['product.product']
            move_obj = self.env['stock.move']
            for product_id in product_val:
                product = product_obj.browse(product_id)
                template = {
                    'name': product.name or '',
                    'product_id': product_id,
                    'product_uom_qty': product_val[product_id] or 0.0,
                    'product_uom': product.uom_id.id,
                    'location_dest_id': wo.picking_type_id.default_location_dest_id.id,
                    'location_id': wo.picking_type_id.default_location_src_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': company_id,
                    'picking_type_id': picking.picking_type_id.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }

                move_obj.create(template)
    @api.multi
    def set_to_draft(self):
        self.state = 'draft'
        for i in self.picking_ids:
            if i.state != 'cancel':
                raise Warning('You can not set to draft this work order because picking')
        for i in self.work_order_line_ids:
            if i.state != 'draft':
                raise Warning('You can not set to draft this work order because work order line')
        for wol in self.work_order_line_ids:
            for sol in wol.sale_order_line_id:
                sol.state_new = 'draft'


    @api.multi
    def set_to_in_process(self):
        for wo in self.filtered(lambda m: m.state == 'draft'):
            wo.state= 'in progress'
            for wol in self.work_order_line_ids:
                for sol in wol.sale_order_line_id:
                    sol.state_new = 'in process'
        return

    @api.multi
    def open_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['context'] = {}
        action['domain'] = [('id', 'in', self.picking_ids.ids)]
        return action

class work_order_line(models.Model):
    _name = "work.order.line"




    name = fields.Char('Number Order item', track_visibility='onchange')
    bar_code = fields.Char('Barcode', track_visibility='onchange')
    work_order_id = fields.Many2one('work.order', track_visibility='onchange', string='Work Order')
    sale_order_id = fields.Many2one('sale.order', track_visibility='onchange', string='Sale Order')
    sale_order_line_id = fields.Many2one('sale.order.line', track_visibility='onchange', string='Sale Order Line')
    sale_order_line_id_show = fields.Integer(related='sale_order_line_id.id', string="Order Line Id")
    product_id = fields.Many2one('product.product', track_visibility='onchange', string='Product')
    reason_cancel_id = fields.Many2one('reason.cancel', string='Sale Order')
    stock_move_line_ids = fields.Many2many('stock.move.line', 'stock_move_work_order_rel', 'work_order_id',
                                           'stock_move_id', track_visibility='onchange',
                                           string='Work Order')

    support_barcode_print_color = fields.Char('color', compute='_compute_support_barcode_print')
    support_barcode_print_size = fields.Char('size', compute='_compute_support_barcode_print')
    support_barcode_print_order_date = fields.Char('order_date', compute='_compute_support_barcode_print')
    support_barcode_print_product_code = fields.Char('product_code', compute='_compute_support_barcode_print')
    support_barcode_print_m = fields.Char('M', compute='_compute_support_barcode_print')


    state = fields.Selection([
        ('draft', 'Draft'),		
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    @api.depends('sale_order_line_id', 'sale_order_id', 'product_id')
    def _compute_support_barcode_print(self):

        for line in self:
            color = 'Null'
            size = 'Null'
            for i in line.product_id.attribute_value_ids:
                if i.attribute_id.name == 'Color':
                    color = i.name
                elif i.attribute_id.name == 'Size':
                    size = i.name
            if line.sale_order_id.order_date:
                order_date = str(line.sale_order_id.order_date).split(' ')
                order_date = order_date[0].split('-')
                order_date = order_date[1]+'/'+order_date[2]
            else:
                order_date = 'mm/dd'
            line.support_barcode_print_color = color
            line.support_barcode_print_size = size
            line.support_barcode_print_order_date = order_date
            line.support_barcode_print_product_code = line.product_id.default_code
            line.support_barcode_print_m = line.product_id

        return

    # @api.model
    # def create(self, vals):
    #
    #     vals['bar_code'] = self.env['ir.sequence'].next_by_code('work.order.line') or _('New')
    #     result = super(work_order, self).create(vals)
    #     return result

    @api.multi
    def button_open_cancel_work_order(self):
        view_id = self.env.ref('working_order.view_cancel_work_order_from').id
        return {'type': 'ir.actions.act_window',
                'name': _('Cancel Work Order'),
                'res_model': 'cancel.work.order',
                'target': 'new',
                'view_mode': 'form',
                'context': {
                    'res_id': self.id,
                },
                'views': [[view_id, 'form']],
        }