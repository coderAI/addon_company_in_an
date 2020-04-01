# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime


class ResPartner(models.Model):
    _inherit = "res.partner"

    mobile_show = fields.Char(related='mobile')
    email_show = fields.Char(related='email')

    @api.onchange('mobile_show')
    def onchange_mobile_show(self):
        if not self.mobile_show:
            return
        else:
            self.mobile = self.mobile_show

    @api.onchange('email_show')
    def onchange_email_show(self):
        if not self.email_show:
            return
        else:
            self.email = self.email_show

    @api.model
    def save_view_mobile_stories(self, id):
        partner_history_env = self.env['res.partner.history']
        type_env = self.env['mb.data.contact.type']
        type_obj = type_env.search([('code', '=', 'customer')])
        info_val = {'customer_id': id,
                    'user_id': self.env.uid,
                    'time_view': datetime.now(),
                    'info_view': 'Mobile',
                    'type_id': type_obj and type_obj.id or False}
        partner_history_env.create(info_val)

    @api.model
    def save_view_email_stories(self, id):
        partner_history_env = self.env['res.partner.history']
        type_env = self.env['mb.data.contact.type']
        type_obj = type_env.search([('code', '=', 'customer')])
        info_val = {'customer_id': id,
                    'user_id': self.env.uid,
                    'time_view': datetime.now(),
                    'info_view': 'Email',
                    'type_id': type_obj and type_obj.id or False}
        partner_history_env.create(info_val)

    @api.model
    def save_view_mobile_stories_wizard(self, type, parent_id):
        partner_history_env = self.env['res.partner.history']
        type_env = self.env['mb.data.contact.type']
        type_obj = False
        if type:
            type_obj = type_env.search([('code', '=', type)])
        info_val = {'customer_id': parent_id,
                    'user_id': self.env.uid,
                    'time_view': datetime.now(),
                    'info_view': 'Mobile',
                    'type_id': type_obj and type_obj.id or False}
        partner_history_env.create(info_val)

    @api.model
    def save_view_email_stories_wizard(self, type, parent_id):
        partner_history_env = self.env['res.partner.history']
        type_env = self.env['mb.data.contact.type']
        type_obj = type_env.search([('code', '=', type)])
        info_val = {'customer_id': parent_id,
                    'user_id': self.env.uid,
                    'time_view': datetime.now(),
                    'info_view': 'Email',
                    'type_id': type_obj and type_obj.id or False}
        partner_history_env.create(info_val)
