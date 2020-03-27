# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from openerp.addons.mail.models.mail_template import format_tz
import logging as _logger

class ExternalPage(models.AbstractModel):
    _description = 'Page API'
    _name = 'external.page'

    @api.model
    def get_page_by_category(self, category, content=1):
        res = {'"code"': 0, '"msg"': '""'}
        DocumentPage = self.env['document.page']
        if not category:
            res['"msg"'] = '"Category could not be empty"'
            return res
        # _logger.info("===================================== %s ======================================" % type(category))
        if type(category) is int:
            category_id = DocumentPage.browse(category)
        else:
            category_id = DocumentPage.search([('name', '=', category)])
        if not category_id:
            res['"msg"'] = '"Category not exists"'
            return res
        page_ids = DocumentPage.search([('parent_id', '=', category_id.id)], order='create_date desc')
        data = []
        try:
            for page in page_ids:
                item = {}
                item.update({
                    '"id"': page.id or '""',
                    '"name"': '\"' + (page.name or '') + '\"',
                    '"create_date"': '\"' + (page.create_date and format_tz(self.env, page.create_date, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                    '"write_date"': '\"' + (page.write_date and format_tz(self.env, page.write_date, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                    '"write_uid"': '\"' + (page.write_uid and page.write_uid.name or '') + '\"',
                    '"summary"': '\"' + (page.summary or '') + '\"',
                })
                if content == 1:
                    item.update({
                        '"content"': '\"' + (page.content and str(page.content.replace("\'", "\\\'").replace("\"", "\\\"").encode('utf-8')) or '') + '\"'
                    })
                data.append(item)
        except Exception as e:
            _logger.error("Error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not get content: %s"' % (e.message or repr(e))}
        return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}

    @api.model
    def get_page_info(self, page_id):
        res = {'"code"': 0, '"msg"': '""'}
        DocumentPage = self.env['document.page']
        if not page_id:
            res['"msg"'] = '"Page ID could not be empty"'
            return res
        page = DocumentPage.browse(page_id)
        if not page:
            res['"msg"'] = '"Page not exists"'
            return res
        data = []
        try:
            data.append({
                '"name"': '\"' + (page.name or '') + '\"',
                '"content"': '\"' + (page.content and str(page.content.replace("\'","\\\'").replace("\"","\\\"").encode('utf-8')) or '') + '\"',
                '"create_date"': '\"' + (page.create_date and format_tz(self.env, page.create_date, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                '"write_date"': '\"' + (page.write_date and format_tz(self.env, page.write_date, tz=self.env.user.tz, format='%Y-%m-%d %H:%M:%S') or '') + '\"',
                '"write_uid"': '\"' + (page.write_uid and page.write_uid.name or '') + '\"',
                '"summary"': '\"' + (page.summary or '') + '\"',
            })
        except Exception as e:
            _logger.error("Error: %s" % (e.message or repr(e)))
            return {'"code"': 0, '"msg"': '"Can not get content: %s"' % (e.message or repr(e))}
        return {'"code"': 1, '"msg"': '"Successfully"', '"data"': data}