# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import xlrd
import base64
import itertools
import logging

from datetime import datetime, timedelta

try:
    from odoo.addons.report_xlsx_trobz.utils import _render  # @UnresolvedImport
    from odoo.addons.report_xlsx_trobz import report_xlsx_utils  # @UnresolvedImport
except:
    from odoo.api import Environment
from odoo.report import report_sxw
from odoo.report.report_sxw import report_sxw
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from cStringIO import StringIO
from collections import OrderedDict
from odoo.api import Environment

import logging
_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')

_logger = logging.getLogger(__name__)
SERVICE_STATUS = [("draft", "Draft"),
                  ("waiting", "Waiting for Activation"),
                  ("done", "Done"),
                  ("refused", "Refused")]






class replay_action_coupon(models.TransientModel):
    _name = "replay.action.coupon"

    upload_file = fields.Binary(string="Upload File")
    sql_active = fields.Boolean(string="active")

    file_name = fields.Char(string="File Name")
    line_number = fields.Integer(string="line run")
    description = fields.Text('Description')
    description_return = fields.Text('description return')



    @api.multi
    def run_btn(self):
        if self._uid not in (1,979,533):
            raise Warning("Your Account can run this action sorry")

        file_data = self.upload_file.decode('base64')
        wb = xlrd.open_workbook(file_contents=file_data)
        sheet = wb.sheet_by_index(0)
        obj_cph = self.env['customer.promotion.history']
        obj_coupon = self.env['mb.coupon']
        obj_so = self.env['sale.order']

        runing_note=''


        for row in itertools.imap(sheet.row, range(sheet.nrows)):
            for cell in row:
                logging.info(cell.value)
                coupon = obj_coupon.sudo().search([('name','=',str(cell.value))],limit = 1)
                if coupon:
                    for order_id in obj_so.sudo().search([('coupon', '=', str(cell.value))]):
                        if obj_cph.sudo().search([('order_id', '=', order_id.id)], limit=1):
                            runing_note = runing_note + ' Code Created ' + str(cell.value) + ' Skip ' + str(order_id.name)
                        else:

                            rsl, check_action = order_id.check_valid_promotion()
                            inv = order_id.sudo().mapped('invoice_ids').filtered(lambda inv: inv.state == 'paid')
                            if inv:
                                if rsl:
                                    for rsl_i in rsl:
                                        try:
                                            inv.sudo().action_enforce_promotion(inv, order_id, rsl_i, check_action)
                                        except:
                                            runing_note = runing_note + ' Have problem by Code '+str(cell.value)+' this action not work' + str(order_id.name)
                                    order_id.created_coupon = True
                            else:
                                runing_note = runing_note + ' Have problem by invoice this code ' + str(
                                    cell.value) + ' this action not work' + str(order_id.name)
                else:
                    runing_note = runing_note + ' Code '+str(cell.value)+' Not viable'
        res = runing_note
        self.description_return=res





class report_jounal_invoice_line_wizard_line(models.TransientModel):
    _name = 'report.jounal.invoice.line.wizard.line'
    report_jounal_invoice_line_wizard_id = fields.Many2one('report.jounal.invoice.line.wizard', string='report')


    account_journal_id = fields.Many2one('account.journal', 'Journal')
    product_category_id = fields.Many2one('product.category', 'Product Category')
    product_id = fields.Many2one('product.product', 'Product')
    product_template_id = fields.Many2one('product.template', 'Product')
    price_subtotal = fields.Float('Subtotal')
    vat_status = fields.Selection([('new', 'Draft'), ('to_export', 'Open'), ('exported', 'Done'),
                                   ('cancel', 'Cancel'), ('lost', 'Lose'), ('refuse', 'Refuse')],
                                  string='VAT Invoice Status')
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    partner_id = fields.Many2one('res.partner',related='invoice_id.partner_id', string="Customer")
    date_invoice = fields.Date(related='invoice_id.date_invoice', string="Invoice Date")
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice Line')






class report_jounal_invoice_line_wizard(models.TransientModel):
    _name = 'report.jounal.invoice.line.wizard'


    account_journal_ids = fields.Many2many('account.journal', 'account_journal_report_jounal_rel', 'account_journal_id', 'report_jounal_rel', string='Journal')
    product_category_ids = fields.Many2many('product.category', 'report_jounal_invoice_line_product_product_category',
                                                  'report_jounal_invoice_line_id', 'product_category_id', "Product Category")

    vat_status = fields.Selection([('new', 'Draft'), ('to_export', 'Open'), ('exported', 'Done'),
                                   ('cancel', 'Cancel'), ('lost', 'Lose'), ('refuse', 'Refuse')], string='VAT Invoice Status', default='new')
    is_draft = fields.Boolean(string="Draft")
    is_open = fields.Boolean(string="Open")
    is_done = fields.Boolean(string="Done")
    is_cancel = fields.Boolean(string="Cancel")
    is_lose = fields.Boolean(string="Lose")
    is_refuse = fields.Boolean(string="Refuse")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    invoice_line_ids_str = fields.Char(string='invoice line ids str')
    account_invoice_line_ids = fields.Many2many('account.invoice.line', 'account_invoice_line_report_jounal_rel', 'account_invoice_line_id', 'report_jounal_id', string='Sale Order Line')
    report_jounal_invoice_line_wizard_line = fields.One2many('report.jounal.invoice.line.wizard.line', 'report_jounal_invoice_line_wizard_id', string='Line')
    partner_id = fields.Many2one('res.partner', 'Customer')





    @api.multi
    def button_search(self):
        if self.start_date and self.end_date:
            self.write({'report_jounal_invoice_line_wizard_line': [(5, 0,)]})

            coupon_list=[]
            args=[]
            vat_status=[]
            args += [('create_date', '>=', self.start_date),('create_date', '<=', self.end_date)]
            args += [('company_id', '>=', self.env.user.company_id.id)]


            if self.is_draft:
                vat_status.append('new')
            if self.is_open:
                vat_status.append('to_export')
            if self.is_done:
                vat_status.append('exported')
            if self.is_cancel:
                vat_status.append('cancel')
            if self.is_lose:
                vat_status.append('lost')
            if self.is_refuse:
                vat_status.append('refuse')
            # not_this_product = []
            # for i in self.env['res.company'].search([]):
            #     if i.product_id.id:
            #         not_this_product.append(i.product_id.id)
            # if not_this_product != []:
            #     not_this_product = str(not_this_product).replace('[', '(')
            #     not_this_product = not_this_product.replace(']', ')')

            account_id = 9

            if self.env.user.company_id.id == 3:
                account_id = 389
            sql='''
            select ail.id, ai.id as "Invoice", pc.id as "Category", pt.id as "Product", ail.price_subtotal as "Subtotal", aj.id as "Journal", ail.vat_status as "VAT Status", ail.register_type
            from account_invoice ai 
            inner join account_invoice_line ail on ail.invoice_id = ai.id
            inner join product_product pp on pp.id = ail.product_id
            inner join product_template pt on pt.id = pp.product_tmpl_id
            inner join product_category pc on pc.id = pt.categ_id
            inner join account_move am on am.id = ai.move_id
            inner join account_move_line aml on aml.move_id = am.id and aml.account_id = '''+str(account_id)+ ''' 
            
            inner join account_partial_reconcile apr on apr.debit_move_id = aml.id
            inner join account_move_line aml1 on aml1.id = apr.credit_move_id
            inner join account_move am1 on am1.id = aml1.move_id
            inner join account_journal aj on aj.id = am1.journal_id
            where
            ai.type = 'out_invoice' 
            and
            (
            ail.price_subtotal >= 0
            )
            and
            ai.date_invoice between '''
            sql+="'"+self.start_date+"' and '"+self.end_date +"'"
            sql+='  and ai.company_id ='+str(self.env.user.company_id.id)
            if self.partner_id:
                sql += '  and ai.partner_id = ' + str(self.partner_id.id)

            if vat_status != []:
                vat_status = str(vat_status).replace('[', '(')
                vat_status = vat_status.replace(']', ')')
                sql += '  and ail.vat_status in' + vat_status
            if self.account_journal_ids:
                account_journal_ids = str(self.account_journal_ids.ids).replace('[', '(')
                account_journal_ids = account_journal_ids.replace(']', ')')
                sql += 'and  aj.id in '+account_journal_ids
            if self.product_category_ids:
                list_product = []
                for i in self.product_category_ids:
                    list_product.append(i.id)
                    list_product += self.env['product.category'].search([('parent_id','=',i.id)]).ids
                product_category_ids = str(list_product).replace('[', '(')
                product_category_ids = product_category_ids.replace(']', ')')
                sql += 'and  pc.id in '+product_category_ids

            self._cr.execute(sql)
            account_invoice_line_ids_tmp = []
            account_invoice_line_ids = []
            invoice_ids_upgrade = []
            for r in self._cr.fetchall():
                account_invoice_line_ids_tmp.append(r[0])

                self.env['report.jounal.invoice.line.wizard.line'].create({'report_jounal_invoice_line_wizard_id':self.id,
                                                                            'invoice_id': r[1],
                                                                            'product_category_id': r[2],
                                                                            'product_template_id': r[3],
                                                                            'price_subtotal': r[4],
                                                                            'account_journal_id': r[5],
                                                                            'vat_status': r[6]
                                                                            }
                                                                      )
                if r[7] == 'upgrade':
                    invoice_ids_upgrade.append(r[1])
            if invoice_ids_upgrade != []:
                invoice_ids_upgrade = str(invoice_ids_upgrade).replace('[', '(')
                invoice_ids_upgrade = invoice_ids_upgrade.replace(']', ')')
                sql = '''
                            select ail.id, ai.id as "Invoice", pc.id as "Category", pt.id as "Product", ail.price_subtotal as "Subtotal", aj.id as "Journal", ail.vat_status as "VAT Status"
                            from account_invoice ai 
                            inner join account_invoice_line ail on ail.invoice_id = ai.id
                            inner join product_product pp on pp.id = ail.product_id
                            inner join product_template pt on pt.id = pp.product_tmpl_id
                            inner join product_category pc on pc.id = pt.categ_id
                            inner join account_move am on am.id = ai.move_id
                            inner join account_move_line aml on aml.move_id = am.id and aml.account_id = 9
                            inner join account_partial_reconcile apr on apr.debit_move_id = aml.id
                            inner join account_move_line aml1 on aml1.id = apr.credit_move_id
                            inner join account_move am1 on am1.id = aml1.move_id
                            inner join account_journal aj on aj.id = am1.journal_id
                            where
                            ai.type = 'out_invoice'                           
                            and ai.id in 
                            '''
                sql+= invoice_ids_upgrade
                sql+=''' and ail.price_subtotal > 0 '''
                # and pp.id in '''
                # sql+=not_this_product

                self._cr.execute(sql)
                for r in self._cr.fetchall():
                    account_invoice_line_ids_tmp.append(r[0])
                    if r[1] == 'upgrade':
                        invoice_ids_upgrade.append(r[7])
                    self.env['report.jounal.invoice.line.wizard.line'].create({'report_jounal_invoice_line_wizard_id':self.id,
                                                                               'invoice_id': r[1],
                                                                               'product_category_id': r[2],
                                                                               'product_template_id': r[3],
                                                                               'price_subtotal': r[4],
                                                                               'account_journal_id': r[5],
                                                                               'vat_status': r[6]
                                                                               }
                                                                              )

            for i in OrderedDict.fromkeys(account_invoice_line_ids_tmp):
                account_invoice_line_ids.append(i)
            self.invoice_line_ids_str=str(account_invoice_line_ids)



    @api.multi
    def button_create_vat_invoice(self):
        self.env['mb.export.invoice'].create({'invoice_line_ids':[(6,0,eval(self.invoice_line_ids_str))],
                                              'state':'new'
                                                               }
                                                              )
        sql = '''UPDATE account_invoice_line
                SET vat_status = 'export_to', vat_no_id = Null                
                WHERE
                id in %s;'''% (self.invoice_line_ids_str.replace('[', '(')).replace(']', ')')

        self._cr.execute(sql)



    @api.multi
    def button_export(self):

        datas = {'ids': self and self.ids or []}
        datas['model'] = 'report.jounal.invoice.line.wizard'
        datas['form'] = self.sudo().read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'report_jounal_invoice_line_wizard',
                'datas': datas,
                'name': 'report_jounal_invoice_line_wizard'
                }

report_jounal_invoice_line_wizard()





class report_jounal_invoice_line_wizard_Xlsx(ReportXlsx):


    def generate_title(self,wb, sheet1):
        format_title = wb.add_format(
            {'font_size': 13, 'bold': True, 'font_name': 'Times New Roman',  'align': 'center', 'bg_color': '#DDADDD',
             'valign': 'vcenter', 'text_wrap': True})
        lst = ['No','Invoice','Invoice Date','Customer','Product Category','Product','Subtotal','Journal','VAT Invoice Status']

        row = 0
        size_30_colum=[]
        size_25_colum=[3]
        size_15_colum=[1,4,5]
        size_10_colum=[2,6]
        size_5_colum = [0,8]
        for i in range(len(lst)):
            sheet1.write(row, i, lst[i], format_title)
            if i in size_5_colum:
                sheet1.set_column(i, i, 5)
            elif i in size_10_colum:
                sheet1.set_column(i, i, 10)
            elif i in size_15_colum:
                sheet1.set_column(i, i, 15)
            elif i in size_25_colum:
                sheet1.set_column(i, i, 25)
            elif i in size_30_colum:
                sheet1.set_column(i, i, 30)
            else:
                sheet1.set_column(i, i, 15)



    def generate_xlsx_report(self, workbook, data, objs):
        header_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 12,
            'bg_color': '#FFF00',
            'text_wrap': True,
        })

        line_center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 10,
            'text_wrap': True,
        })

        line_left_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 10,
            'text_wrap': True,
        })
        line_right_format = workbook.add_format({
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman', 'font_size': 10,
            'text_wrap': True,
        })


        i = 1
        sheet = workbook.add_worksheet(u'Danh Sách Invoice Journal')
        sheet.set_column(0, 0, 11)
        sheet.write(i, 0, 'Code', header_format)
        convert={'new':'Draft',
                 'to_export':'Open',
                 'exported':'Done',
                 'cancel':'Cancel',
                 'lost':'Lose',
                 'refuse':'Refuse'}
        self.generate_title(workbook, sheet)
        for i_data in objs.report_jounal_invoice_line_wizard_line:
            sheet.write(i, 0, i, line_center_format)
            sheet.write(i, 1, i_data.invoice_id.number, line_left_format)
            sheet.write(i, 2, i_data.date_invoice, line_center_format)
            sheet.write(i, 3, '['+i_data.partner_id.ref+'] ' + i_data.partner_id.name, line_left_format)
            sheet.write(i, 4, i_data.product_category_id.name, line_left_format)
            sheet.write(i, 5, i_data.product_template_id.name, line_left_format)
            sheet.write(i, 6, i_data.price_subtotal, line_right_format)
            sheet.write(i, 7, i_data.account_journal_id.name, line_center_format)
            sheet.write(i, 8, convert.get(i_data.vat_status), line_center_format)
            i+=1
        workbook.close()

report_jounal_invoice_line_wizard_Xlsx('report.report_jounal_invoice_line_wizard', 'report.jounal.invoice.line.wizard')

