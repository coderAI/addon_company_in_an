# -*- coding: utf-8 -*-
import random
import string
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
from datetime import datetime, timedelta
import urllib2
import urllib
import json
from odoo.tools.float_utils import float_compare


def randomString(stringLength):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(stringLength))


class chili_affiliate_program(models.Model):
    _name = 'chili.affiliate.program'
    _inherit = ['mail.thread']
    name = fields.Char(string='Name', required=True, track_visibility='onchange')
    matrix_type = fields.Selection([("f", "Fixed"), ("p", "Percentage")], string="Matrix type", default='p',
                                   track_visibility='onchange')
    amount = fields.Float(string="Amount", required=True, track_visibility='onchange')
    product_category_ids = fields.Many2many('product.category', 'affp_pc', 'pc_id', 'affp_id',
                                            string='Product Category')


class chili_affiliate(models.Model):
    _name = 'chili.affiliate'
    _inherit = ['mail.thread']
    name = fields.Char(string='Name', track_visibility='onchange')
    address = fields.Char(string='Address', track_visibility='onchange')
    email = fields.Char(string='Email', track_visibility='onchange')
    phone = fields.Char(string='Phone', track_visibility='onchange')
    description = fields.Html(string='Description')
    date = fields.Date(string="Date", default=datetime.today())
    url_referrer = fields.Char(string='Url Referrer')
    aff_user_id = fields.Many2one('chili.affiliate.user', string='User', required=True, track_visibility='onchange')
    lead_id = fields.Many2one('crm.lead', string='Lead', track_visibility='onchange')
    referrer_name = fields.Char(string='Referrer name', track_visibility='onchange')


class chili_affiliate_user(models.Model):
    _name = 'chili.affiliate.user'
    _inherit = ['mail.thread']

    def getdefault_affkey(self):
        return randomString(16).lower()

    name = fields.Char(string='Name', required=True, track_visibility='onchange')
    login = fields.Char(string='Login Name', required=True, track_visibility='onchange')
    password = fields.Char(string='Password', required=True)
    state = fields.Selection([("draft", "draft"), ("approved", "approved")], string="State", default='draft',
                             track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    aff_key = fields.Char(string='Affiliate key', required=True, readonly=True, default=getdefault_affkey,
                          track_visibility='onchange')
    aff_program_id = fields.Many2one('chili.affiliate.program', string='Program', required=True,
                                     track_visibility='onchange')
    aff_link = fields.Char(string="Affiliate Link", store=False, readonly=True, compute='_gen_aff_link',
                           track_visibility='onchange')
    last_logon = fields.Datetime(string="Last logon")

    @api.depends('aff_key')
    def _gen_aff_link(self):
        for aff in self:
            if aff.aff_key:
                config_parameter_obj = self.env['ir.config_parameter']
                setting_url = config_parameter_obj.get_param('affiliate.config.settings.setting_aff_url',
                                                             default='https://ref.chili.vn/affiliate/?key=')
                aff.aff_link = '{0}{1}'.format(setting_url, aff.aff_key)

    @api.model
    def create(self, vals):
        l = self.env["chili.affiliate.user"].search_count([('login', '=', vals.get('login'))])
        if l > 0:
            raise Warning(_("Login already exists!"))
            return
        random_key = randomString(16).lower()
        c = self.env["chili.affiliate.user"].search_count([('aff_key', '=', random_key)])
        while c > 0:
            random_key = randomString(16).lower()
            c = self.env["chili.affiliate.user"].search_count([('aff_key', '=', random_key)])
        vals.update({'aff_key': random_key})
        res = super(chili_affiliate_user, self).create(vals)
        return res


class ChiliAffiliateSettings(models.TransientModel):
    _name = 'affiliate.config.settings'
    _inherit = 'res.config.settings'

    setting_account_id = fields.Many2one('account.account', string='Refund Account', required=True)
    setting_aff_url = fields.Char(string="Affiliate Url", required=True)

    @api.multi
    def set_setting_account_id(self):
        self.env['ir.config_parameter'].set_param('affiliate.config.settings.setting_account_id',
                                                  self[0].setting_account_id.id, groups=["base.group_system"])

    @api.model
    def get_default_setting_account_id(self, fields):
        params = self.env['ir.config_parameter']
        setting_account_id = params.get_param('affiliate.config.settings.setting_account_id', False)
        if setting_account_id:
            return {'setting_account_id': int(setting_account_id)}
        return {'setting_account_id': ''}

    @api.multi
    def set_setting_aff_url(self):
        self.env['ir.config_parameter'].set_param('affiliate.config.settings.setting_aff_url', self[0].setting_aff_url,
                                                  groups=["base.group_system"])

    @api.model
    def get_default_setting_aff_url(self, fields):
        params = self.env['ir.config_parameter']
        setting_aff_url = params.get_param('affiliate.config.settings.setting_aff_url', default='https://ref.chili.vn/affiliate/?key=')
        return {'setting_aff_url': setting_aff_url}


class CRMLead(models.Model):
    _inherit = 'crm.lead'
    aff_id = fields.Many2one('chili.affiliate', string='Affiliate')
    aff_key = fields.Char(string='Affiliate key', readonly=True)
    aff_user_id = fields.Many2one('chili.affiliate.user', string='User', required=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    aff_refunds = fields.Float(string='Aff Refunds', compute='_calculator_aff_refunds')

    @api.depends('price_subtotal')
    def _calculator_aff_refunds(self):
        for so_line in self:
            order = self.env['sale.order'].browse(so_line.order_id.id)
            if order:
                if order.opportunity_id:
                    aff_program = order.opportunity_id.aff_user_id.aff_program_id
                    if aff_program:
                        if aff_program.matrix_type == 'p':
                            so_line.aff_refunds = so_line.price_subtotal * (aff_program.amount / 100)
                        else:
                            so_line.aff_refunds = aff_program.amount

