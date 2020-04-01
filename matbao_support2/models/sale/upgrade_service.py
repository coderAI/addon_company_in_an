# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, SUPERUSER_ID


class MBUpgradeService(models.Model):
    _inherit = "mb.upgrade.service"

    @api.multi
    def action_send_request(self):
        ir_values_env = self.env['ir.values']
        upgrades = self.filtered(lambda l: l.state == 'draft')
        for record in upgrades:
            template = self.env.ref(
                'matbao_support2.upgrade_service_template')
            us_email = ir_values_env.get_default(
                'sale.config.settings', 'upgrade_service') or ''
            email_to_lst = []
            if us_email:
                email_to_lst = us_email.split(';')
                email_to_lst = ','.join(email_to_lst)
            template.send_mail(res_id=record.id, force_send=True,
                               email_values={
                'email_from': '%s <%s>' % (self.company_id.name,self.company_id.email),
                'email_to': email_to_lst})
        rs = super(MBUpgradeService, self).action_send_request()
        return rs


