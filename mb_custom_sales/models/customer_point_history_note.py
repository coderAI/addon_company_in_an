# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging
from odoo.exceptions import Warning
from datetime import datetime,date, timedelta
import json
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class action_change_gift_note(models.Model):
    _name = "action.change.gift.note"
    res_partner_gift_id = fields.Many2one('res.partner.gift', string='Gift')
    customer_point_history_note_id = fields.Many2one('customer.point.history.note', string='History Note')
    point = fields.Integer('point')



class customer_point_history_note(models.Model):
    _name = "customer.point.history.note"

    partner_id = fields.Many2one('res.partner',string='Customer')
    service_id = fields.Many2one('sale.service', string='Service')
    action_change_gift_note_ids = fields.One2many('action.change.gift.note','customer_point_history_note_id',string='Action change')
    account_move_line_id = fields.Many2one('account.move.line', string='Account Move Line')

    point = fields.Integer('point')
    available_point = fields.Integer('Available Point')
    date = fields.Date('date')
    active = fields.Boolean('Active', default=True)

class res_partner(models.Model):
    _inherit = "res.partner"
    @api.multi
    def point_button(self):
        attachment_view = self.env.ref('mb_custom_sales.view_customer_point_history_note_tree')
        return {
            'name': 'Customer Point',
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'customer.point.history.note',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'tree')],
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

class res_partner_gift(models.Model):
    _inherit = "res.partner.gift"

    # history_note_ids = fields.Many2many('customer.point.history.note', 'cphn_rpg_rel','rpg_id', 'cphn_id', 'Point relationship')
    action_change_gift_note_ids = fields.One2many('action.change.gift.note', 'res_partner_gift_id',
                                                  string='Action change')


    @api.multi
    def update_data(self):
        note_obj = self.sudo().env['customer.point.history.note']
        for i_rec in self.search([('state', '!=', 'cancel')]):
            logging.info(i_rec.id)
            point_list = note_obj.search(
                [('partner_id', '=', i_rec.partner_id.id), ('available_point', '>', 0)], order="date asc")
            gift_settings = i_rec.gift_id
            coppy = gift_settings.point
            check_point = 0
            for i in point_list:
                check_point += i.available_point
                if check_point >= coppy:
                    break
            if check_point >= coppy:
                check_point = 0
                action_change_gift_note_ids = []
                for i in point_list:
                    if i.available_point <= coppy - check_point:
                        check_point += i.available_point
                        using_point = i.available_point
                        available_point = 0
                    else:

                        using_point = coppy - check_point
                        available_point = i.available_point - (coppy - check_point)
                        check_point += coppy - check_point
                    i.available_point = available_point
                    action_change_gift_note_ids.append((0, 0, {'customer_point_history_note_id': i.id,
                                                               'point': using_point}))
                    if check_point >= coppy:
                        break
                i_rec.action_change_gift_note_ids = action_change_gift_note_ids

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        for i in self.sudo().env['action.change.gift.note'].search([('res_partner_gift_id', '=', self.id)]):
            i.customer_point_history_note_id.available_point = i.customer_point_history_note_id.available_point + i.point
            i.unlink()

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})
        today_remove_year = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
        point_list = self.sudo().env['customer.point.history.note'].search(
            [('partner_id', '=', self.partner_id.id), ('available_point', '>', 0),('date','>',today_remove_year)], order="date asc")
        gift_settings = self.gift_id
        coppy = gift_settings.point
        check_point = 0
        for i in point_list:
            check_point += i.available_point
            if check_point >= coppy:
                break
        if check_point >= coppy:
            check_point = 0
            action_change_gift_note_ids = []
            for i in point_list:
                if i.available_point <= coppy - check_point:
                    check_point += i.available_point
                    using_point = i.available_point
                    available_point = 0
                else:
                    using_point = coppy - check_point
                    available_point = i.available_point - (coppy - check_point)
                    check_point += coppy - check_point
                i.available_point = available_point
                action_change_gift_note_ids.append((0, 0, {'customer_point_history_note_id': i.id,
                                                           'point': using_point}))
                if check_point >= coppy:
                    break
            self.action_change_gift_note_ids = action_change_gift_note_ids

    @api.model
    def create(self, values):
        partner_id = values.get('partner_id')
        today_remove_year = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
        point_list = self.sudo().env['customer.point.history.note'].search([('partner_id','=',partner_id),('available_point','>',0),('date','>',today_remove_year)], order="date asc")
        gift_settings = self.env['res.partner.gift.settings'].browse(values.get('gift_id'))
        coppy = gift_settings.point
        check_point = 0
        for i in point_list:
            check_point += i.available_point
            if check_point >= coppy:
                break
        if check_point >= coppy:
            check_point =0
            action_change_gift_note_ids =[]
            for i in point_list:
                if i.available_point <= coppy - check_point:
                    check_point += i.available_point
                    using_point = i.available_point
                    available_point = 0
                else:
                    using_point = coppy - check_point
                    available_point = i.available_point - (coppy - check_point)
                    check_point += coppy - check_point
                i.available_point = available_point
                action_change_gift_note_ids.append((0, 0, {'customer_point_history_note_id':i.id,
                                                           'point':using_point}))
                if check_point >= coppy:
                    break
            values.update({'action_change_gift_note_ids':action_change_gift_note_ids})
        else:
            raise Warning(_("The customer don't enought point for this action"))

        return super(res_partner_gift, self).create(values)



class res_partner(models.Model):
    _inherit = "res.partner"
    point_new = fields.Integer('Point', compute='get_point_new')
    available_point = fields.Integer('Available Point', compute='get_point_new')

    def get_point_new(self):
        for partner in self:
            available_point = 0
            point_new = 0
            today_remove_year = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
            point_data = self.env['customer.point.history.note'].search([('partner_id', '=', partner.id),('date','>',today_remove_year)])
            for i in point_data:
                available_point+=i.available_point
                point_new+=i.point
            self.available_point = int(available_point)
            self.point_new = int(point_new)

    @api.model
    def get_point_new(self, customer_code):
        partner = self.env['res.partner'].search([('ref', '=', customer_code)], limit=1)
        available_point = 0
        point_new = 0
        today_remove_year = (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d')
        point_data = self.env['customer.point.history.note'].search([('partner_id', '=', partner.id),('date','>',today_remove_year)])
        for i in point_data:
            available_point += i.available_point
            point_new += i.point
        data = {
            'point_new':point_new,
            'available_point':available_point,
        }
        res = {'code': 200, 'messages': 'Successfull' , 'data':data}
        return json.dumps(res)

class sale_service(models.Model):
    _inherit = "sale.service"

    @api.multi
    def write(self, vals):
        if vals.get('review'):
            phn_obj=self.env['customer.point.history.note']
            if phn_obj.search_count([('service_id','!=',False),('partner_id','=',self.customer_id.id)]) < 5:
                if phn_obj.search([('service_id','=',self.id)], limit=1):
                    pass
                else:
                    phn_obj.create({
                        'point':50.0,
                        'available_point':50,
                        'service_id':self.id,
                        'partner_id':self.customer_id.id,
                        'date':vals.get('review_date') or fields.Date.today(),
                    })
        return super(sale_service, self).write(vals)


class account_move(models.Model):
    _inherit = "account.move"
    @api.multi
    def write(self, vals):
        if vals.get('state'):
            if vals.get('state') == 'posted':
                phn_obj = self.env['customer.point.history.note']
                amount_once_point = self.env['ir.values'].sudo().get_default('sale.config.settings',
                                                                             'revenue_for_point')
                if amount_once_point:
                    for i_self in self:
                        for aml in i_self.line_ids:
                            if aml.account_id.id in [9, 389] and aml.credit > 0:
                                if phn_obj.search([('account_move_line_id', '=', aml.id)], limit=1):
                                    pass
                                else:
                                    phn_obj.create({
                                        'point': int(aml.credit / amount_once_point),
                                        'available_point': int(aml.credit / amount_once_point),
                                        'partner_id': aml.partner_id.id,
                                        'account_move_line_id': aml.id,
                                        'date': fields.Date.today(),
                                    })
        return super(account_move, self).write(vals)


class account_move_line(models.Model):
    _inherit = "account.move.line"
    @api.multi
    def write(self, vals):
        if vals.get('partner_id'):
            phn_obj = self.env['customer.point.history.note']
            for i in self:
                if i.account_id:
                    if i.account_id.id in [9,389] and i.credit > 0:
                        if i.move_id.state == 'posted':
                            phn = phn_obj.search([('account_move_line_id', '=', i.id)], limit=1)
                            if phn:
                                if phn.available_point == phn.point:
                                    phn.partner_id=vals.get('partner_id')
        return super(account_move_line, self).write(vals)