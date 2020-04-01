# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()
    @api.one
    def _get_refund_only(self):
        if self.user_has_groups('base.group_system'):
            self.refund_only = True
        else:
            self.refund_only = False

    read_only_checking = fields.Boolean('readonly',compute='_get_refund_only')
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True, default=_get_default_team, oldname='section_id')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._uid <> SUPERUSER_ID:
            if self.user_has_groups('base.group_system') == False:
                    if self.user_has_groups('sales_team.group_sale_manager') == True:
                        return super(AccountPayment, self).search(args, offset, limit, order, count=count)
                    elif self.user_has_groups('sales_team.group_sale_salesman_all_leads') == True:
                        res_users_data = self.env['res.users'].sudo().browse(self._uid)
                        for i in res_users_data:
                                args.append(('team_id', '=', i.sale_team_id.id))
                    elif self.user_has_groups('sales_team.group_sale_salesman') == True:
                        args.append(('user_id', '=', self._uid))

        return super(AccountPayment, self).search(args, offset, limit, order, count=count)