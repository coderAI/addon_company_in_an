# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def unlink(self):
        if not self.user_has_groups('base.group_system'):
            raise UserError(_("You do not have the permission to delete this user!!!"))
        return super(ResUsers, self).unlink()
