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
from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import Warning
import logging
from datetime import datetime

import json

import logging

_logger = logging.getLogger(__name__)

NAME='Tên miền'
READ_FIELDS=['id','name', 'seen_check','display_content','create_date','write_date']

class ProductProduct(models.Model):
    _inherit = 'document.page'

    partner_id = fields.Many2one('res.partner', string='Partner')
    seen_check = fields.Boolean('Seen')

    @api.model
    def get_document_page(self,res_partner_ref):
        data=[]
        messages='Successfully'
        code=200
        res_partner_obj = self.env['res.partner']
        document_page_obj = self.env['document.page']
        res_partner = res_partner_obj.sudo().search([('ref', '=', res_partner_ref)],limit=1)
        if res_partner:
            data = document_page_obj.search([('partner_id','=',res_partner.id)]).read(READ_FIELDS)
        else:
            messages='your customer ref not in system'
            code=402
        res = {'code': code, 'messages':messages,'data':data}
        return json.dumps(res)

    @api.model
    def set_document_page_seen(self,res_partner_ref,document_page_id):
        data=[]
        messages='Successfully'
        code=200
        document_page_obj = self.env['document.page']
        res_partner_obj = self.env['res.partner']
        res_partner = res_partner_obj.sudo().search([('ref', '=', res_partner_ref)],limit=1)
        if res_partner:
            if document_page_id == 'all':
                document_page = document_page_obj.search([('partner_id','=',res_partner.id)])
            else:
                document_page = document_page_obj.search([('partner_id','=',res_partner.id),('id','=',document_page_id)])
            document_page.write({
            'seen_check': True})
        else:
            messages='your customer ref not in system'
            code=402
        res = {'code': code, 'messages':messages}
        return json.dumps(res)

class ExternalPage(models.AbstractModel):
    _inherit = 'external.page'


    @api.model
    def get_page_by_category(self, category, content=1):
        res = {'"code"': 0, '"msg"': '""'}
        DocumentPage = self.env['document.page']
        if not category:
            res['"msg"'] = '"Category could not be empty"'
            return res

        if type(category) is int:
            category_id = DocumentPage.browse(category)
        else:
            category_id = DocumentPage.search([('name', '=', category),('partner_id','=',False)])
        if not category_id:
            res['"msg"'] = '"Category not exists"'
            return res
        page_ids = DocumentPage.search([('parent_id', '=', category_id.id),('partner_id','=',False)], order='create_date desc')
        data = []
        try:
            for page in page_ids:
                item = {}
                item.update({
                    '"id"': page.id or '""',
                    '"name"': '\"' + (page.name or '') + '\"',
                    '"create_date"': '\"' + (
                                page.create_date and format_tz(self.env, page.create_date, tz=self.env.user.tz,
                                                               format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                    '"write_date"': '\"' + (
                                page.write_date and format_tz(self.env, page.write_date, tz=self.env.user.tz,
                                                              format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                    '"write_uid"': '\"' + (page.write_uid and page.write_uid.name or '') + '\"',
                    '"summary"': '\"' + (page.summary or '') + '\"',
                })
                if content == 1:
                    item.update({
                        '"content"': '\"' + (page.content and str(
                            page.content.replace("\'", "\\\'").replace("\"", "\\\"").encode('utf-8')) or '') + '\"'
                    })
                data.append(item)
        except Exception as e:
            _logger.error("Error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not get content: %s"' % (e.message or repr(e))}
        return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}