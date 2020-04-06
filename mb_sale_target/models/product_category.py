# -*- coding: utf-8 -*-

import json
from odoo import api, fields, models, _
import logging
import time
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class product_category(models.Model):
    _inherit = "product.category"


    maximum_register_time = fields.Float(String='Maximum Register Time',track_visibility='onchange')


