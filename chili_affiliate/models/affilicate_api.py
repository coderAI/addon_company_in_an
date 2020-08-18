# coding=utf-8
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare
from openerp.addons.mail.models.mail_template import format_tz
import logging as _logger
from datetime import datetime, timedelta


class ExternalAffilicate(models.AbstractModel):
    _description = 'Affilicate API'
    _name = 'external.affilicate.api'

    @api.model
    def create_affiliate(self, aff_key, name, email, phone, address, description, url_referrer, referrer_name):
        res = {'"code"': 0, '"msg"': '""'}
        aff_user = self.env['chili.affiliate.user'].search([('aff_key', '=', aff_key)])
        if not aff_key:
            res['"msg"'] = '"Key chương trình liên kết không thể rỗng."'
            return res
        if not email:
            res['"msg"'] = '"Email không thể rỗng."'
            return res

        if not phone:
            res['"msg"'] = '"Phone không thể rỗng."'
            return res

        aff = self.env['chili.affiliate'].create({
            'name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'description': description,
            'url_referrer': url_referrer,
            'aff_user_id': aff_user.id,
            'referrer_name': referrer_name})

        # Lead source
        lead_source = self.env['utm.source'].search([('name', '=', 'CHILI Affiliate')], limit=1)
        if not lead_source:
            lead_source = self.env['utm.source'].create({'name': 'CHILI Affiliate'})
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        CrmLead = self.env['crm.lead'].create({
            'type': 'lead',
            'name': name,
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'mobile': phone,
            'street': address,
            'description': description,
            'aff_key': aff_key,
            'aff_user_id': aff_user.id,
            'aff_id': aff.id,
            'company_id': aff_user.partner_id.user_id.company_id.id,
            'country_id': country.id,
            'source_id': lead_source.id,
            'team_id': 35,
            'referred': url_referrer
        })
        aff.write({'lead_id': CrmLead.id})
        if CrmLead:
            res['"code"'] = 1
            res['"msg"'] = '"Success"'
        return res


    @api.model
    def create_lead_chili(self, name, email, phone, address, description, url_referrer, campaign, source, tag):
        res = {'"code"': 0, '"msg"': '""'}

        if not email:
            res['"msg"'] = '"Email không thể rỗng."'
            return res

        if not phone:
            res['"msg"'] = '"Phone không thể rỗng."'
            return res

        CrmTeam = self.env['crm.team'].search([('active', '=', True)], limit=1)
        crm_team_max = self.env['crm.team'].search([('active', '=', True)], limit=1)

        # Lead source
        if not source:
            source = "Default"

        lead_source = self.env['utm.source'].search([('name', '=', source)], limit=1)
        if not lead_source:
            lead_source = self.env['utm.source'].create({'name': source})

        # Lead campaign
        if not campaign:
            campaign = "Default"
        lead_campaign = self.env['utm.campaign'].search([('name', '=', campaign)], limit=1)
        if not lead_campaign:
            lead_campaign = self.env['utm.campaign'].create({'name': campaign})
        # Country
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        # Tags
        if not tag:
            tag = 'Default'
        lead_tag = self.env['crm.lead.tag'].search([('name', '=', tag)], limit=1)
        if not lead_tag:
            lead_tag = self.env['crm.lead.tag'].create({'name': tag})
        CrmLead = self.env['crm.lead'].create({
            'type': 'lead',
            'name': name,
            'contact_name': name,
            'email_from': email,
            'phone': phone,
            'mobile': phone,
            'street': address,
            'description': description,
            'company_id': 1,
            'country_id': country.id,
            'source_id': lead_source.id,
            'campaign_id': lead_campaign.id,
            'team_id': CrmTeam.id,
            'referred': url_referrer,
            'tag_ids': [(6, 0, {lead_tag.id})]
        })


        cr = self.env.cr
        cr.execute("select id from res_users where sale_team_id=%s limit 1",
                   (CrmTeam.id,))
        res_users_id = cr.fetchone()[0]
        CrmLead.write({'user_id': res_users_id})
        # self.env.cr.execute(
        #     "update crm_team_res_users_rel set rotation=(select rotation from crm_team_res_users_rel where crm_team_id=%s order by rotation desc limit 1)+1 where crm_team_id=%s and res_users_id=%s",
        #     (CrmTeam.id, CrmTeam.id, res_users_id,))
        #self.env.cr.commit()
        if CrmLead:
            res['"code"'] = 1
            res['"msg"'] = '"Success"'
        return res

    @api.model
    def affiliate_login(self, login_name, login_password):
        res = {'"code"': 0, '"msg"': '""'}
        if not login_name:
            res['"msg"'] = '"Vui lòng nhập tên đăng nhập."'
            return res
        if not login_password:
            res['"msg"'] = '"Vui lòng nhập mật khẩu."'
            return res
        user_login = self.env['chili.affiliate.user'].search(
            [('login', '=', login_name), ('password', '=', login_password)],
            limit=1)
        if not user_login:
            res['"msg"'] = '"Đăng nhập không hợp lệ! Kiểm tra lại tên đăng nhập và mật khẩu."'
            return res
        if user_login.state != 'approved':
            res['"msg"'] = '"Đăng nhập không hợp lệ! Tài khoản chưa chứng thực."'
            return res
        if user_login:
            res['"msg"'] = '"Success"'
            res['"code"'] = 1
            self.env['chili.affiliate.user'].browse(user_login.id).write({'last_logon': datetime.now()})
            return res
        return res

    @api.model
    def affiliate_customer_list(self, login_name):
        res = {'"code"': 0, '"msg"': '""', '"data"': '""'}
        user = self.env['chili.affiliate.user'].search([('login', '=', login_name), ('state', '=', 'approved')],
                                                       limit=1)
        if user:
            customers = self.env['chili.affiliate'].search([('aff_user_id', '=', user.id), ('lead_id', '!=', False)],
                                                           order="id desc")
            if customers:
                res['"code"'] = 1
                data = []
                for c in customers:
                    so_stage = '(Chưa tạo)'
                    amount_total = 0.0
                    so = self.env['sale.order'].search([('opportunity_id', '=', c.lead_id.id)], limit=1)
                    stage_lead = 'Chưa tiếp nhận'
                    if c.lead_id.type == 'lead':
                        stage_lead = 'Chưa tiếp nhận'
                    if c.lead_id.type == 'opportunity':
                        stage_lead = 'Đang xử lý'
                    if so:
                        amount_total = so.amount_untaxed - (so.amount_discount or 0.0)
                        so_stage = so.name
                        if so.fully_paid:
                            stage_lead = 'Đã thanh toán'
                        else:
                            stage_lead = 'Chưa thanh toán'
                    data.append(
                        {
                            '"id"': c.id,
                            '"name"': '\"' + c.name + '\"',
                            '"phone"': '\"' + c.phone + '\"',
                            '"email"': '\"' + c.email + '\"',
                            '"address"': '\"' + (c.address or '') + '\"',
                            '"create_date"': '\"' + c.date + '\"',
                            '"stage_lead"': '\"' + stage_lead + '\"',
                            '"stage_so"': '\"' + so_stage + '\"',
                            '"sale_person"': '\"' + c.lead_id.user_id.name + '\"',
                            '"referrer_name"': '\"' + (c.referrer_name or '') + '\"',
                            '"amount_total"': '\"' + (str(amount_total) or '0') + '\"'
                        })

                res['"data"'] = data
        return res

    @api.model
    def affiliate_log_activities(self, login_name, affiliate_id):
        res = {'"code"': 0, '"msg"': '""', '"data"': '""'}
        user = self.env['chili.affiliate.user'].search([('login', '=', login_name), ('state', '=', 'approved')],
                                                       limit=1)
        if user:
            affilate = self.env["chili.affiliate"].browse(affiliate_id)
            if affilate:
                res['"code"'] = 1
                # sub_types = self.env['mail.message.subtype'].search[('res_model', '=', 'crm.lead')]
                log_activity = self.env['mail.message'].search(
                    [('res_id', '=', affilate.lead_id.id), ('model', '=', 'crm.lead'),
                     ('subtype_id', 'in', [2, 14, 15, 16, 17, 18, 19, 20]),
                     ('message_type', 'in', ['notification', 'comment']),
                     ('body', '!=', ''),
                     ('author_id', '!=', 3)],
                    order='date desc')
                data = []
                for l in log_activity:
                    data.append({
                        '"id"': '\"' + str(l.id) + '\"',
                        '"subject"': '\"' + (l.subject or '') + '\"',
                        '"body"': '\"' + (l.body or '') + '\"',
                        '"date"': '\"' + l.date + '\"',
                        '"subtype"': '\"' + l.subtype_id.name + '\"',
                        '"author"': '\"' + l.author_id.name + '\"',
                    })
                res['"data"'] = data
        return res


    @api.model
    def affiliate_user_profile(self, login_name):
        res = {'"code"': 0, '"msg"': '""', '"data"': '""'}
        user = self.env['chili.affiliate.user'].search([('login', '=', login_name), ('state', '=', 'approved')],
                                                       limit=1)
        if user:
            res['"code"'] = 1
            data = []
            data.append({
                '"name"': '\"' + user.name + '\"',
                '"state"': '\"' + user.state + '\"',
                '"partner"': '\"' + user.partner_id.ref + '\"',
                '"aff_key"': '\"' + user.aff_key + '\"',
                '"aff_link"': '\"' + user.aff_link + '\"',
                '"last_logon"': '\"' + (user.last_logon or str(datetime.now())) + '\"',
                '"create_date"': '\"' + user.create_date + '\"'
            })
            res['"data"'] = data
        return res

    @api.model
    def affiliate_user_search_aff_key(self, aff_key):
        res = {'"code"': 0, '"msg"': '""', '"data"': '""'}
        user = self.env['chili.affiliate.user'].search([('aff_key', '=', aff_key), ('state', '=', 'approved')],
                                                       limit=1)
        if user:
            res['"code"'] = 1
            data = []
            data.append({
                '"name"': '\"' + user.name + '\"',
                '"state"': '\"' + user.state + '\"',
                '"partner"': '\"' + user.partner_id.ref + '\"',
                '"aff_key"': '\"' + user.aff_key + '\"',
                '"aff_link"': '\"' + user.aff_link + '\"',
                '"last_logon"': '\"' + (user.last_logon or str(datetime.now())) + '\"',
                '"create_date"': '\"' + user.create_date + '\"',
                '"login"': '\"' + user.login + '\"',
            })
            res['"data"'] = data
        return res

    @api.model
    def affiliate_user_changepass(self, login_name, old_pass, new_pass):
        res = {'"code"': 0, '"msg"': '""'}
        if not old_pass:
            res['"msg"'] = '"Vui lòng nhập mật khẩu đang sử dụng."'
            return res

        if not new_pass:
            res['"msg"'] = '"Vui lòng nhập mật khẩu muốn thay đổi."'
            return res

        if old_pass == new_pass:
            res['"msg"'] = '"Mật khẩu cũ và mật khẩu mới không được giống nhau."'
            return res

        user_login = self.env['chili.affiliate.user'].search(
            [('login', '=', login_name), ('password', '=', old_pass), ('state', '=', 'approved')],
            limit=1)
        if not user_login:
            res['"msg"'] = '"Mật khẩu cũ không đúng."'
            return res

        if user_login:
            user_login.write({'password': new_pass})
            res['"msg"'] = '"Đổi mật khẩu thành công."'
            res['"code"'] = 1
            return res

        return res
