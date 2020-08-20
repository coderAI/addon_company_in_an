# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import Warning
import logging as _logger
from suds.client import Client
from odoo.tools import config

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _sql_constraints = [('unique_name', 'UNIQUE(name)', 'Order Name must be unique')]

    payment_method_so = fields.Char('Payment Method')

    @api.multi
    def write(self, vals):
        try:

            if vals.get('state') == 'paid' or \
              (vals.get('state') in ['completed','done'] and self.state == 'sale'):
                if self.mapped('opportunity_id').mapped('probability') <> 100:
                    self.mapped('opportunity_id').action_set_won()
                    self.mapped('opportunity_id').write({
                        'next_activity_id': False,
                        'date_action': False,
                        'title_action': False,
                    })
                    if self.mapped('coupon'):
                        if config.get('demo_server', False):
                            url = "http://112.78.2.248:1235/KBKMService.svc?wsdl"
                        else:
                            url = 'http://pro.matbao.net/KBKMService.svc?wsdl'
                        client = Client(url)
                        client.service.CapNhatCoupon_DaSuDung(self.mapped('coupon'))
                        client.service.CapNhatKHDungCoupon(self.mapped('partner_id').mapped('email'), self.mapped('coupon'))
        except Exception as e:
            _logger.info("Set WON for opportunity error: %s" % (e.message or repr(e)))
        if len(self) == 1 and self.team_id and self.user_id and vals.get('state') == 'paid':
            try:
                parameters = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])
                if parameters:
                    view_url = parameters[0].value
                    view_url += '/web?#id=%s&view_type=form&model=sale.order' % self.id
                else:
                    view_url = 'https://erponline.matbao.com'
                url = u'<a href="%s"><strong>%s</strong></a>' % (view_url, self.name)
                msg = u'<p>Chào %s,</p><p>Đơn hàng %s mà bạn đang xử lý đã được thanh toán thành công.</p><p>Vui lòng vào đơn hàng để kiểm tra.</p><p>Cảm ơn.</p>' % (self.user_id.name, url,)
                mail_values = {
                    'email_from': self.env.user.email,
                    'email_to': self.user_id.login or 'thaodt@matbao.com',
                    # 'email_to': 'hainv@matbao.com',
                    'subject': u"Thông báo đơn hàng đã được thanh toán",
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
                # pass
        rsl = super(SaleOrder, self).write(vals)
        return rsl

    @api.multi
    def check_coupon_and_update_price(self):
        try:
            for order in self.filtered(lambda so: so.coupon and so.coupon.strip()):
                if config.get('demo_server', False):
                    url = "http://112.78.2.248:1235/KBKMService.svc?wsdl"
                else:
                    url = 'http://pro.matbao.net/KBKMService.svc?wsdl'
                client = Client(url)
                result = client.service.KBKM_LayChiTietCoupon(order.coupon)
                if result:
                    if result.DaSuDung >= result.SuDungToiDa:
                        raise Warning(_("Coupon codes `%s` can't be used because it exceed the number of uses"))
        except Exception as e:
            raise Warning(_("Check Coupon error: %s" % (e.message or repr(e))))
        self.update_price()


class CancelSOWizard(models.TransientModel):
    _inherit = 'cancel.so.wizard'

    @api.multi
    def action_apply(self):
        try:
            if self._context.get('active_model') == 'sale.order':
                order_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
                if order_id.opportunity_id:
                    # reason_id = self.env['crm.lost.reason'].search([('name', '=', self.reason_id.name)])
                    # order_id.opportunity_id.write({'lost_reason': self.reason_id.id})
                    order_id.opportunity_id.action_set_lost()
                    order_id.opportunity_id.write({
                        'next_activity_id': False,
                        'date_action': False,
                        'title_action': False,
                    })
        except Exception as e:
            _logger.info("Can`t set LOST for opportunity: %s" % (e.message or repr(e)))
            pass
        return super(CancelSOWizard, self).action_apply()