# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def default_get(self, fields_list):
        defaults = super(AccountAnalyticLine, self).default_get(fields_list)
        if self._context.get('default_project_id'):
            project_id = self.env['project.project'].browse(self._context.get('default_project_id'))
            if project_id:
                defaults.setdefault('account_id', project_id.analytic_account_id.id)
                defaults.setdefault('company_id', project_id.analytic_account_id.company_id.id)
        return defaults
    
    @api.model
    def create(self, vals):
        # _logger.info("--------------------- %s -----------------------" % vals)
        return super(AccountAnalyticLine, self).create(vals)
