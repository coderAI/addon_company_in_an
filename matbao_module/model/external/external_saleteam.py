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

from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class ExternalSaleteam(models.AbstractModel):
    _description = 'External Saleteam API'
    _name = 'external.saleteam'

    @api.model
    def get_saleteam(self, date_from=False, date_to=False, limit=False,
                     order='name'):
        """
        Get Saleteam by date
        """
        CrmTeam = self.env['crm.team']
        args = []
        res = {'code': 0, 'msg': '', 'data': []}
        if date_from:
            try:

                system_date_from = self.env[
                    'ir.fields.converter']._str_to_datetime(
                        None, None, date_from)

                args += [('create_date', '>=', system_date_from[0])]
            except ValueError:
                res['msg'] = 'Wrong DATE FROM format'
                return res
        if date_to:
            try:
                system_date_to = self.env[
                    'ir.fields.converter']._str_to_datetime(
                        None, None, date_to)

                args += [('create_date', '<', system_date_to[0])]
            except ValueError:
                res['msg'] = 'Wrong DATE TO format'
                return res
        try:
            teams = CrmTeam.search(args, limit=limit, order=order)
        except UserError, e:
            res['msg'] = e[0]
            return res
        except ValueError, e:
            res['msg'] = e[0]
            return res
        except:
            res['msg'] = 'Unknow Error'
            return res
        res['code'] = 1
        for team in teams:
            res['data'].append({'code': team.code, 'name': team.name})
        return res
