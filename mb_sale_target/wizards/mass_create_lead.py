# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import base64
import logging
try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None
from datetime import datetime
from odoo.exceptions import UserError
from odoo.exceptions import Warning
MONTH_TEXT=['none','January','February','March','April','May','June','July','August','September','October','November','December']

_logger = logging.getLogger(__name__)




class mass_create_lead(models.TransientModel):
    _name = 'mass.create.lead'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    quantity = fields.Integer(string='Quantity')
    compare = fields.Selection([
                                ('<', '<'),
                                ('>', '>'),
                                ('=', '='),
                                ],string='compare')
    partner_ids = fields.Many2many('res.partner',string="Partners")
    description = fields.Char("Description")

    @api.multi
    def btn_get_customer(self):
        sql='''
        select rp.id,count(ss.id)
        from res_partner rp
        left join sale_service ss on rp.id = ss.customer_id and ss.end_date <= '%s'
        where
        		rp.company_type in ('person','company')
			    and rp.parent_id is Null
			    and rp.company_id = %s
			group by rp.id
			having count(ss.id) %s %s
        '''%(datetime.now(),str(self.env.user.company_id.id),self.compare,self.quantity)
        logging.info(sql)
        self._cr.execute(sql)
        sql_data = self._cr.fetchall()
        partner_ids =[]
        for r in sql_data:
            partner_ids.append(r[0])
        self.write({'partner_ids': [(6,0,partner_ids)]})




    @api.multi
    def btn_create_lead(self):
        self.description='create done'
        team_data_hcm = self.env['crm.team'].sudo().search([('type','=','sale'),('company_id','=',1),('id','!=',35)]).ids
        team_data_hn = self.env['crm.team'].sudo().search([('type','=','sale'),('company_id','=',3)]).ids
        hcm_len = len(team_data_hcm)
        hn_len = len(team_data_hn)
        m=[]
        running_hcm_company=0
        running_hcm_person=0
        running_hn_company=0
        running_hn_person=0
        sql=''
        uid =  str(self._uid)
        datatime_now = str(datetime.now())
        count = 0
        for i in self.partner_ids:
            logging.info(count)
            count=count+1
            if count == 1024:
                count=1
                self._cr.execute(sql)
                sql=''
            if i.company_type == 'person':
                if i.company_id.id == 1:
                    company_id = '1'
                    team_id = team_data_hcm[running_hcm_company]
                    running_hcm_company=running_hcm_company+1
                    if running_hcm_company == hcm_len:
                        running_hcm_company=0
                else:
                    company_id = '3'
                    team_id = team_data_hn[running_hn_company]
                    running_hn_company = running_hn_company + 1
                    if running_hn_company == hn_len:
                        running_hn_company=0
            else:
                if i.company_id.id == 1:
                    company_id = '1'
                    team_id = team_data_hcm[running_hcm_person]
                    running_hcm_person = running_hcm_person + 1
                    if running_hcm_person == hcm_len:
                        running_hcm_person = 0
                else:
                    company_id = '3'
                    team_id = team_data_hn[running_hn_person]
                    running_hn_person = running_hn_person + 1
                    if running_hn_person == hn_len:
                        running_hn_person = 0
            sql_tmp='''INSERT INTO crm_lead    
                            (active,type, 
                            create_uid,  write_uid, create_date, write_date, name, 
                            contact_name,email_from,mobile, phone, street, street2, 
                            city,state_id,country_id, 
                            partner_id, company_id,team_id) 
                            VALUES 
                            (true,'lead', 
                            %s, %s, '%s', '%s',
                            '%s',
                            '%s',
                            '%s','%s','%s',
                            '%s', 
                            '%s',
                            '%s', %s, %s, %s, %s, %s);'''%\
                    (uid, uid, datatime_now, datatime_now,
                     str(i.display_name).replace("'",' ') if "'" in str(i.display_name) else i.display_name,
                     str(i.name).replace("'",' ') if "'" in str(i.name) else i.name,
                     i.email,i.mobile,i.phone,
                     str(i.street).replace("'", ' ') if "'" in str(i.street) else i.street,
                     str(i.street2).replace("'", ' ') if "'" in str(i.street2) else i.street2,
                     i.city,
                     i.state_id and i.state_id.id or 'null',
                     i.country_id and i.country_id.id or 'null',str(i.id),str(company_id),str(team_id))
            sql =sql+sql_tmp
        if sql != '':
            self._cr.execute(sql)

