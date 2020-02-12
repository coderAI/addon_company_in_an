# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
from odoo import api, fields, models,_
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.exceptions import UserError, ValidationError
import json

import logging
_logger = logging.getLogger(__name__)

LIST_CONVERT = [
                ['team_id','crm.team','code'],
                ['state_id', 'res.country.state','code'],
                ['partner_id','res.partner','ref'],
                ['title','res.partner.title','name'],
                ['source_id','utm.source','name'],
                ['country_id','res.country','code']
               ]
class system_api_config(models.Model):
    _name = 'system.api.config'
    _inherit = ['res.config.settings']
    def _get_default_account_ids(self):
        res = []
        default_set = self.search([], limit=1, order='id desc')
        if default_set:
            res = default_set.account_ids.ids
        return res
    account_ids = fields.Many2many('res.users', 'system_api_config_users_rel', 'system_api_config_id', 'user_id', default=_get_default_account_ids, string='account')



class summary_system_api(models.Model):
    _name = 'summary.system.api'
    summary_day = fields.Datetime('Summary Day')
    user_id = fields.Many2one('res.users', string='User Call')
    system_api_action_history_ids = fields.One2many('system.api.action.history', 'summary_system_api_id')
    state = fields.Selection([('open', 'New'), ('summary', 'Summary')], string='Status', default='open')

    @api.multi
    def unlink(self):
        if self.state == 'summary':
            raise UserError(_('You cannot remove summary state rec'))
        return super(summary_system_api, self).unlink()

    @api.multi
    def btn_summary(self):
        sql = '''UPDATE system_api_history_line
                        SET is_checking = True, summary_system_api_id = '''+str(self.id)+''' where summary_system_api_id is Null;
                 SELECT name,MAX(timestamptz(date_end)- timestamptz(date_start)) as max_time, Min(timestamptz(date_end)- timestamptz(date_start)) as min_time FROM system_api_history_line Where is_checking = TRUE and summary_system_api_id = '''+str(self.id)+''' GROUP BY name'''

        self.state = 'summary'
        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()
        for (name, max_time, min_time) in data:
            system_api_history_line_obj = self.env['system.api.history.line']
            system_api_action_history_obj = self.env['system.api.action.history']
            old_total_call=0
            old_total_error_call=0
            for i in system_api_action_history_obj.search([('name','=',name),('summary_system_api_id','=',self.id)]):
                old_total_call += i.total_call
                old_total_error_call += i.total_error_call
            total_call = system_api_history_line_obj.search_count(
                [('name', '=', name), ('summary_system_api_id', '=', self.id)]) - old_total_call

            total_error_call = system_api_history_line_obj.search_count([('is_error', '=', True), ('summary_system_api_id', '=', self.id),
                                                      ('name', '=', name)]) - old_total_error_call
            if total_call > 0:
                if total_error_call < 0:
                    total_error_call = 0
                vals={
                    'name':name,
                    'maximun_time':max_time,
                    'minimun_time':min_time,
                    'summary_system_api_id':self.id,
                    'total_call':total_call,
                    'total_error_call':total_error_call
                }
                system_api_action_history_obj.create(vals)



class system_api_action_history(models.Model):
    _name = 'system.api.action.history'
    name = fields.Char('API Name')
    summary_system_api_id = fields.Many2one('summary.system.api')
    total_call = fields.Integer('Total Call')
    total_error_call = fields.Integer('Total error Call')
    minimun_time = fields.Char('Minimun Running Time(s)')
    maximun_time = fields.Char('Maximun Running Time(s)')
    #account_call = fields.Char('account call this API')
    @api.multi
    def view_detail(self):
        for this_rec in self:
            list_view_id = self.env['ir.model.data'].xmlid_to_res_id('mb_custom_api.view_system_api_history_line_tree')

            return {
                'type': 'ir.actions.act_window',
                'name': 'system.api.history.line.tree',
                "views": [[list_view_id, "tree"]],
                'res_model': 'system.api.history.line',
                'domain': str([('name','=',this_rec.name),('summary_system_api_id','=',self.summary_system_api_id.id)]),
                "context": {"create": False, },
            }


class system_api_action(models.Model):
    _name = 'system.api.action'
    # name = fields.Char('API Name')
    user_id = fields.Many2one('res.users', string='User Call')
    system_api_action_history_id = fields.Many2one('system.api.action.history', string='system api')
    summary_day = fields.Datetime('Summary Day')
    total_call = fields.Integer('Total Call')
    total_error_call = fields.Integer('Total error Call')
    minimun_time = fields.Float('Minimun Running Time(s)')
    maximun_time = fields.Float('Maximun Running Time(s)')
    account_call = fields.Char('account call this API')

class system_api_history_line(models.Model):
    _name = 'system.api.history.line'
    name = fields.Char('API Name')
    user_id = fields.Many2one('res.users', string='User Call')
    system_api_action_id = fields.Many2one('system.api.action')
    summary_system_api_id = fields.Many2one('summary.system.api')
    date_start = fields.Datetime(string='start Datetime')
    date_end = fields.Datetime(string='end Datetime')
    is_checking = fields.Boolean(string="Is Checking")
    is_error = fields.Boolean(string="Is Error", default=False)
    description = fields.Text('Description')

    @api.model
    def create_line_call(self,date_start,date_end='',name='',description='',is_error = False):

        if date_end == '':
            is_error = date_start[4]
            description = date_start[3]
            name = date_start[2]
            date_end = date_start[1]
            date_start = date_start[0]

        messages = 'Successfully'
        code = 200
        system_api_config_users_rel = self.env['system.api.config'].search([],limit=1, order='id desc')
        lst =  system_api_config_users_rel.account_ids.ids
        # if self._uid in lst or self._uid == 1:


        self.create({
            'date_start':date_start.strftime(DTF),
            'date_end':date_end.strftime(DTF),
            'name':name,
            'description':str(description),
            'is_error':is_error,
            'user_id':self._uid,
        })
        # else:
        #     raise UserError(_('You account can not call api'))
        res = {'code': code, 'messages': messages}
        return json.dumps(res)

