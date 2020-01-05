# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    customer_type = fields.Selection([('personal', 'Personal'), ('acgency', 'Acgency')], default='personal')
    reference = fields.Char('Reference')
    # tax_code = fields.Char('Tax Code')
    # job_title = fields.Char('Tax Code')
    # sub_name = fields.Char('Tax Code')
    @api.model
    def create(self, vals):
        vals['reference'] = self.env['ir.sequence'].next_by_code('res.partner') or _('New')
            
        result = super(Partner, self).create(vals)
        return result