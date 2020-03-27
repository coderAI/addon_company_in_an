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

import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError


class ExternalConfig(models.Model):
    _description = 'External API Config'
    _name = 'external.config'

    host_url = fields.Char(string="Host", required=True)
    db_name = fields.Char(string="Database Name", required=True)
    username = fields.Char(string="Username")
    pwd = fields.Char(string="Access token / Password")
    model_name = fields.Char(string="Model")
    func = fields.Char(string="Func")
    params = fields.Text(string="Arguments")
    msg = fields.Text(string="Result")

    @api.model
    def get_common(self, url):
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        return common

    @api.model
    def get_model(self, url):
        model = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
        return model

    @api.multi
    def get_uid(self):
        self.ensure_one()
        common = self.get_common(self.host_url)
        uid = common.authenticate(self.db_name, self.username, self.pwd, {})
        return uid

    @api.multi
    def call(self):
        try:
            self.ensure_one()
            uid = self.get_uid()
            model = self.get_model(self.host_url)
            model_name = self.model_name
            func = self.func
            params = eval(self.params)
            res = model.execute_kw(
                self.db_name, uid, self.pwd, model_name, func, params)
        except Exception, e:
            raise UserError(_(e.message or repr(e)) + " on API model: " + model_name + "; function: " + func)
        return res

    @api.multi
    def go(self):
        self.ensure_one()
        if not self.func or not self.params:
            raise Warning(_('Input `Func` and `Arguments` before continuing'))
        res = self.call()
        self.msg = res

    @api.model
    def create_so(self, vals={}, msg='', raise_wn=False):
        """
        Test creating new SO
        """
        res = {'code': 1, 'msg': 'Success', 'data': {}}
        return res
