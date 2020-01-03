# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning

class sale_order(models.Model):
    _inherit = "sale.order"

    coupon_code = fields.Char('Coupon Code')
    # orther information
    payment_method = fields.Char('Payment Method')
    order_date = fields.Datetime('Order Date')
    transaction_id = fields.Char('Transaction ID')
    order_ip = fields.Char('Order IP')
    tracking_number = fields.Char('Tracking Number')
    order_shipping_location = fields.Char('Order Shipping Location')
    #
    store_id = fields.Many2one('store.info', string='Store')
    market_place_id = fields.Many2one('market.place', string='Market Place')

    platform_id = fields.Many2one('platform.list', string='Platform')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Confirm'),
        ('paid', 'Paid'),
        ('product hold', 'Product Hold'),
        ('in product', 'In Product'),
        ('to delivery', 'To Delivery'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        # self._action_confirm()
        # if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
        #     self.action_done()
        return True

    @api.multi
    def action_set_to_paid(self):
        for so in self:
            so.write({'state': 'paid'})

    @api.multi
    def action_set_to_done(self):
        for so in self:
            so.write({'state': 'done'})

    @api.multi
    def action_set_to_delivery(self):
        for so in self:
            # self._action_confirm()
            # create picking
            type_obj = self.env['stock.picking.type']
            company_id = so.company_id.id
            types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)], limit=1)
            if not types:
                types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
            picking_type = types[:1]
            location_dest_id = picking_type.default_location_dest_id.id or so.partner_id.property_stock_customer and so.partner_id.property_stock_customer.id or False
            pick = {
                'partner_id': so.partner_id.id,
                'picking_type_id': picking_type.id,
                'origin': so.name,
                'sale_id': so.id,
                'location_dest_id': location_dest_id,
                'location_id': picking_type.default_location_src_id.id,
                'company_id': company_id,
            }
            picking = self.env['stock.picking'].create(pick)

            product_obj = self.env['product.product']
            move_obj = self.env['stock.move']
            for so_line in so.order_line:
                product = so_line.product_id
                template = {
                    'name': product.name or '',
                    'product_id': product.id,
                    'product_uom_qty': so_line.product_uom_qty or 0.0,
                    'product_uom': product.uom_id.id,
                    'location_dest_id': location_dest_id,
                    'location_id': picking_type.default_location_src_id.id or False,
                    'sale_line_id': so_line.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': company_id,
                    'picking_type_id': picking.picking_type_id.id,
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }

                move_obj.create(template)

            #####
            so.write({'state': 'to delivery'})
            so.picking_ids = [(6, 0, [picking.id])]
            # if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            # self.action_done()
        return True


class ir_attachment(models.Model):
    _inherit = "ir.attachment"
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')



class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    attachment_ids = fields.One2many('ir.attachment', 'sale_order_line_id',
                                     string='Attachments')
    check_product_id = fields.Many2one('check.product', string='check product')
    check_maped = fields.Boolean(string='Map Check Product', default=False)
    description = fields.Char('Description')
    side_to_print = fields.Selection([
        ('front', 'Front'),
        ('backside', 'Backside'),
        ('in both sides', 'In Both Sides')
    ], string='Side to Print', track_visibility='onchange', default='front')
    state_new = fields.Selection([
        ('draft', 'Draft'),
        ('in process', 'In Process'),
        ('done', 'Done')
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def btn_img(self):
        view_id = self.env.ref('working_order.view_sale_order_line_imgae_from', False)
        return {
            'name': _('Image From'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'view_id': view_id.id,
            'target': 'new',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
        }
