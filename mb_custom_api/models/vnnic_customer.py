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
from odoo import api, fields, models

import json
from datetime import datetime, timedelta
import json
import xlsxwriter
import StringIO
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)




class VnnicCustomer(models.Model):
    _name = 'vnnic.customer'

    partner_id = fields.Char(string='Partner')
    type = fields.Char(string='Type')
    seen_check = fields.Boolean('Seen')
    quantity = fields.Float(string="Quantity")
    rank = fields.Float(string="rank")
    percent = fields.Float(string="Percent")
    quantity_year = fields.Float(string="Quantity Year")
    quantity_month = fields.Float(string="Quantity")
    date = fields.Date(string='Date')


    @api.model
    def set_vnnic_customer(self,vals={}):
        data=[]
        messages='Successfully'
        code=200
        self.create(vals)
        res = {'code': code, 'messages':messages}
        return json.dumps(res)


class support_vnnic_customer_report_data(models.Model):   
    _name = 'support.vnnic.customer.report.data'
    date_merger = fields.Char('memory search')
    type_merger = fields.Char('type search')

class vnnic_customer_report(models.Model):
    _name = "vnnic.customer.report"

    merge_data = fields.Boolean(string='Merge Data')
    date_merger = fields.Char('memory search')
    type_merger = fields.Char('type search')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('vnnic.customer.report.line', 'vnnic_customer_report_id',string='Report Line', readonly=True)
    id_search_working = fields.Integer(string='Working', readonly=True)
    #---
    type = fields.Selection([
        ('Renew', 'Renew'),
        ('Register', 'Register')],default='Register', string="Type")


    @api.multi
    def get_lines(self, context_id, line_id=None):
        if isinstance(context_id, int):
            context_id = self.env['vnnic.customer.report.context'].browse(context_id)
        line_obj = self.line_ids
        if line_id:
            line_obj = self.env['vnnic.customer.report.line'].search([('id', '=', line_id)])
        if context_id.comparison:
            line_obj = line_obj.with_context(periods=context_id.get_cmp_periods())
        used_currency = self.env.user.company_id.currency_id
        currency_table = {}
        for company in self.env['res.company'].search([]):
            if company.currency_id != used_currency:
                currency_table[company.currency_id.id] = used_currency.rate / company.currency_id.rate
        lines_dicts = [{} for _ in context_id.get_periods()]

        res = line_obj.with_context(
            context=context_id,
            company_ids=context_id.company_ids.ids,
        ).get_lines(self, context_id, currency_table, lines_dicts)
        return res


class vnnic_customer_report_line(models.Model):
    _name = 'vnnic.customer.report.line'


    percent = fields.Float(string="Percent")
    quantity_year = fields.Float(string="Quantity Year")
    quantity_month = fields.Float(string="Quantity")

    vnnic_customer_report_id = fields.Many2one('vnnic.customer.report', string='Report', readonly=True)

class vnnic_customer_report_context(models.Model):
    _name = 'vnnic.customer.report.context'
    _inherit = "mb.report.context"
    product_category_id = fields.Many2one('product.category', string="Product Category")
    memory_type = fields.Char('memory type')
    type = fields.Selection([
        ('Renew', 'Renew'),
        ('Register', 'Register')],default='Register', string="Type")

    def get_columns_names(self):
        return ['Total','Count']

    def _report_model_to_report_context(self):
        return {
            'vnnic.customer.report': 'vnnic.customer.report.context',
        }

    @api.model
    def return_context(self, report_model, given_context, report_id=None):
        context_model = self._report_model_to_report_context()[report_model]
        data = [context_model, report_id]

        context = self.env[context_model].browse(data[1])
        for field in given_context:
            if context._fields.get(field) and given_context[field] != 'undefined' and field == 'category_ids':
                context.write({field: [(6, 0, [int(i) for i in given_context[field]])]})
        return data


    def get_data_rec(self, date_from, date_to, type=['Register']):

        key = str(date_from) + ' to ' + str(date_to)

        if type:

            if type:
                if len(type) > 1:
                    type = tuple(type)
                    type = "in ('Register','Renew')"
                elif type == ['']:
                    type = "= 'Register'"
                else:
                    type = "= '" + str(type[0])+"'"

            sql = '''
            
               select 								
               vc_f.partner_id,
               sum(vc_f.quantity_month) total,
							 
               COALESCE(SUM(vc_f.quantity_month),0)
							 /(
							  select 
								COALESCE(SUM(vc_c.quantity_month),0)/100
								from
								vnnic_customer as vc_c
								 where 
                vc_c.date >= '%s'::date and 
                vc_c.date <= '%s'::date and 
                type %s
								)
								as percent
             
                from vnnic_customer as vc_f
                where 
                vc_f.date >= '%s'::date and 
                vc_f.date <= '%s'::date and
                type %s
                GROUP BY vc_f.partner_id
                ORDER BY
                        total DESC

                        
               ''' % (date_from, date_to,type,date_from, date_to, type)

        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()
        convert_data_list = {}
        company_list = []
        total =0
        for i in datas:
            total += float(i[1])
            company_list.append(i[0])
            convert_data_list.update({key + str(i[0]):{
                'company_name':i[0],
                'total': '{:,.0f}'.format(i[1]),
                'count': format(i[2], '.2f'),

            }})
        res=convert_data_list
        res.update({key: total})
        return res , company_list


    @api.multi
    def get_html_and_data(self, context={}):
        result = {}
        report_data = self.env['vnnic.customer.report']
        report_id = report_data.search([('id_search_working', '=', self.id)], limit=1)
        date_merger = ''
        check_merger = False
        specail_list = False
        category_ids_running = []


        if context.get('category_ids'):
            type_search = []
            for i in context.get('category_ids'):
                type_search.append(i)
        else:
            if report_id.type_merger:
                if ',' in report_id.type_merger:
                    type_search = report_id.type_merger.split(',')
                else:
                    type_search = [report_id.type_merger]
            else:
                type_search = ['Register']

        for i_type_search in type_search:
            if i_type_search == 'Register':
                category_ids_running.append(['Register', u'Đăng Ký'])
            else:
                category_ids_running.append(['Renew', u'Duy trì'])



        #-------------
        if context.get('add_company_ids'):
            company_ids = context.get('add_company_ids')
        else:
            company_ids = self.env.user.company_id.id
        if report_id:
            date_merger = report_id.date_merger
        else:
            report_id = report_data.create({
                'start_date': '2019-01-01',
                'quit_date': '2019-12-31',
                'id_search_working': self.id,
                'date_merger': '',
                'type_search': 'Register'
            })
        if context.get('date_from'):
            date_from = context.get('date_from')
            date_to = context.get('date_to')
            date_list = [date_from + ' to ' + date_to]
        else:
            if context.get('date_from_cmp'):
                check_merger = True
                date_list_specail = ''
                if ',' in report_id.date_merger:
                    date_f = report_id.date_merger.split(',')[0]
                    date_from_date = datetime.strptime(date_f.split(' to ')[0], "%Y-%m-%d")
                    date_to_date = datetime.strptime(date_f.split(' to ')[1], "%Y-%m-%d")
                else:
                    date_from_date = datetime.strptime(report_id.date_merger.split(' to ')[0], "%Y-%m-%d")
                    date_to_date = datetime.strptime(report_id.date_merger.split(' to ')[1], "%Y-%m-%d")

                if context.get('periods_number'):
                    if context.get('date_filter_cmp') == 'same_last_year':

                        for range in xrange(0, int(context.get('periods_number'))):
                            date_from = date_from_date.replace(year=date_from_date.year - (range + 1))
                            date_to = date_to_date.replace(year=date_to_date.year - (range + 1))
                            if date_list_specail == '':
                                date_list_specail = str(date_from).split(' ')[0] + ' to ' + str(date_to).split(' ')[0]
                            else:
                                date_list_specail = date_list_specail + ',' + str(date_from).split(' ')[0] + ' to ' + \
                                                    str(date_to).split(' ')[0]
                if context.get('periods_number'):
                    if context.get('date_filter_cmp') == 'previous_period':
                        for range in xrange(0, int(context.get('periods_number'))):
                            date_from = date_from_date - relativedelta(months=(range + 1))
                            date_to = date_to_date - relativedelta(months=(range + 1))

                            if date_list_specail == '':
                                date_list_specail = str(date_from).split(' ')[0] + ' to ' + str(date_to).split(' ')[0]
                            else:
                                date_list_specail = date_list_specail + ',' + str(date_from).split(' ')[0] + ' to ' + \
                                                    str(date_to).split(' ')[0]
                if context.get('date_filter_cmp') and context.get('date_filter_cmp') == 'custom':
                    date_from = context.get('date_from_cmp')
                    date_to = context.get('date_to_cmp')
                elif ',' in report_id.date_merger:
                    date_f = report_id.date_merger.split(',')[0]
                    date_from = date_f.split(' to ')[0]
                    date_to = date_f.split(' to ')[1]
                else:
                    date_from = report_id.date_merger.split(' to ')[0]
                    date_to = report_id.date_merger.split(' to ')[1]
                date_list = [date_from + ' to ' + date_to]
                if date_list_specail != '':
                    report_id.date_merger = ''
                    specail_list = True


            else:
                if report_id:
                    date_list = report_id.date_merger.split(',')
                else:
                    date_from = '2020-02-01'
                    date_to = '2020-02-29'
                    date_list = [date_from + ' to ' + date_to]
        if context.get('date_filter_cmp') == 'no_comparison':
            check_merger = False
            date_from = '2020-02-01'
            date_to = '2020-02-29'
            date_list = [date_from + ' to ' + date_to]

        if check_merger:
            if specail_list:
                if report_id.date_merger == '':
                    report_id.date_merger = str(date_list[0]) + ',' + date_list_specail
                else:
                    report_id.date_merger = report_id.date_merger + ',' + str(date_list[0]) + ',' + date_list_specail
                date_merger = report_id.date_merger.split(',')
            else:
                report_id.date_merger = report_id.date_merger + ',' + str(date_list[0])
                date_merger = report_id.date_merger.split(',')
        else:
            report_id.date_merger = str(date_list[0])
            date_merger = date_list



        support_obj = self.sudo().env['support.vnnic.customer.report.data']
        support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)
        if support_report_data:
            support_report_data.date_merger = report_id.date_merger
            type_merger_tmp =''
            tmp_check =0
            for i_type_search in type_search:
                if tmp_check != 0:
                    type_merger_tmp = type_merger_tmp+','+i_type_search
                else:
                    type_merger_tmp = i_type_search
                tmp_check+=1
            support_report_data.type_merger = type_merger_tmp

        else:
            support_obj.create({'date_merger': report_id.date_merger})

            
        full_data = {}
        company_list = []
        if date_merger != '':
            for i in date_merger:
                if i != '':
                    data_line, company_list_tmp = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],type_search)
                    for i_company_list_tmp in company_list_tmp:
                        if i_company_list_tmp not in company_list:
                            company_list.append(i_company_list_tmp)
                    full_data.update(data_line)

        filter_company = [[c.id, c.name] for c in self.env['res.company'].search([])]

        context = {
            'id': self.id,
            'report_type': {'comparison': False, 'extra_options': False, 'date_range': False},
            'date_filter': 'today',
            'available_ids':True
        }
        if self.with_context(**context)._context:
            date_list_context = self.with_context(**context)._context.get('date_list') or []

        rcontext = {
            'res_company': self.env['res.users'].browse(self.env.uid).company_id,
            'context': context.update({'children_categories': [['Register', u'Đăng Ký'], ['Renew', u'Duy trì']],
                                       'category_ids': ['Register','Renew']}),
            'report_type': {'date_range': 15, 'comparison': True},
            'report': report_id,
            'date_filter': '2020-01-01',
            'date_filter_cmp': '2020-01-01',
            'date_from': '2020-01-01',
            'date_to': '2020-12-01',
            'periods_number':'2020-01-01',
            'date_from_cmp': '2020-01-01',
            'date_to_cmp': '2020-12-01',
            'company_ids': filter_company,
            'category_ids': ['Register','Renew'],
            'company_id_list': [company_ids],
            'date_list': date_merger,
            'product_category_id_list': company_list,


            'lines': full_data,
            'columns_names': ['cột1', 'cột2', 'cột3'],
            'test_data': [1, 2, 2, 3, 5, 5, 4, 4, 4, 4, 4, 8],
            'footnotes': [],
            'mode': 'display',
        }

        result['html'] = self.env['ir.model.data'].xmlid_to_object('mb_custom_api.report_vnnic').render(
            rcontext)
        result['report_type'] = {'comparison': True, 'extra_options': False, 'date_range': True, 'density': True}


        result['report_context'] = {
            'id': self.id,
            'date_filter': '2020-01-01',
            'date_filter_cmp': '2020-01-01',
            'date_from': '2020-12-01',
            'date_to': '2020-12-01',
            'periods_number': '2020-01-01',
            'date_from_cmp': '2020-01-01',
            'date_to_cmp': '2020-01-01',
            'company_ids': [],
            # 'available_ids': [['Register',u'Đăng Ký'],['Renew',u'Duy trì']],
            'category_ids': [],
            'comparison': True,

        }



        result['available_companies'] = filter_company
        result['report_context']['available_ids'] = [['Register',u'Đăng Ký'],['Renew',u'Duy trì']]
        result['report_context']['category_ids'] = category_ids_running
        result['report_context']['available_ids_name'] = 'Filter Type'
        result['comparison'] = True
        #reshow data selected
        result['report_context']['not_available_ids_name'] = 'Not Filter Product Category'
        result['report_context']['not_category_ids'] = []
        result['report_context']['not_available_ids'] = False



        #reshow data selected
        result['report_context']['available_customer_type_name'] = 'Filter Customer Type'
        result['report_context']['customer_type'] = []
        result['report_context']['available_customer_type'] = False


        #reshow data selected
        result['report_context']['not_customer_type'] = []
        result['report_context']['not_available_customer_type'] = []
        # result['report_context']['available_ids'] = False

        return result

    def get_pdf(self):

        for context in self:

            company_ids = self.env.user.company_id.id
            support_obj = self.sudo().env['support.vnnic.customer.report.data']
            report_obj = self.sudo().env['vnnic.customer.report']

            support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)
            full_data = {}
            time_line = []
            company_list = []
            if ',' in support_report_data.date_merger:
                group_time = support_report_data.date_merger.split(',')
                for i in support_report_data.date_merger.split(','):
                    if i != '':
                        time_line.append([i.split(' to ')[0], i.split(' to ')[1]])

                        data_line, company_list_tmp = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],
                                                                        support_report_data.type_merger.split(','))
                        for i_company_list_tmp in company_list_tmp:
                            if i_company_list_tmp not in company_list:
                                company_list.append(i_company_list_tmp)

                        full_data.update(data_line)


            else:
                group_time = [support_report_data.date_merger]
                i = support_report_data.date_merger
                data_line, company_list_tmp = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],
                                                                support_report_data.type_merger.split(','))
                for i_company_list_tmp in company_list_tmp:
                    if i_company_list_tmp not in company_list:
                        company_list.append(i_company_list_tmp)

                full_data.update(data_line)


            base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
                'ir.config_parameter'].sudo().get_param('web.base.url')

            rcontext = {
                'mode': 'print',
                'base_url': base_url,
                'res_company': self.env.user.company_id,
                'company': self.env.user.company_id,
                'company_id_list': [self.env.user.company_id.id],
                'date_list': group_time,
                'product_category_id_list': company_list,
                'lines': full_data,
            }

            body = self.env['ir.ui.view'].render_template(
                "mb_custom_api.report_template_vnnic_letter",
                values=dict(rcontext, lines=full_data, report={}, context=self))

            header = self.env['report'].render("report.internal_layout", values=rcontext)
            header = self.env['report'].render("report.minimal_layout", values=dict(rcontext, subst=True, body=header))

            landscape = False
            if len(self.get_columns_names()) > 4:
                landscape = True
        return self.env['report']._run_wkhtmltopdf([header], [''], [(0, body)], landscape,
                                                   self.env.user.company_id.paperformat_id,
                                                   spec_paperformat_args={'data-report-margin-top': 10,
                                                                          'data-report-header-spacing': 10})

    def write_data_to_sheet(self,workbook,sheet,group_time,company_list,lines):
        line_format = workbook.add_format({
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 10,
            'text_wrap': True,
        })
        line_h_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 10,
            'text_wrap': True,
        })

        sheet.write(1, 0, 'Company Name', line_format)
        clu_h=1
        for i_key in group_time:
            sheet.write(0, clu_h, i_key, line_h_format)
            sheet.write(0, clu_h+1, '', line_h_format)
            sheet.write(1, clu_h, 'Total', line_h_format)
            sheet.write(1, clu_h+1, 'Percent', line_h_format)
            clu_h+=2

        row=2
        for company in company_list:
            clu = 0
            sheet.write(row, clu, company, line_format)
            for i_key in group_time:

                    if lines.get(i_key):
                        group_line = lines.get(i_key+company)
                        sheet.write(row, clu+1, group_line.get('total'),line_format)
                        sheet.write(row, clu+2, group_line.get('count'),line_format)
                    else:
                        sheet.write(row, clu + 1, 0.0, line_format)
                        sheet.write(row, clu + 2, 0, line_format)
                    clu+=2
            row+=1

    def get_xlsx(self, response):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        support_obj = self.sudo().env['support.vnnic.customer.report.data']
        product_category_obj = self.sudo().env['product.category']
        support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)


        sheet = workbook.add_worksheet('Report')

        def_style = workbook.add_format({'font_name': 'Arial'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})
        sheet.write(0, 0, '', title_style)
        y_offset = 0
        x = 1
        for column in self.with_context(is_xls=True).get_columns_names():
            sheet.write(y_offset, x, column.replace('<br/>', ' ').replace('&nbsp;', ' '), title_style)
            x += 1
        y_offset += 1
        full_data={}

        no_add_on_data={}
        only_add_on_data={}
        time_line = []
        company_list = []

        company_ids = self.env.user.company_id.id
        if ','in support_report_data.date_merger:
            group_time = support_report_data.date_merger.split(',')
            for i in support_report_data.date_merger.split(','):
                if i != '':
                    time_line.append([i.split(' to ')[0],i.split(' to ')[1]])
                    data_line, company_list_list_id = self.get_data_rec(i.split(' to ')[0],i.split(' to ')[1],support_report_data.type_merger.split(','))

                    for i_company_list_tmp in company_list_list_id:
                        if i_company_list_tmp not in company_list:
                            company_list.append(i_company_list_tmp)
                    full_data.update(data_line)

        else:
            group_time = [support_report_data.date_merger]
            i = support_report_data.date_merger
            data_line, company_list_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],support_report_data.type_merger.split(','))

            for i_company_list_tmp in company_list_list_id:
                if i_company_list_tmp not in company_list:
                    company_list.append(i_company_list_tmp)
            full_data.update(data_line)
        lines = full_data

        self.write_data_to_sheet(workbook,sheet,group_time,company_list,lines)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
