# -*- coding: utf-8 -*-
from odoo import models,  api, SUPERUSER_ID, _
import json
import uuid
import logging as _logger
from datetime import datetime, timedelta, date

class ExternalHelpdeskTicket(models.AbstractModel):
    _description = 'Helpdesk API'
    _inherit = 'external.helpdesk.ticket'



    @api.model
    def all_ticket_new(self, customer_code):
        messages = 'Successful'
        code=200
        data=[]
        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit =1)
        if not customer_id:
            code = 501
            messages = 'Customer not exists'
        data_tmp = self.env['helpdesk.ticket'].search([('partner_id', '=', customer_id.id), ('display', '=', True)])
        if data_tmp:
            data=[]
            for ticket in data_tmp:
                ticket_data=ticket.read(['name','create_date', 'write_date'])[0]
                ticket_data.update({
                    'user_id': ticket.user_id and ticket.user_id.id or '',
                    'user_name': ticket.user_id and ticket.user_id.id or '',
                    'team_id': ticket.team_id and ticket.team_id.id or '',
                    'team_name': ticket.team_id and ticket.team_id.name or '',
                    'partner_id': ticket.partner_id and ticket.partner_id.id or '',
                    'partner_name': ticket.partner_id and ticket.partner_id.name or '',
                    'service_id': ticket.service_id and ticket.service_id.id or '',
                    'service_name': ticket.service_id and ticket.service_id.name or '',
                    'ticket_type_id': ticket.ticket_type_id and ticket.ticket_type_id.id or '',
                    'ticket_type_name': ticket.ticket_type_id and ticket.ticket_type_id.name or '',
                    'stage_id': ticket.stage_id and ticket.stage_id.id or '',
                    'stage_name': ticket.stage_id and ticket.stage_id.name or '',
                })
                message = self.env['mail.message'].search([('res_id', '=', ticket.id),
                                                           ('model', '=', 'helpdesk.ticket'),
                                                           ('message_type', '=', 'comment')], order='id desc', limit=1)
                if message:
                    ticket_data.update({
                        'write_date': message.write_date
                    })
                data.append(ticket_data)
        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'


    @api.model
    def create_ticket_for_service(self, customer_code='MB0000000', subject='Not data', service ='Not data', team ='Not data', description='Not data', on_web=True, ticket_type='', tags=''):
        messages = 'Successfull'
        code = 200
        ticket_id = 0
        team_id_tmp = False

        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit= 1)
        if not customer_id:
            messages = "Customer not exists"
            code = 402



        if service != 'Not data':
            service_id = self.env['sale.service'].search([('reference', '=', service)], limit=1)
            if not service_id:
                service_id = None
        else:
            service_id = None
        if on_web:
            display = on_web
        else:
            display = False


        team_id = False
        if team !='Not data':
            team_id = self.env['helpdesk.team'].search([('name', '=', team)], limit= 1)
            if not team_id:
                messages = "Helpdesk Team not exists"
                code = 402
            else:
                team_id = team_id.id


        ticket_type_id = self.env['helpdesk.ticket.type'].search([('name', '=', ticket_type)], limit=1)
        if ticket_type_id.group_id and ticket_type_id.group_id.team_id:
            team_id_tmp = ticket_type_id.group_id.team_id

        tags_ids = []
        if tags:
            tags_arr = tags.split(',')
            for tag in tags_arr:
                tag_id = self.env['helpdesk.tag'].search([('name', '=', tag)])
                if tag_id:
                    tags_ids.append(tag_id.id)
        if team_id_tmp and team_id == False:
            team_id = team_id_tmp.id
        elif team_id == False:
            team_id = 29
        now = datetime.now()
        ticket_value={
            'name': subject,
            'team_id': team_id,
            'service_id': service_id and service_id.id or False,
            'partner_id': customer_id and customer_id.id or False,
            'partner_name': customer_id and customer_id.name or False,
            'partner_email': customer_id and customer_id.email or False,
            'description': description,
            'display': display,
            'ticket_type_id': ticket_type_id and ticket_type_id.id or False,
            'kanban_state':'normal',
            'access_token':uuid.uuid4().hex,
            'create_date':str(now),
            'write_date':str(now),
            'create_uid':1,
            'write_uid':1,
            'sla_fail':False,
            'assign_hours':0,
            'priority':0,
            'rating_last_value':0,
            'active':True,
            'stage_id':121,
            'fee':False,
        }

        cr = self._cr
        if customer_id:
            cr.execute("""INSERT INTO helpdesk_ticket (name, team_id, partner_id, partner_name, partner_email, description, display,kanban_state, access_token, create_date, 
                                                        write_date, create_uid, write_uid, sla_fail, assign_hours, priority, rating_last_value, active, stage_id, fee)
                               VALUES (%(name)s, %(team_id)s, %(partner_id)s, %(partner_name)s, %(partner_email)s, %(description)s, %(display)s, %(kanban_state)s, %(access_token)s
                               , %(create_date)s, %(write_date)s, %(create_uid)s, %(write_uid)s, %(sla_fail)s, %(assign_hours)s, %(priority)s, %(rating_last_value)s, %(active)s, %(stage_id)s, %(fee)s)
                               RETURNING id """, ticket_value)
        else:

            cr.execute("""INSERT INTO helpdesk_ticket  (name, team_id,  description, display,kanban_state, access_token, create_date, 
                                                        write_date, create_uid, write_uid, sla_fail, assign_hours, priority, rating_last_value, active, stage_id, fee)
                               VALUES (%(name)s, %(team_id)s, %(description)s, %(display)s, %(kanban_state)s, %(access_token)s
                               , %(create_date)s, %(write_date)s, %(create_uid)s, %(write_uid)s, %(sla_fail)s, %(assign_hours)s, %(priority)s, %(rating_last_value)s, %(active)s, %(stage_id)s, %(fee)s)
                               RETURNING id """, ticket_value)

        ticket_id = cr.fetchone()[0]

        res = {'code': code, 'messages': messages, 'ticket_id': ticket_id}
        return json.dumps(res)


    @api.model
    def create_ticket_new(self, customer_code='MB0000000', subject='Not data', service ='Not data', team ='', description='Not data', on_web=1, ticket_type='', tags=''):
        messages = 'Successfull'
        code = 200
        ticket_id = 0
        team_id_tmp = False

        customer_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit= 1)
        if not customer_id:
            messages = "Customer not exists"
            code = 402


        # team_id = False
        # if team !='':
        #     team_id = self.env['helpdesk.team'].search([('name', '=', team)], limit= 1)
        #     if not team_id:
        #         messages = "Helpdesk Team not exists"
        #         code = 402

        if service != 'Not data':
            service_id = self.env['sale.service'].search([('reference', '=', service)], limit=1)
            if not service_id:
                service_id = None
        else:
            service_id = None
        if on_web and on_web in (0, 1):
            display = True if on_web == 1 else False
        else:
            display = True

        ticket_type_id = self.env['helpdesk.ticket.type'].search([('name', '=', ticket_type)], limit=1)
        if ticket_type_id.group_id and ticket_type_id.group_id.team_id:
            team_id_tmp = ticket_type_id.group_id.team_id
        if not ticket_type_id:
                messages = "Ticket Type not found"
                code = 402
        tags_ids = []
        if tags:
            tags_arr = tags.split(',')
            for tag in tags_arr:
                tag_id = self.env['helpdesk.tag'].search([('name', '=', tag)])
                if tag_id:
                    tags_ids.append(tag_id.id)
        if team_id_tmp:
            team_id = team_id_tmp.id
        else:
            team_id = 29
        now = datetime.now()
        ticket_value={
            'name': subject,
            'team_id': team_id,
            'service_id': service_id and service_id.id or False,
            'partner_id': customer_id and customer_id.id or False,
            'partner_name': customer_id and customer_id.name or False,
            'partner_email': customer_id and customer_id.email or False,
            'description': description,
            'display': display,
            'ticket_type_id': ticket_type_id and ticket_type_id.id or False,
            'kanban_state':'normal',
            'access_token':uuid.uuid4().hex,
            'create_date':str(now),
            'write_date':str(now),
            'create_uid':1,
            'write_uid':1,
            'sla_fail':False,
            'assign_hours':0,
            'priority':0,
            'rating_last_value':0,
            'active':True,
            'stage_id':121,
            'fee':False,


        }

        cr = self._cr
        cr.execute("""INSERT INTO helpdesk_ticket  (name, team_id, service_id, partner_id, partner_name, partner_email, description, display, ticket_type_id, kanban_state, access_token, create_date, 
                                                    write_date, create_uid, write_uid, sla_fail, assign_hours, priority, rating_last_value, active, stage_id, fee)
                           VALUES (%(name)s, %(team_id)s, %(service_id)s, %(partner_id)s, %(partner_name)s, %(partner_email)s, %(description)s, %(display)s, %(ticket_type_id)s, %(kanban_state)s, %(access_token)s
                           , %(create_date)s, %(write_date)s, %(create_uid)s, %(write_uid)s, %(sla_fail)s, %(assign_hours)s, %(priority)s, %(rating_last_value)s, %(active)s, %(stage_id)s, %(fee)s)
                           RETURNING id """, ticket_value)
        ticket_id = cr.fetchone()[0]

        res = {'code': code, 'messages': messages, 'ticket_id': ticket_id}
        return json.dumps(res)



    @api.model
    def create_ticket_by_smart_api(self,customer_code='',id_ticket_type=225,service_code='',description=''):
        messages = 'Successful'
        code=200
        data=False
        partner_id = self.env['res.partner'].search([('ref', '=', customer_code)], limit=1)
        if partner_id.id:
            sale_service_data = self.env['sale.service'].search([('reference', '=', service_code)], limit=1)
            if sale_service_data.id:
                vals = {
                    'name': 'Khách hàng góp ý cải thiện dịch vụ '+sale_service_data.name,
                    'team_id': 29,
                    'service_id': sale_service_data.id,
                    'ticket_type_id': id_ticket_type,
                    'description': description,
                    'partner_id': partner_id.id,
                    'display': False,
                    # 'stage_id':stage_id.id,
                }
                ticket_creaeted = self.create(vals)
                ticket_creaeted.write({'display': False,})
                data=True
            else:
                code = 401
                messages = 'Error service code can not map data'
        else:
            code = 401
            messages = 'Error customer code can not map data'
        res = {'code': code, 'messages': messages, 'data': data}
        return json.dumps(res)
