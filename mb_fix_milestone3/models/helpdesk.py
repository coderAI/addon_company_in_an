# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger

class HelpDesk(models.Model):
    _inherit = 'helpdesk.ticket'


    @api.multi
    def write(self, vals):
        if vals.get('user_id'):
            helpdesk_stage_obj = self.env['helpdesk.stage']
            if self.team_id.name == 'Support MATBAO':
                stage_id = helpdesk_stage_obj.search([('name', '=', 'InProgress-MB')], limit=1)
                if stage_id:
                    vals['stage_id'] = stage_id.id
            elif self.team_id.name == 'Support CHILI':
                stage_id = helpdesk_stage_obj.search([('name', '=', 'InProgress-CHILI')], limit=1)
                if stage_id:
                    vals['stage_id'] = stage_id.id
            else:
                stage_id = helpdesk_stage_obj.search([('name', '=', 'InProgress')], limit=1)
                if stage_id:
                    vals['stage_id'] = stage_id.id
        return super(HelpDesk, self).write(vals)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.depends('res_id', 'model')
    def get_rating_url(self):
        a=1
        # for mes in self:
        #     mes.access_token = False
        #     if mes.model == 'helpdesk.ticket' and mes.res_id:
        #         ticket_id = self.env['helpdesk.ticket'].browse(mes.res_id)
        #         if ticket_id.access_token and ticket_id.partner_id and ticket_id.team_id and ticket_id.team_id.name == 'Support MATBAO':
        #             mes.rating_url = "https://managed.matbao.com/viewticket/%s/%s" % (ticket_id.access_token, mes.res_id)


    rating_url = fields.Char('Rating URL', compute='get_rating_url', store=True)
