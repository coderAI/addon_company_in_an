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
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import json
import xlsxwriter
import StringIO
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
SEARCH_TYPE =[['person','Individual'],['agency','Agency'],['company','Company']]
SEARCH_TYPE_OBJ ={'person':'Individual',
                  'agency':'Agency',
                  'company':'Company'}


class count_search_service_seniority(models.Model):
    _name = 'count.search.service.seniority'

    service_id = fields.Many2one('sale.service', "Service")
    count_search = fields.Integer(string='Search')
    seniority = fields.Integer(string='Seniority')


    @api.model
    def get_service_point(self,values):
        code=200
        messages='Successfully'
        product_obj = self.env['product.product']
        sale_service_obj = self.env['sale.service']
        product_category_obj = self.env['product.category']
        product_category_ids =[]
        product_category_ids_tmp = product_category_obj.search([('parent_id', '=', 4088)]).ids
        while product_category_ids_tmp:
            product_category_ids_tmp = product_category_obj.search([('parent_id', '=', product_category_ids_tmp)])
            if product_category_ids_tmp:
                product_category_ids=+product_category_ids_tmp.ids
            else:
                product_category_ids_tmp=[]
        for i_data in values:
            product_id = product_obj.search([('name', '=',i_data.get('domain'))], limit=1)
            if product_id:
                ss = sale_service_obj.search([('product_id','=',product_id.id),('product_category_id','in',product_category_ids)],limit=1)
                if ss:
                    this_rec = self.search([('service_id','=',ss.id)],limit=1)
                    if this_rec:
                        this_rec.count_search= i_data.get('count_search')
                        this_rec.seniority= i_data.get('seniority')
                    else:
                        self.create({
                            'service_id':ss.id,
                            'seniority':i_data.get('seniority'),
                            'count_search':i_data.get('count_search'),
                        })


        res = {'code': code, 'messages':messages}
        return json.dumps(res)

class support_report_data(models.Model):
    _name = 'support.report.data'
    date_merger = fields.Char('memory search')
    product_category_id = fields.Many2one('product.category', string="Product Category")
    category_ids = fields.Many2many('product.category', 'product_category_support_category_ids_rel', string="Product Category")
    not_category_ids = fields.Many2many('product.category', 'product_category_support_not_category_ids_rel',string="Not Product Category")
    customer_type = fields.Char(string='customer_type_list')
    not_customer_type = fields.Char(string='not_customer_type_list')

class ss_forecast_renew_service_report(models.Model):
    _name = "ss.forecast.renew.service.report"

    merge_data = fields.Boolean(string='Merge Data')
    date_merger = fields.Char('memory search')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('ss.forecast.renew.service.report.line', 'ss_forecast_renew_service_report_id',string='Report Line', readonly=True)
    id_search_working = fields.Integer(string='Working', readonly=True)
    product_category_id = fields.Many2one('product.category', string="Product Category")
    category_ids = fields.Many2many('product.category', 'product_category_ss_forecast_renew_category_ids_rel', string="Product Category")
    not_category_ids = fields.Many2many('product.category', 'product_category_ss_forecast_renew_not_category_ids_rel',string="Not Product Category")
    customer_type = fields.Char(string='customer_type_list')
    not_customer_type = fields.Char(string='not_customer_type_list')

class ss_forecast_renew_service_report_line(models.Model):
    _name = 'ss.forecast.renew.service.report.line'


    start_date = fields.Date(string='Start Date')
    quit_date = fields.Date(string='Quit Date')

    product_category_id = fields.Many2one('product.category', string="Product Category")
    product_id = fields.Many2one('product.product', string="Product")
    total = fields.Float(string='total', readonly=True)

    ss_forecast_renew_service_report_id = fields.Many2one('ss.forecast.renew.service.report', string='Report', readonly=True)

class ss_forecast_renew_service_report_context(models.Model):
    _name = 'ss.forecast.renew.service.report.context'
    _inherit = "mb.report.context"
    product_category_id = fields.Many2one('product.category', string="Product Category")
    not_category_ids = fields.Many2many('product.category',string="Not Product Category")
    customer_type = fields.Char(string='customer_type_list')
    not_customer_type = fields.Char(string='not_customer_type_list')


    def get_columns_names(self):
        return ['Total','Count']

    def _report_model_to_report_context(self):
        return {
            'ss.forecast.renew.service.report': 'ss.forecast.renew.service.report.context',
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


    def get_data_rec(self, date_from, date_to,company_id=1, customer_type='snow,',check_addon = 'full'):

        key = str(date_from) + ' to ' + str(date_to)

        sql_search_cusstomer_type = '--'
        if len(customer_type.split(',')) != 1:
            sql_search_cusstomer_type = "and rp.company_type in ('snow'"
            for i_customer_type in customer_type.split(','):
                sql_search_cusstomer_type = sql_search_cusstomer_type+",'"+i_customer_type.encode('utf-8')+"'"
            sql_search_cusstomer_type = sql_search_cusstomer_type+')'


        if check_addon =='full':
            sql = '''
               select 	
                    pc1.name,
                    sum(coalesce(null,pc.renew_price_vendor, 0) + case when pc.uom_id = 20 then coalesce(null,pc.renew_price_mb,0) else coalesce(null,pc.renew_price_mb,0) * 12 end) as revenue,
                    count(pc1.id) as count,
                    pc1.id
                    from sale_service ss
                    inner join res_partner rp on rp.id = ss.customer_id
                    inner join product_category pc on pc.id = ss.product_category_id
                    inner join product_category pc1 on pc1.id = pc.parent_id
                    where
                            rp.company_id = %s
                        and	ss.end_date >= '%s' and ss.end_date <= '%s'
                        and	pc.uom_id in (20, 21)
                        and	ss.status = 'active'                       
                        %s
                    group by pc1.name,pc1.id
                    ORDER BY pc1.name
               ''' % (company_id,date_from, date_to, sql_search_cusstomer_type)
        elif check_addon == 'none add on':
            sql = '''
               select 	
                    pc1.name,
                    sum(coalesce(null,pc.renew_price_vendor, 0) + case when pc.uom_id = 20 then coalesce(null,pc.renew_price_mb,0) else coalesce(null,pc.renew_price_mb,0) * 12 end) as revenue,
                    count(pc1.id) as count,
                    pc1.id
                    from sale_service ss
                    inner join res_partner rp on rp.id = ss.customer_id
                    inner join product_category pc on pc.id = ss.product_category_id
                    inner join product_category pc1 on pc1.id = pc.parent_id
                    where
                            rp.company_id = %s
                        and	ss.end_date >= '%s' and ss.end_date <= '%s'
                        and	pc.uom_id in (20, 21)
                        and pc.is_addons != TRUE
                        and	ss.status = 'active'
                        %s
                    group by pc1.name,pc1.id
                    ORDER BY pc1.name
               ''' % (company_id,date_from, date_to, sql_search_cusstomer_type)
        elif check_addon == 'only add on':
            sql = '''
               select 	
                    pc1.name,
                    sum(coalesce(null,pc.renew_price_vendor, 0) + case when pc.uom_id = 20 then coalesce(null,pc.renew_price_mb,0) else coalesce(null,pc.renew_price_mb,0) * 12 end) as revenue,
                    count(pc1.id) as count,
                    pc1.id
                    from sale_service ss
                    inner join res_partner rp on rp.id = ss.customer_id
                    inner join product_category pc on pc.id = ss.product_category_id
                    inner join product_category pc1 on pc1.id = pc.parent_id
                    where
                            rp.company_id = %s
                        and	ss.end_date >= '%s' and ss.end_date <= '%s'
                        and	pc.uom_id in (20, 21)
                        and pc.is_addons = TRUE
                        and	ss.status = 'active'
                        %s
                    group by pc1.name,pc1.id
                    ORDER BY pc1.name
               ''' % (company_id,date_from, date_to, sql_search_cusstomer_type)
        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()
        convert_data_list = {}
        product_category_list_id = []
        total =0
        for i in datas:
            total += float(i[1])
            product_category_list_id.append(int(i[3]))
            convert_data_list.update({key + str(i[3]):{
                'product_name':i[0],
                'total': '{:,.0f}'.format(i[1]),
                'count': i[2],
                'id': i[3],
            }})
        res=convert_data_list
        res.update({key: total})
        return res , product_category_list_id


    @api.multi
    def get_available_ids_and_names(self):
        return [[a.id, a.name] for a in self.env['product.category'].search([])]

    def rebuild_date_customer_type(self,type_lst=False):
        res=[]
        if type_lst:
            if ',' in type_lst:
                for i in type_lst.split(','):
                    if SEARCH_TYPE_OBJ.get(i):
                        res.append([i,SEARCH_TYPE_OBJ.get(i)])
        else:
            res = []

        return res

    def get_children_category(self, category):
        list_category = category.ids
        if category.child_id:
            for child_category in category.child_id:
                list_category += self.get_children_category(child_category)
        return list_category

    @api.multi
    def convert_data_date_range(self):
        return [[a.id, a.name] for a in self.env['product.category'].search([])]


    @api.multi
    def get_html_and_data(self, context={}):
        result = {}
        report_data = self.env['ss.forecast.renew.service.report']
        report_id = report_data.search([('id_search_working', '=', self.id)], limit=1)


        date_merger = ''
        customer_type = ''
        check_merger = False
        specail_list = False
        category_ids = []
        not_category_ids = []

        # convert search category_ids
        if context.get('category_ids') or context.get('category_ids') == []:
            if context.get('category_ids') == []:
                category_ids=[]
            else:
                for i in context.get('category_ids'):
                    category_ids.append(int(i))
        else:
            if report_id:
                if report_id.category_ids:
                    category_ids = report_id.category_ids.ids
        # convert search not_category_ids
        if context.get('not_category_ids') or context.get('not_category_ids') == []:
            if context.get('not_category_ids') == []:
                not_category_ids=[]
            else:
                for i in context.get('not_category_ids'):
                    not_category_ids.append(int(i))
        else:
            if report_id:
                if report_id.not_category_ids:
                    not_category_ids = report_id.not_category_ids.ids


        # convert search customer_type
        if context.get('customer_type')  or context.get('customer_type') == []:
            if context.get('customer_type') == []:
                customer_type = []
            for i in context.get('customer_type'):
                customer_type = context.get('customer_type')
        else:
            if report_id:
                if report_id.customer_type:
                    customer_type = report_id.customer_type.split(',')




        if context.get('add_company_ids'):
            company_ids = context.get('add_company_ids')
        else:
            company_ids = self.env.user.company_id.id
        if report_id:
            pass
        else:
            report_id = report_data.create({
                'start_date': '2019-01-01',
                'quit_date': '2019-12-31',
                'id_search_working': self.id,
                'date_merger': '',
                'customer_type': 'snow',
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

        customer_type_tmp = ''
        #save data search
        if report_id:
            for i_customer_type in customer_type:
                customer_type_tmp = customer_type_tmp+','+i_customer_type
            report_id.customer_type = customer_type_tmp
            report_id.category_ids=[(6, 0, category_ids)]
            report_id.not_category_ids=[(6, 0, not_category_ids)]


        support_obj = self.sudo().env['support.report.data']
        support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)
        if support_report_data:
            support_report_data.date_merger = report_id.date_merger
            support_report_data.customer_type = customer_type_tmp
            support_report_data.category_ids=[(6, 0, category_ids)]
            support_report_data.not_category_ids=[(6, 0, not_category_ids)]
        else:
            support_obj.create({
                'date_merger': report_id.date_merger,
                'customer_type': customer_type_tmp,
                'category_ids': [(6, 0, category_ids)],
                'not_category_ids': [(6, 0, not_category_ids)]


                                })
        full_data = {}
        product_category_list_ids = []
        if date_merger != '':
            for i in date_merger:
                if i != '':
                    data_line, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],company_ids,customer_type_tmp)
                    product_category_list_ids+=product_category_list_id
                    full_data.update(data_line)

        product_category_obj = self.env['product.category']



        filter_company = [[c.id, c.name] for c in self.env['res.company'].search([])]

        category_ids_tmp=[]
        not_category_ids_tmp=[]
        if report_id.category_ids:
            for i_category_ids in report_id.category_ids:
                category_ids_tmp += self.get_children_category(i_category_ids)
        if report_id.not_category_ids:
            for i_not_category_ids in report_id.not_category_ids:
                not_category_ids_tmp += self.get_children_category(i_not_category_ids)

        if category_ids_tmp!=[] and not_category_ids_tmp!=[]:
            filter_product_category = [[c.id, c.name] for c in
                                       product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                   order="name asc") if
                                       c.id in category_ids_tmp and c.id not in not_category_ids_tmp]
        elif category_ids_tmp != []:
                filter_product_category = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc") if
                                           c.id in category_ids_tmp]
        elif not_category_ids_tmp != []:
                filter_product_category = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc") if
                                           c.id not in not_category_ids_tmp]
        else:
                filter_product_category = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc")]

        context = {
            'id': self.id,
            'report_type': {'comparison': False, 'extra_options': False, 'date_range': False},
            'date_filter': 'today',
            'available_ids':False
        }
        if self.with_context(**context)._context:
            date_list_context = self.with_context(**context)._context.get('date_list') or []

        rcontext = {
            'res_company': self.env['res.users'].browse(self.env.uid).company_id,
            'context': context,
            'report_type': {'date_range': 15, 'comparison': True},
            'report': report_id,
            'date_filter': '2020-01-01',
            'date_filter_cmp': '2020-01-01',
            'date_from': '2020-01-01',
            'date_to': '2020-12-01',
            'periods_number': '2020-01-01',
            'date_from_cmp': '2020-01-01',
            'date_to_cmp': '2020-01-01',
            'company_ids': filter_company,
            'product_category_id': [],#filter_product_category,
            'company_id_list': [company_ids],
            'date_list': date_merger,
            'product_category_id_list': filter_product_category,
            'lines': full_data,
            'columns_names': ['cột1', 'cột2', 'cột3'],
            'test_data': [1, 2, 2, 3, 5, 5, 4, 4, 4, 4, 4, 8],
            'footnotes': [],
            'mode': 'display',
        }
        # result = super(ReportHrEmployeeContext, self).get_html_and_data(given_context=given_context)
        result['html'] = self.env['ir.model.data'].xmlid_to_object('mb_custom_sales.report_ss_forecast_renew_service').render(
            rcontext)

        result['report_type'] = {'comparison': True, 'extra_options': False, 'date_range': True, 'density': False, 'available_ids':False}
        select = ['id', 'date_filter', 'date_filter_cmp', 'date_from', 'date_to', 'periods_number', 'date_from_cmp',
                  'date_to_cmp', 'company_ids', 'department_id']

        result['report_context'] = {
            'id': self.id,
            'date_filter': '2020-01-01',
            'date_filter_cmp': '2020-01-01',
            'date_from': '2020-01-01',
            'date_to': '2020-12-01',
            'periods_number': '2020-01-01',
            'date_from_cmp': '2020-01-01',
            'date_to_cmp': '2020-01-01',
            'company_ids': [],
            'category_ids': [],
            'comparison': True,

        }
        # lines = self.report_id.get_lines(self)
        # self.write({'report_id': report_id.id})
        available_fillter_ids = self.get_available_ids_and_names()
        result['available_companies'] = filter_company
        result['report_context']['available_ids'] = available_fillter_ids
        result['report_context']['category_ids'] = [(t_not.id, t_not.name) for t_not in report_id.category_ids]
        result['comparison'] = True
        result['available_ids'] = False
        result['report_context']['available_ids_name'] = 'Filter Product Category'
        result['comparison'] = True


        #reshow data selected
        result['report_context']['not_available_ids_name'] = 'Not Filter Product Category'
        result['report_context']['not_category_ids'] = [(t_not.id, t_not.name) for t_not in report_id.not_category_ids]
        result['report_context']['not_available_ids'] = available_fillter_ids



        #reshow data selected
        result['report_context']['available_customer_type_name'] = 'Filter Customer Type'
        result['report_context']['customer_type'] = self.rebuild_date_customer_type(customer_type_tmp)
        result['report_context']['available_customer_type'] = SEARCH_TYPE


        return result

    def get_pdf(self):

        for context in self:

            company_ids = self.env.user.company_id.id
            support_obj = self.sudo().env['support.report.data']
            report_obj = self.sudo().env['ss.forecast.renew.service.report']
            product_category_obj = self.sudo().env['product.category']
            support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)
            lines = {}
            time_line = []
            product_category_list_ids = []
            if ',' in support_report_data.date_merger:
                group_time = support_report_data.date_merger.split(',')
                for i in support_report_data.date_merger.split(','):
                    if i != '':
                        time_line.append([i.split(' to ')[0], i.split(' to ')[1]])

                        data_line, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],
                                                      self.env.user.company_id.id,support_report_data.customer_type)
                        product_category_list_ids += product_category_list_id

                        lines.update(data_line)
            else:
                group_time = [support_report_data.date_merger]
                i = support_report_data.date_merger
                data_line, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1], company_ids,support_report_data.customer_type)
                product_category_list_ids += product_category_list_id
                lines.update(data_line)


            base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env[
                'ir.config_parameter'].sudo().get_param('web.base.url')

            category_ids_tmp = []
            not_category_ids_tmp = []
            if support_report_data.category_ids:
                for i_category_ids in support_report_data.category_ids:
                    category_ids_tmp += self.get_children_category(i_category_ids)
            if support_report_data.not_category_ids:
                for i_not_category_ids in support_report_data.not_category_ids:
                    not_category_ids_tmp += self.get_children_category(i_not_category_ids)

            if category_ids_tmp != [] and not_category_ids_tmp != []:
                product_category_list_ids = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc") if
                                           c.id in category_ids_tmp and c.id not in not_category_ids_tmp]
            elif category_ids_tmp != []:
                product_category_list_ids = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc") if
                                           c.id in category_ids_tmp]
            elif not_category_ids_tmp != []:
                product_category_list_ids = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc") if
                                           c.id not in not_category_ids_tmp]
            else:
                product_category_list_ids = [[c.id, c.name] for c in
                                           product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                       order="name asc")]

            rcontext = {
                'mode': 'print',
                'base_url': base_url,
                'res_company': self.env.user.company_id,
                'company': self.env.user.company_id,
                'company_id_list': [self.env.user.company_id.id],
                'date_list': group_time,
                'product_category_id_list': product_category_list_ids,
                'lines': lines,
            }

            body = self.env['ir.ui.view'].render_template(
                "mb_custom_sales.report_ss_forecast_renew_service",
                values=dict(rcontext, lines=lines, report={}, context=self))

            header = self.env['report'].render("report.internal_layout", values=rcontext)
            header = self.env['report'].render("report.minimal_layout", values=dict(rcontext, subst=True, body=header))

            landscape = False
            if len(self.get_columns_names()) > 4:
                landscape = True
        return self.env['report']._run_wkhtmltopdf([header], [''], [(0, body)], landscape,
                                                   self.env.user.company_id.paperformat_id,
                                                   spec_paperformat_args={'data-report-margin-top': 10,
                                                                          'data-report-header-spacing': 10})

    def write_data_to_sheet(self,workbook,sheet,group_time,product_category_list_ids,lines):
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

        sheet.write(1, 0, 'Product Category', line_format)
        clu_h=1
        for i_key in group_time:
            sheet.write(0, clu_h, i_key, line_h_format)
            sheet.write(0, clu_h+1, '', line_h_format)
            sheet.write(1, clu_h, 'Total Forecast Renew', line_h_format)
            sheet.write(1, clu_h+1, 'Count Forecast Renew', line_h_format)
            clu_h+=2
        sheet.write(2, 0, self.env.user.company_id.name, line_format)
        row=3
        for i_product_category in product_category_list_ids:
            clu = 0
            sheet.write(row, clu, i_product_category[1], line_format)
            for i_key in group_time:
                if i_key !='department_list_id':
                    if lines.get(i_key + str(i_product_category[0])):
                        group_line = lines.get(i_key+str(i_product_category[0]))
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
        support_obj = self.sudo().env['support.report.data']
        product_category_obj = self.sudo().env['product.category']
        support_report_data = support_obj.sudo().search([('id', '=', 1)], limit=1)


        sheet = workbook.add_worksheet('Report')
        sheet2 = workbook.add_worksheet('Report Only Add On')
        sheet3 = workbook.add_worksheet('Report None Add On')
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
        product_category_list_ids = []

        company_ids = self.env.user.company_id.id
        if ','in support_report_data.date_merger:
            group_time = support_report_data.date_merger.split(',')
            for i in support_report_data.date_merger.split(','):
                if i != '':
                    time_line.append([i.split(' to ')[0],i.split(' to ')[1]])
                    data_line, product_category_list_id = self.get_data_rec(i.split(' to ')[0],i.split(' to ')[1],company_ids,support_report_data.customer_type)
                    data_line_addon, product_category_list_id = self.get_data_rec(i.split(' to ')[0],i.split(' to ')[1],company_ids,support_report_data.customer_type,'only add on')
                    data_line_none, product_category_list_id = self.get_data_rec(i.split(' to ')[0],i.split(' to ')[1],company_ids,support_report_data.customer_type,'none add on')
                    product_category_list_ids += product_category_list_id
                    full_data.update(data_line)
                    no_add_on_data.update(data_line_addon)
                    only_add_on_data.update(data_line_none)
        else:
            group_time = [support_report_data.date_merger]
            i = support_report_data.date_merger
            data_line, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],self.env.user.company_id.id,'full')
            data_line_addon, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],self.env.user.company_id.id,support_report_data.customer_type,'only add on')
            data_line_none, product_category_list_id = self.get_data_rec(i.split(' to ')[0], i.split(' to ')[1],self.env.user.company_id.id,support_report_data.customer_type,'none add on')
            product_category_list_ids += product_category_list_id
            full_data.update(data_line)
            no_add_on_data.update(data_line_addon)
            only_add_on_data.update(data_line_none)

        lines = full_data


        category_ids_tmp = []
        not_category_ids_tmp = []
        if support_report_data.category_ids:
            for i_category_ids in support_report_data.category_ids:
                category_ids_tmp += self.get_children_category(i_category_ids)
        if support_report_data.not_category_ids:
            for i_not_category_ids in support_report_data.not_category_ids:
                not_category_ids_tmp += self.get_children_category(i_not_category_ids)

        if category_ids_tmp != [] and not_category_ids_tmp != []:
            product_category_list_ids = [[c.id, c.name] for c in
                                         product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                     order="name asc") if
                                         c.id in category_ids_tmp and c.id not in not_category_ids_tmp]
        elif category_ids_tmp != []:
            product_category_list_ids = [[c.id, c.name] for c in
                                         product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                     order="name asc") if
                                         c.id in category_ids_tmp]
        elif not_category_ids_tmp != []:
            product_category_list_ids = [[c.id, c.name] for c in
                                         product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                     order="name asc") if
                                         c.id not in not_category_ids_tmp]
        else:
            product_category_list_ids = [[c.id, c.name] for c in
                                         product_category_obj.search([('id', 'in', product_category_list_ids)],
                                                                     order="name asc")]




        self.write_data_to_sheet(workbook,sheet,group_time,product_category_list_ids,lines)
        self.write_data_to_sheet(workbook,sheet2,group_time,product_category_list_ids,no_add_on_data)
        self.write_data_to_sheet(workbook,sheet3,group_time,product_category_list_ids,only_add_on_data)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
