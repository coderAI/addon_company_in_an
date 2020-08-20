# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging as _logger
from odoo.exceptions import Warning
from lxml import etree
from odoo.osv.orm import setup_modifiers

class SaleContractReason(models.TransientModel):
    _inherit   = 'mb.contract.reason.wizard'

    def action_apply(self):
        contract_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if contract_id and contract_id.state in ('submit', 'cus_signed') and contract_id.order_id:
            try:
                parameters = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
                if parameters:
                    view_url = parameters[0].value
                    view_url += '/web?#id=%s&view_type=form&model=sale.order' % contract_id.order_id.id
                else:
                    view_url = 'https://erponline.matbao.com'
                url = u'<a href="%s"><strong>%s</strong></a>' % (view_url, contract_id.order_id.name)
                msg = u'<p>Chào %s,</p><p>Hợp đồng số [%s] của đơn hàng %s đã bị phòng OP từ chối duyệt vì lý do "%s"</p>' \
                      u'<p>Thực hiện lại hợp đồng để không bị treo doanh số và dịch vụ của Khách hàng không bị khóa nhé %s.</p>' \
                      u'<p>Cảm ơn.</p>' % \
                        (contract_id.user_id.name, contract_id.name, url, self.name, contract_id.user_id.name)
                email_to = contract_id.user_id and contract_id.user_id.login or \
                           (contract_id.order_id.user_id and contract_id.order_id.user_id.login or
                            (contract_id.partner_id.company_type == 'agency' and 'partner@matbao.com' or
                             'thaodt@matbao.com'))
                mail_values = {
                    'email_from': self.env.user.email,
                    'email_to': email_to,
                    'subject': u"Thông báo từ chối hợp đồng số [%s]" % contract_id.name,
                    'body_html': msg,
                    'body': msg,
                    'notification': True,
                    'author_id': self.env.user.partner_id.id,
                    'message_type': "email",
                }
                # _logger.info("%s", mail_values)
                mail_id = self.env['mail.mail'].create(mail_values)
                mail_id.send()
            except Exception as e:
                _logger.info("Can`t send email: %s" % (e.message or repr(e)))
                pass
        return super(SaleContractReason, self).action_apply()


class SaleContract(models.Model):
    _inherit = 'mb.sale.contract'

    @api.multi
    def action_return(self):
        res = super(SaleContract, self).action_return()
        if self.order_id and self.state == 'return':
            try:
                parameters = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
                if parameters:
                    view_url = parameters[0].value
                    view_url += '/web?#id=%s&view_type=form&model=sale.order' % self.order_id.id
                else:
                    view_url = 'https://erponline.matbao.com'
                url = u'<a href="%s"><strong>%s</strong></a>' % (view_url, self.order_id.name)
                msg = u'<p>Chào %s,</p><p>Hợp đồng số [%s] của đơn hàng %s đã được phòng OP duyệt thành công.</p>' \
                      u'<p>Chúc mừng bạn %s nhé, cố gắng lên nào.</p>' \
                      u'<p>Cảm ơn.</p>' % \
                        (self.user_id.name, self.name, url, self.user_id.name)
                mail_values = {
                    'email_from': self.env.user.email,
                    'email_to': self.user_id and self.user_id.login or (self.order_id.user_id and self.order_id.user_id.login or 'thaodt@matbao.com'),
                    # 'email_to': 'hainv@matbao.com',
                    'subject': u"Thông báo duyệt thành công hợp đồng số [%s]" % self.name,
                    'body_html': msg,
                    'body': msg,
                    'notification': True,
                    'author_id': self.env.user.partner_id.id,
                    'message_type': "email",
                }
                # _logger.info("%s", mail_values)
                mail_id = self.env['mail.mail'].create(mail_values)
                mail_id.send()
            except Exception as e:
                _logger.info("Can`t send email: %s" % (e.message or repr(e)))
                pass
        return res