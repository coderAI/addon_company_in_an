# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import Warning



class PartnerCategory(models.Model):
    _inherit = 'res.partner.category'
    _order = 'sequence'

    @api.model
    def _get_count_customer(self):
        for i in self:
            i.customer_count = self.env['res.partner'].search_count([("category_2_id", "=", i.id)])

    sequence = fields.Integer(default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    is_career = fields.Boolean(string="Career")
    customer_count = fields.Integer('count',compute='_get_count_customer')



    @api.onchange('is_career')
    def onchange_parent_id(self):
        if self.is_career:
            domain = {'parent_id': [('is_career', '=', True)]}
        else:
            domain = {'parent_id': [('is_career', '!=', True)]}
        res = {}
        if domain:
            res['domain'] = domain
        return res


    @api.multi
    def btn_view_partner(self):

            return {
                "type": "ir.actions.act_window",
                "res_model": "res.partner",
                "views": [[self.env.ref('matbao_module.view_res_partner_tree_inherit').id, "tree"],
                          [self.env.ref('matbao_module.view_res_partner_form_inherit').id, "form"]],
                "domain": [["id", "in", self.env['res.partner'].search([("category_2_id", "=", self.id)]).ids]],

                "context": {"create": False, },
                "name": "Customer list",
            }

class ResPartner(models.Model):
    _inherit = 'res.partner'
    category_2_id = fields.Many2many('res.partner.category','category_2_res_partner__rel', 'res_partner_id', 'category_2_id' ,string='Tags')

    @api.multi
    def write(self, values):
        if values.get('phone'):
            if len(values.get('phone')) < 7:
                raise Warning('Minium Phone number 10')
        if values.get('mobile'):
            if len(values.get('mobile')) < 7:
                raise Warning('Minium Phone number 10')
        return super(ResPartner, self).write(values)