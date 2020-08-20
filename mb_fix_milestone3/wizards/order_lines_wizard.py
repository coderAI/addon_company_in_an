# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools.float_utils import float_compare
from datetime import datetime, timedelta

class OrderLinesWizard(models.TransientModel):
    _inherit = "order.lines.wizard"

    @api.onchange('register_type')
    def onchange_register_type(self):
        super(OrderLinesWizard, self).onchange_register_type()
        self.product_category_id = False
        domain = []
        if self._context.get('default_is_service', False):
            domain.append(('is_addons', '=', False))
            if self.register_type == 'register':
                domain.append(('sold', '=', True))
        else:
            domain.append(('is_addons', '=', True))
            if self.register_type == 'register':
                domain.append(('sold', '=', True))
        return {
            'domain': {
                'product_category_id': domain
            }
        }