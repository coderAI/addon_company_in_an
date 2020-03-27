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

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    code = fields.Char("Code")

    def _check_unique_code(self):
        for team in self:
            team_ids = self.search(
                [('code', '=', team.code), ('id', '!=', team.id)], limit=1)
            if team_ids:
                return False
        return True

    _constraints = [
        (_check_unique_code, 'Team Code must be unique!',
         ['code']),
    ]
