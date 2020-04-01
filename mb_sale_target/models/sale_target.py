# -*- coding: utf-8 -*-

import json
from odoo import api, fields, models, _
import logging
import time
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)



class sale_target(models.Model):
    _name = "sale.target"

    team_id = fields.Many2one('crm.team', String='Team Name')
    user_id = fields.Many2one('res.users', String='Saleperson')
    company_id = fields.Many2one('res.company', String='Saleperson')
    date_from = fields.Date(string="Date", default=lambda *a: time.strftime('%Y-%m-01'))


    total_target = fields.Float(string='Target')
    target_line_ids = fields.One2many('sale.target.line', 'sale_target_id')

    @api.onchange('date_from')
    def onchange_date_from(self):
        if self.env['res.users'].has_group('sales_team.group_sale_salesman_all_leads') and not self.env['res.users'].has_group('sales_team.group_sale_manager'):
            return {'domain': {'team_id': [('id', 'in', self.env.user.sale_team_id.ids)]}}
        else:
            return {}

    @api.onchange('team_id')
    def onchange_team_id(self):
        self.user_id = False



    @api.model
    def create(self, vals):

        date = vals.get('date_from').split('-')
        vals.update({
            'date_from': date[0]+'-'+date[1]+'-'+'1'
        })
        same_ids = self.sudo().search([('team_id', '=', vals['team_id']),
                                       ('user_id', '=', vals['user_id']),
                                       ('date_from', '=', vals['date_from'])])
        if same_ids:
            raise UserError(_('This saleperson has already been used!'))
        return super(sale_target, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('team_id') or vals.get('user_id') or vals.get('date_from'):

            team_id = vals.get('team_id') or self.team_id.id
            user_id = vals.get('user_id') or self.user_id.id
            if vals.get('date_from'):
                date = vals.get('date_from').split('-')
                date_from = date[0] + '-' + date[1] + '-' + '1'
                vals.update({
                    'date_from': date_from
                })

            else:
                self.date_from
            same_ids = self.sudo().search([('id', '!=', self.id), ('team_id', '=', team_id),
                    ('user_id', '=', user_id), ('date_from', '=', date_from)])
            if same_ids:
                raise UserError(_('This saleperson has already been used!'))
        return super(sale_target, self).write(vals)



class sale_target_line(models.Model):
    _name = "sale.target.line"

    total_target = fields.Float(string='Target')
    sale_target_id = fields.Many2one('sale.target')