from datetime import datetime
from odoo import api, fields, models


class SalePhoneHistory(models.Model):
    _name = "sale.phone.history"

    stt = fields.Integer('STT')
    key = fields.Char()
    call_date = fields.Datetime('Call Date', default=datetime.now())
    phone_from = fields.Char('Phone From')
    ext_phone = fields.Char('EXT')
    phone_to = fields.Char('Phone To')
    status = fields.Char('Status')
    call_time = fields.Char('Call Time')
    call_real_time = fields.Char('Real-time call')
    link_file = fields.Char('Link file')
    link_file_in_mb = fields.Char('Link file in MatBao')

    @api.model
    def sync_phone_call(self, vals={}):
        import HTMLParser
        parser = HTMLParser.HTMLParser()
        if not vals or type(vals) is not dict:
            return {'"code"': 0, '"msg"': '"Invalid Data"'}
        args = {}
        list_partner = []
        partner_obj = self.env['res.partner']
        if vals.get('stt'):
            args['stt'] = vals['stt']
        if vals.get('key'):
            if self.search([('key', '=', vals['key'])]):
                return {'"code"': 0, '"msg"': '"Key is exist"'}
            args['key'] = vals['key']
        if vals.get('call_date'):
            args['call_date'] = vals['call_date']
        if vals.get('phone_from'):
            args['phone_from'] = vals['phone_from'] and parser.unescape(vals['phone_from']) or ''
            list_partner += partner_obj.search([
                '|', ('phone', 'ilike', vals['phone_from']), ('mobile', 'ilike', vals['phone_from'])]).ids
        if vals.get('ext_phone'):
            args['ext_phone'] = vals['ext_phone']
        if vals.get('phone_to'):
            args['phone_to'] = vals['phone_to']
            list_partner += partner_obj.search([
                '|', ('phone', 'ilike', vals['phone_to']), ('mobile', 'ilike', vals['phone_to'])]).ids
        if vals.get('status'):
            args['status'] = vals['status']
        if vals.get('call_time'):
            args['call_time'] = vals['call_time']
        if vals.get('call_real_time'):
            args['call_real_time'] = vals['call_real_time']
        if vals.get('link_file'):
            args['link_file'] = vals['link_file']
        if vals.get('link_file_in_mb'):
            args['link_file_in_mb'] = vals['link_file_in_mb']
        try:
            history_ids = self.create(args)
            partners = partner_obj.browse(list_partner)
            if partners:
                partners.write({
                    'phone_history_ids': [(4, history) for history in history_ids.ids]
                })
            return {'"code"': 1, '"msg"': '"Create successfully phone call"'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can not create / write phone call: %s"' % (e.message or repr(e))}
