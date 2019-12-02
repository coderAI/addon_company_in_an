# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class sale_order(models.Model):
    _inherit = "sale.order"

    coupon_code = fields.Char('Coupon Code')
    # orther information
    payment_menthod = fields.Char('Payment Menthod')
    transaction_id = fields.Char('Transaction Id')
    order_ip = fields.Char('Order Ip')
    tracking_number = fields.Char('Tracking Number')
    order_shipping_location = fields.Char('Order Shipping Location')
    #
    store_id = fields.Many2one('store.info', string='Store')
    market_place_id = fields.Many2one('market.place', string='Market Place')
    delivery_method_id = fields.Many2one('delivery.method', string='Delivery Method')
    platfrom_id = fields.Many2one('platfrom.list', string='Platfrom')
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('paid', 'Paid'),
        ('product hold', 'Product Hold'),
        ('in product', 'In Product'),
        ('to delivery', 'To Delivery'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    attachment_ids = fields.Many2many('ir.attachment', 'sale_order_line_ir_attachments_rel',
                                      'order_line', 'attachment_id', string='Attachments')
    description = fields.Char('Description')


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
            'type': 'ir.actions.act_window',
        }