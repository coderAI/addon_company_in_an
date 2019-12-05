# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class check_product(models.Model):
    _name = 'check.product'

    name = fields.Char('Name')
    active = fields.Boolean('Active',default=True)
    sale_order_line_ids = fields.One2many('sale.order.line', 'check_product_id')
    user_id = fields.Many2one('res.users', 'User',default=lambda self: self.env.user)
    maximum_sale_order_line = fields.Integer('Limit Sale Order Line')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')


    @api.multi
    def btn_map_sale_order_line(self):
        sale_order_line_obj = self.env['sale.order.line']
        sale_order_line = sale_order_line_obj.search([('order_id.state','=','paid'),('check_maped','=',False)], order="id asc")
        for line in sale_order_line:
            line.check_maped=True
            line.check_product_id=self.id
            line.state=self.id

            #checking anything and add to check product


