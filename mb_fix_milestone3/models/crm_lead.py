# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
import logging as _logger
from datetime import timedelta, date
from odoo.exceptions import UserError, ValidationError

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def retrieve_sales_dashboard(self):
        result = super(CRMLead, self).retrieve_sales_dashboard()
        opportunities = self.search([('type', '=', 'opportunity'), ('user_id', '=', self._uid), ('probability', '!=', 100), ('active', '=', True)])
        for opp in opportunities:
            # Next activities
            if opp.next_activity_id and opp.date_action:
                date_action = fields.Date.from_string(opp.date_action)
                if date_action == date.today():
                    result['activity']['today'] += 1
                if date.today() <= date_action <= date.today() + timedelta(days=7):
                    result['activity']['next_7_days'] += 1
                if date_action < date.today():
                    result['activity']['overdue'] += 1
        return result

    @api.one
    @api.constrains('team_id', 'company_id')
    def _check_team_company(self):
        if self.team_id and self.company_id and self.team_id.company_id <> self.company_id:
            raise ValidationError(_("Team {%s} must belong Company {%s}." % (self.team_id.name, self.company_id.name)))