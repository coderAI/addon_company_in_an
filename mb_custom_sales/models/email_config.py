# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class email_config(models.Model):
    _name = 'email.config'
    _description = 'this object for config support send mail when funtion get sales oder run'

    name = fields.Char(string="Rule name", required=True)
    employee_ids = fields.Many2many('hr.employee', 'email_config_employee_rel', 'email_config_id', 'employee_id', string='Employee')
    email_config = fields.Char(string="Email list")
    active = fields.Boolean(string="Active")


    def update_email_config(self,employee_list):
        result={'email_config':''}

        if employee_list:
            if employee_list[0][2]:
                tmp_email_list = ''
                employee_data_list = self.env['hr.employee'].browse(employee_list[0][2])
                for i in employee_data_list:
                    tmp_email_list = tmp_email_list + i.work_email+';'
                result['email_config'] = tmp_email_list
        return result

    @api.model
    def select_property(self,number):
        data = self.sudo().env['product.category'].search([], order='website_sequence', limit=1000)

        return data

    @api.model
    def create(self, vals):
        if vals.get('employee_ids'):
            vals.update(self.update_email_config(vals.get('employee_ids')))
        return super(email_config, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('employee_ids'):
            vals.update(self.update_email_config(vals.get('employee_ids')))
        return super(email_config, self).write(vals)