# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    approver = fields.Many2many('res.users', 'holidays_users_rel', 'holiday_id', 'user_id', string='Approvers',
                               compute='check_approve', store=True)
    approve = fields.Boolean(string='Can Approve', compute='check_is_approve',
                            help="If return True, show button Approve.")

    def recursive_user_approve(self, employee_id, users):
        approvers = employee_id.holidays_approvers and employee_id.holidays_approvers.mapped('approver') or False
        if approvers:
            users += approvers.mapped('user_id') and approvers.mapped('user_id').ids or []
            for employee in approvers - employee_id:
                self.recursive_user_approve(employee, users)
            return users
        else:
            return users

    @api.depends('employee_id', 'employee_id.holidays_approvers')
    def check_approve(self):
        for record in self:
            if record.employee_id:
                record.approver = [(6, 0, record.recursive_user_approve(record.employee_id, []))]

    def check_is_approve(self):
        for record in self:
            record.approve = False
            if self.env.user in record.approver:
                record.approve = True
            if self.user_has_groups('hr_holidays.group_hr_holidays_user'):
                record.approve = True

    @api.multi
    def action_confirm(self):
        for leave in self:
            try:
                approver_ids = leave.mapped('employee_id').mapped('holidays_approvers').mapped('approver')
                email_to = approver_ids and ';'.join(approver.work_email for approver in approver_ids)
                if email_to:
                    parameters = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
                    _logger.info("-------------------- %s --------------------" % parameters)
                    if parameters:
                        view_url = parameters[0].value
                        view_url += '/web?#id=%s&view_type=form&model=hr.holidays' % leave.id
                    else:
                        view_url = 'https://erponline.matbao.com'
                    url = u'<a href="%s"><strong>tại đây</strong></a>' % (view_url,)
                    msg = u'<p>Chào bạn,</p><p>Nhân viên %s xin nghỉ phép.</p><p>Nội dung: %s</p>' \
                          u'<p>Loại nghỉ phép: %s</p><p>Thời gian: %s - %s (%s days)</p>' % \
                          (leave.employee_id and leave.employee_id.name, leave.name or '', leave.holiday_status_id and leave.holiday_status_id.name or '',
                           leave.date_from or '', leave.date_to or '', leave.number_of_days_temp)
                    footer = u'<p>Vui lòng truy cập %s để xem thông tin và duyệt phép.</p>' % (url,)
                    mail_values = {
                        'email_from': self.env.user.email,
                        'email_to': email_to,
                        'subject': u"V/v Nhân viên %s xin nghỉ phép" % leave.employee_id.name,
                        'body_html': msg + footer,
                        'body': msg + footer,
                        'notification': True,
                        'author_id': self.env.user.partner_id.id,
                        'message_type': "email",
                    }
                    mail_id = self.env['mail.mail'].create(mail_values)
                    mail_id.send()
            except Exception as e:
                _logger.info("Can't send email: %s" % (e.message or repr(e)))
                pass
        return super(HrHolidays, self).action_confirm()

    @api.model
    def create(self, vals):
        leave = super(HrHolidays, self).create(vals)
        try:
            approver_ids = leave.mapped('employee_id').mapped('holidays_approvers').mapped('approver')
            email_to = approver_ids and ';'.join(approver.work_email for approver in approver_ids)
            if email_to:
                parameters = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
                _logger.info("-------------------- %s --------------------" % parameters)
                if parameters:
                    view_url = parameters[0].value
                    view_url += '/web?#id=%s&view_type=form&model=hr.holidays' % leave.id
                else:
                    view_url = 'https://erponline.matbao.com'
                url = u'<a href="%s"><strong>tại đây</strong></a>' % (view_url,)
                msg = u'<p>Chào bạn,</p><p>Nhân viên %s xin nghỉ phép.</p><p>Nội dung: %s</p>' \
                      u'<p>Loại nghỉ phép: %s</p><p>Thời gian: %s - %s (%s days)</p>' % \
                      (leave.employee_id and leave.employee_id.name, leave.name or '', leave.holiday_status_id and leave.holiday_status_id.name or '',
                       leave.date_from or '', leave.date_to or '', leave.number_of_days_temp)
                footer = u'<p>Vui lòng truy cập %s để xem thông tin và duyệt phép.</p>' % (url,)
                mail_values = {
                    'email_from': self.env.user.email,
                    'email_to': email_to,
                    'subject': u"V/v Nhân viên %s xin nghỉ phép" % leave.employee_id.name,
                    'body_html': msg + footer,
                    'body': msg + footer,
                    'notification': True,
                    'author_id': self.env.user.partner_id.id,
                    'message_type': "email",
                }
                mail_id = self.env['mail.mail'].create(mail_values)
                mail_id.send()
        except Exception as e:
            _logger.info("Can't send email: %s" % (e.message or repr(e)))
            pass
        return leave

    @api.multi
    def action_approve(self):
        for holiday in self:
            current_user = self.env.user
            # is_last_approbation = False
            sequence = 0
            # next_approver = None
            # for approver in holiday.employee_id.holidays_approvers:
            #     sequence = sequence + 1
            #     if holiday.pending_approver.id == approver.approver.id:
            #         if sequence == len(holiday.employee_id.holidays_approvers):
            #             is_last_approbation = True
            #         else:
            #             next_approver = holiday.employee_id.holidays_approvers[sequence].approver
            # if is_last_approbation:
            holiday.sudo().with_context(default_author=current_user.partner_id.id, approver=current_user.id).action_validate()
            # else:
            # holiday.write({'state': 'confirm', 'pending_approver': next_approver and next_approver.id})
            # self.env['hr.employee.holidays.approbation'].create({'holidays': holiday.id, 'approver': current_user.id, 'sequence': sequence, 'date': fields.Datetime.now()})

class EmployeeHolidaysApprobation(models.Model):
    _inherit = "hr.employee.holidays.approbation"

    @api.model
    def create(self, vals):
        if self._context.get('approver'):
            vals['approver'] = self._context.get('approver')
        return super(EmployeeHolidaysApprobation, self).create(vals)