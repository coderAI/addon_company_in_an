# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from openerp.addons.mail.models.mail_template import format_tz
import logging as _logger

class ExternalHelpdeskTicket(models.AbstractModel):
    _description = 'Helpdesk API'
    _name = 'external.helpdesk.ticket'

    @api.model
    def create_ticket(self, customer_code, subject, service, team, description, on_web=1, ticket_type='', tags=''):
        res = {'"code"': 0, '"msg"': '""'}
        if on_web <> 0 or customer_code:
            if not customer_code:
                res['"msg"'] = '"Customer code could not be empty"'
                return res
            customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
            if not customer_id:
                res['"msg"'] = '"Customer not exists"'
                return res
        else:
            customer_id = False
        if not subject:
            res['"msg"'] = '"Subject could not be empty"'
            return res
        if not team:
            res['"msg"'] = '"Team Support could not be empty"'
            return res
        team_id = self.env['helpdesk.team'].search([('name', '=', team)])
        if not team_id:
            res['"msg"'] = '"Helpdesk Team not exists"'
            return res
        if not description:
            res['"msg"'] = '"Description could not be empty"'
            return res
        if on_web <> 0 or service:
            if not service:
                res['"msg"'] = '"Service could not be empty"'
                return res
            service_id = self.env['sale.service'].search([('reference', '=', service)])
            if not service_id:
                res['"msg"'] = '"Service not exists"'
                return res
        else:
            service_id = False
        if on_web and on_web in (0, 1):
            display = True if on_web == 1 else False
        else:
            display = True

        ticket_id = self.env['helpdesk.ticket'].create({
            'name': subject,
            'team_id': team_id.id,
            'service_id': service_id and service_id.id or False,
            'partner_id': customer_id and customer_id.id or False,
            'partner_name': customer_id and customer_id.name or False,
            'partner_email': customer_id and customer_id.email or False,
            'description': description,
            'display': display,
        })
        if on_web == 0:
            ticket_id.write({'display': False})
        if ticket_id.message_ids:
            ticket_id.message_ids.write({
                'author_id': customer_id and customer_id.id or self.env.user.partner_id.id
            })
        # Custom for A.Ngan
        try:
            if on_web == 0:
                if ticket_type:
                    ticket_type_id = self.env['helpdesk.ticket.type'].search([('name', '=', ticket_type)], limit=1)
                    if ticket_type_id:
                        ticket_id.write({'ticket_type_id': ticket_type_id.id})
                if tags:
                    tags_arr = tags.split(',')
                    tags_ids = []
                    for tag in tags_arr:
                        tag_id = self.env['helpdesk.tag'].search([('name', '=', tag)], limit=1)
                        if tag_id:
                            tags_ids.append(tag_id.id)
                    if tags_ids:
                        ticket_id.write({'tag_ids': [(6, 0, tags_ids)]})
        except Exception as e:
            _logger.error("Create ticket Error: %s" % (e.message or repr(e)))
            pass
        if ticket_id:
            res['"code"'] = 1
            res['"ticket_id"'] = ticket_id.id
        else:
            res['"code"'] = 0
        return res

    @api.model
    def all_ticket(self, customer_code):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        tickets = self.env['helpdesk.ticket'].search_read([('partner_id', '=', customer_id.id), ('display', '=', True)],
        # tickets = self.env['helpdesk.ticket'].search_read([('partner_id', '=', customer_id.id),],
                                   ['name', 'user_id', 'team_id', 'partner_id', 'service_id',
                                    'ticket_type_id', 'create_date', 'write_date', 'stage_id'])
        if tickets:
            res['"code"'] = 1
            lst_ticket = []
            for ticket in tickets:
                message = self.env['mail.message'].search([('res_id', '=', ticket.get('id')),
                                                           ('model', '=', 'helpdesk.ticket'),
                                                           ('message_type', '=', 'comment')], order='id desc', limit=1)
                ticket.update({
                    'write_date': message.write_date
                })
                json_ticket = {}
                for key, value in ticket.iteritems():
                    if key in ('user_id', 'team_id', 'service_id', 'partner_id', 'ticket_type_id', 'stage_id'):
                        if value:
                            lst = list(value)
                            lst[1] = '\"' + lst[1] + '\"'
                            json_ticket.update({
                                '\"' + key + '\"': tuple(lst)
                            })
                        else:
                            json_ticket.update({
                                '\"' + key + '\"': []
                            })
                    elif type(value) == 'integer' or key == 'id':
                        json_ticket.update({
                            '\"' + key + '\"': value
                        })
                    elif key in ('description', 'name'):
                        json_ticket.update({
                            '\"' + key + '\"': '\"' + (value and str(value.replace("\'","\\\'").replace("\"","\\\"").encode('utf-8')) or '') + '\"'
                        })
                    elif key in ('create_date', 'write_date'):
                        json_ticket.update({
                            '\"' + key + '\"': '\"' + (value and format_tz(self.env, value, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or 'False') + '\"'
                        })
                    else:
                        json_ticket.update({
                            '\"' + key + '\"': '\"' + (value or 'False') + '\"'
                        })
                lst_ticket.append(json_ticket)
            tickets = lst_ticket
        else:
            res['"code"'] = 0
        return tickets

    @api.model
    def ticket_detail(self, ticket_id, customer_code):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        if not ticket_id:
            res['"msg"'] = '"Ticket could not be empty"'
            return res
        ticket = self.env['helpdesk.ticket'].search_read([('id', '=', ticket_id), ('partner_id', '=', customer_id.id), ('display', '=', True)],
        # ticket = self.env['helpdesk.ticket'].search_read([('id', '=', ticket_id), ('partner_id', '=', customer_id.id)],
                                  ['name', 'sla_name', 'team_id', 'user_id', 'priority', 'deadline',
                                   'partner_id', 'service_id', 'create_date', 'write_date',
                                   'ticket_type_id', 'description', 'message_ids', 'stage_id'], limit=1)
        if not ticket:
            res['"msg"'] = '"Ticket not exists"'
            return res
        json_ticket = {}
        for key,value in ticket[0].iteritems():
            if key in ('user_id', 'team_id', 'service_id', 'partner_id', 'stage_id', 'ticket_type_id') and value:
                if key == 'ticket_type_id':
                    json_ticket.update({
                        '\"' + key + '\"': '"False"'
                    })
                else:
                    lst = list(value)
                    lst[1] = '\"' + lst[1] + '\"'
                    json_ticket.update({
                        '\"' + key + '\"': tuple(lst)
                    })
            elif key in ('message_ids') or type(value) == 'integer':
                json_ticket.update({
                    '\"' + key + '\"': value
                })
            elif key in ('description', 'name'):
                json_ticket.update({
                    '\"' + key + '\"': '\"' + (value and str(value.replace("\'","\\\'").replace("\"","\\\"").encode('utf-8')) or '') + '\"'
                })
            elif key in ('create_date', 'write_date'):
                json_ticket.update({
                    '\"' + key + '\"': '\"' + (value and format_tz(self.env, value, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or 'False') + '\"'
                })
            else:
                try:
                    json_ticket.update({
                        '\"' + key + '\"': '\"' + (value and value or 'False') + '\"'
                    })
                except Exception as e:
                    res['"msg"'] = '"Key %s have problem: %s --> %s"' % (key, value, tools.ustr(e))
                    return res
        t = self.env['helpdesk.ticket'].browse(ticket_id)
        json_ticket.update({
            '"author_id"': '\"' + (t.message_ids and t.message_ids[-1].author_id and t.message_ids[-1].author_id.name or t.create_uid.partner_id.name) + '\"'
        })
        ticket = json_ticket
        message = self.env['mail.message'].search_read(
            [('res_id', '=', ticket_id), ('model', '=', 'helpdesk.ticket'), ('message_type', 'in', ('comment', 'email')), ('subtype_id', '=', 1)],
            ['body', 'attachment_ids', 'create_date', 'write_date', 'create_uid', 'author_id'])
        if message:
            lst_message = []
            # json_message = {}
            for mes in message:
                json_message = {}
                for key, value in mes.iteritems():
                    if key == 'attachment_ids':
                        json_message.update({
                            '\"' + key + '\"': value
                        })
                    elif key in ('create_uid', 'author_id') and value:
                        lst = list(value)
                        lst[1] = '\"' + lst[1] + '\"'
                        json_message.update({
                            '\"' + key + '\"': tuple(lst)
                        })
                    elif key == 'id':
                        json_message.update({
                            '\"' + key + '\"': value
                        })
                    elif key == 'body':
                        json_message.update({
                            '\"' + key + '\"': '\"' + (value and str(value.replace("\'","\\\'").replace("\"","\\\"").encode('utf-8')) or '') + '\"'
                        })
                    elif key in ('create_date', 'write_date'):
                        json_message.update({
                            '\"' + key + '\"': '\"' + (value and format_tz(self.env, value, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or 'False') + '\"'
                        })
                    else:
                        json_message.update({
                            '\"' + key + '\"': '\"' + (str(value.encode('utf-8')) or 'False') + '\"'
                        })
                lst_message.append(json_message)
            message = lst_message
        # attachment = self.env['ir.attachment'].search_read(
        #     [('res_id', '=', ticket_id), ('res_model', '=', 'helpdesk.ticket')],
        #     ['name', 'store_fname', 'checksum', 'datas_fname'])
        return ticket, message

    @api.model
    def update_ticket(self, ticket_id, customer_code, body, link_file=False):
        res = {'"code"': 0, '"msg"': '""'}
        if not customer_code:
            res['"msg"'] = '"Customer code could not be empty"'
            return res
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)])
        if not customer_id:
            res['"msg"'] = '"Customer not exists"'
            return res
        if not ticket_id:
            res['"msg"'] = '"Ticket could not be empty"'
            return res
        if not body:
            res['"msg"'] = '"Content could not be empty"'
            return res
        ticket = self.env['helpdesk.ticket'].search([('id', '=', ticket_id), ('partner_id', '=', customer_id.id)])
        if not ticket:
            res['"msg"'] = '"Ticket not exists"'
            return res
        message_id = self.env['mail.message'].search([('res_id', '=', ticket_id), ('model', '=', 'helpdesk.ticket')], order='id asc', limit=1)
        stage = self.env['helpdesk.stage'].search([('name', '=', 'Replied')], limit=1)
        ticket.with_context(id_page=True).write({
            'stage_id': stage and stage.id or ticket.stage_id.id,
            'message_ids': [(0, 0, {'body': body + '\n' + link_file if link_file else body,
                                    'model': 'helpdesk.ticket',
                                    'res_name': ticket.display_name,
                                    'parent_id': message_id.id,
                                    'author_id': customer_id.id,
                                    'subtype_id': 1,
                                    'message_type': 'email'})]
        })
        res['"code"'] = 1
        return res

    @api.model
    def create_ticket_chili(self, subject, email, team, description):
        res = {'"code"': 0, '"msg"': '""'}
        if not subject:
            res['"msg"'] = '"Subject could not be empty"'
            return res
        team_id = False
        if team:
            team_id = self.env['helpdesk.team'].search([('name', '=', team)])
        if not description:
            res['"msg"'] = '"Description could not be empty"'
            return res
        customer_id = False
        if email:
            customer_id = self.env['res.partner'].search([('email', '=', email)])
            if len(customer_id) <> 1:
                customer_id = False
        ticket_id = self.env['helpdesk.ticket'].create({
            'name': subject,
            'team_id': team_id and team_id.id or False,
            'partner_email': email or '',
            'description': description,
            'partner_id': customer_id and customer_id.id or False
        })
        if ticket_id:
            res['"code"'] = 1
            res['"ticket_id"'] = ticket_id.id
        else:
            res['"code"'] = 0
        return res
