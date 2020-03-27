# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
from datetime import datetime
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import re

class ExternalCronMail(models.AbstractModel):
    _description = 'Auto cron mail API'
    _name = 'external.cron.mail'

    @api.model
    def cron_mail(self):
        fetch = self.env['ir.cron'].search([('model', '=', 'fetchmail.server'), ('function', '=', '_fetch_mails')], limit=1)
        if not fetch:
            return True
        fetch.method_direct_trigger()