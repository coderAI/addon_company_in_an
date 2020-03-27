# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class KsDashboardNinjaBoardItemAction(models.TransientModel):
    _name = 'ks_ninja_dashboard.item_action'

    name = fields.Char()
    ks_dashboard_item_ids = fields.Many2many("ks_dashboard_ninja.item", string="Dashboard Items")
    ks_dashboard_item = fields.Many2one("ks_dashboard_ninja.item")
    ks_action = fields.Selection([('move', 'Move'),
                                  ('duplicate', 'Duplicate'),
                                  ], default=lambda self: self._context['ks_dashboard_item_action'], string="Action")
    ks_dashboard_ninja_id = fields.Many2one("ks_dashboard_ninja.board", string="Dashboards")
    ks_dashboard_ninja_ids = fields.Many2many("ks_dashboard_ninja.board", string="Select Dashboards")


    # Move or Copy item to another dashboard action
    @api.one
    def action_item_move_copy_action(self):
        if self.ks_action == 'move':
            for item in self.ks_dashboard_item_ids:
                item.ks_dashboard_ninja_board_id = self.ks_dashboard_ninja_id
        elif self.ks_action == 'duplicate':
            for dashboard_id in self.ks_dashboard_ninja_ids:
                for item in self.ks_dashboard_item_ids:
                    item.sudo().copy({'ks_dashboard_ninja_board_id': dashboard_id.id})
