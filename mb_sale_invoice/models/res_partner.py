# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class Partner(models.Model):
    _inherit = "res.partner"

    mobile_show = fields.Char(related='mobile', string="Mobile Show")
    email_show = fields.Char(related='email', string="Email Show")
    info_types_organization = fields.Many2one('mb.data.contact.type', string='Info Types Organization')
    sale_warn = fields.Selection(string='Sales Order Warn')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('edited', 'Edited'),
        ('waiting_for_approval', "Waiting for Approval"),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], default='draft', readonly=True, string='Status')
    microsoft_customer_id = fields.Char('Microsoft Customer ID')
    phone_history_ids = fields.Many2many(
        'sale.phone.history', 'partner_history_rel', 'partner_id', 'history_id', string='Phone History')

    @api.multi
    def button_submit_to_operation(self):
        customer = self.sudo().filtered(lambda c: c.state in ('draft', 'edited'))
        if customer:
            customer.write({'state': 'waiting_for_approval'})
        return True

    @api.multi
    def write(self, vals):
        if not self.user_has_groups('account.group_account_invoice') \
           and not self.user_has_groups('base.group_system') \
           and not self.user_has_groups('mb_sale_contract.group_operator_mb_sale_contract') \
           and not self.user_has_groups('sales_team.group_sale_manager') \
           and not self.user_has_groups('mb_fix_milestone.group_sale_support'):
            for cus in self:
                if len(vals.keys()) == 1:
                    for i in vals.keys():
                        if i == 'category_2_id' or i == 'gender':
                            return super(Partner, self).write(vals)
                if self.user_has_groups('mb_sale_contract.group_sale_online_mb_sale_contract') and \
                   ((not cus.parent_id and cus.state in ('waiting_for_approval', 'approved'))
                       or (cus.parent_id and cus.parent_id.state in ('waiting_for_approval', 'approved'))):
                   raise Warning(_("You can't update info customer and contact, pls contact Operator."))
                if not self.user_has_groups('mb_sale_contract.group_sale_online_mb_sale_contract') and \
                   ((not cus.parent_id and cus.state in ('edited', 'waiting_for_approval', 'approved'))
                       or (cus.parent_id and cus.parent_id.state in ('edited', 'waiting_for_approval', 'approved'))):

                   raise Warning(_("You can't update info customer and contact, pls contact Operator/ Sale Online."))

        return super(Partner, self).write(vals)

    @api.multi
    def generate_code(self):
        if self.ref:
            ref = self.get_ref_partner()
            if ref:
                self.write({
                    'ref': ref
                })
