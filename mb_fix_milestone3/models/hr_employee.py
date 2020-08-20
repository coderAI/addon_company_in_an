# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # @api.depends('holidays_approvers')
    # def _get_holidays_approvers_users(self):
    #     for employee in self:
    #         user_ids = employee.mapped('holidays_approvers').mapped('approver').mapped('user_id')
    #         employee.holidays_approvers_users = user_ids and [(6, 0, user_ids.ids)] or [(5,)]
    #         _logger.info("================= %s ---------------" % employee.holidays_approvers_users)
    #
    # holidays_approvers_users = fields.Many2many('res.users', 'holidays_approvers_users_rel', 'empoyee_id', 'user_id',
    #                                             compute="_get_holidays_approvers_users", store=True)