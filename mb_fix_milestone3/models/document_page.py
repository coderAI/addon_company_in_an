# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging as _logger

class DocumentPage(models.Model):
    _inherit = 'document.page'

    summary = fields.Text(string='Summary')