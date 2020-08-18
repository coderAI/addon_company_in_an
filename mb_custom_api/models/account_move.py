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
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning

from datetime import datetime
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

DATE_FORMAT = "%Y-%m-%d"
FIELDS_SERVICE_DATA= ['id','name','reference','ip_hosting','ip_email','start_date','end_date','write_date','is_stop','temp_stop_date','temp_un_stop_date','status','id_domain_floor','is_active','order_ssl_id','price','vps_code','os_template','open','temp_open_date']
FIELDS_PRODUCT_CATEGORY_DATA= ['id','name','reference','ip_hosting','ip_email','start_date','end_date','write_date','is_stop','temp_stop_date','temp_un_stop_date','status','id_domain_floor','is_active','order_ssl_id','price','vps_code','os_template','open','temp_open_date']

import logging
_logger = logging.getLogger(__name__)




class AccountMove(models.Model):
    _inherit = 'account.move'

    def caculate_discount_amount(self,customer,so_id):
        res_partner = self.env['res.partner'].search([('ref', '=', customer)], limit=1)
        company = res_partner[0].company_id
        messages = 'successfully'
        if company.account_journal_id:
            journal_id = company.account_journal_id.id
        else:
            messages = 'Do not have data journal in this company data'

        if company.account_receivable_id:
            account_id = company.account_receivable_id.id
        else:
            messages = 'Do not have data account id in this company data'

        sql = '''
                SELECT  (SELECT COALESCE(
						    (SELECT sum(credit_cash_basis) - sum(debit_cash_basis) As sum_data from account_move_line aml
                                            LEFT JOIN account_move am on aml.move_id = am.id
                                            where aml.partner_id = %s
                                                        and aml.journal_id = %s 
                                                        and aml.company_id = %s
                                                        and aml.account_id = %s
                                                        and am.state= 'posted')
                                            ,0))                      
                       -(SELECT COALESCE(
												 (SELECT sum(amount_untaxed) As sum_data from sale_order so																		
																		where so.id <> %s
																		      and so.partner_id = %s   
																			  and so.state in ('draft','sale'))
												 
												 ,0))
                        ''' % (res_partner.id, journal_id, company.id, account_id,so_id, res_partner.id)
        logging.info(sql)
        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()
        data = data[0][0]

        return data,messages

    @api.model
    def get_discount_amount(self, customer_code = 'MBxxxxxxx',so_id = -1232):
        code=200
        messages='Successfully'
        data= False
        data,messages = self.caculate_discount_amount(customer_code,so_id)

        res = {'code': code, 'messages':messages,'data':data or 0}
        return json.dumps(res)
