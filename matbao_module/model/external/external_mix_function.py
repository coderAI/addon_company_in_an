# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, DEFAULT_SERVER_DATE_FORMAT as DF
import re
import logging as _logger
import urllib2
import ssl

class ExternalMixFunction(models.AbstractModel):
    _name = 'external.mix.function'

    @api.model
    def mix_function(self, name, coupon, date_order, saleteam_code, order_type, customer, status, company_id,
                     payment_amount, payment_journal, payment_date, memo, lines=[], payment_method='', transaction_id='', source=''):
        # Create Customer, SO
        try:
            if type(customer) is not dict:
                return {'msg': "Invalid CustomerEntity"}
            flag = False
            if customer.get('ref'):
                customer_id = self.env['res.partner'].search([('ref', '=', customer.get('ref'))], limit=1)
                if customer_id:
                    flag = True
            create_so = self.env['external.so'].create_so_fix(name, coupon, date_order, saleteam_code, order_type, customer, status, company_id, lines=lines, source=source)
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create: %s"' % (e.message or repr(e))}
        if type(create_so) is not dict or create_so.get('code') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create 1: %s"' % (type(create_so) is dict and create_so.get('msg') or 'Func create_so_fix not return dict')}
        order_id = create_so.get('data')
        if payment_amount > 0:
            try:
                receive_money = self.env['external.receive.money'].with_context(no_add_funds=True).receive_money(order_id.partner_id.ref, payment_amount, payment_journal, payment_date, memo, transaction_id)
            except:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s"' % order_id.partner_id.name}
            if type(receive_money) is not dict or receive_money.get('"code"') <> 1:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s 1: %s"' % (order_id.partner_id.name, (type(receive_money) is dict and receive_money.get('"msg"')))}
        try:
            subtract_money = self.env['external.subtract.money.so'].subtract_money_so(order_id.name)
            try:
                if order_id and 'payment_method_so' in order_id.fields_get() and payment_method:
                    order_id.payment_method_so = payment_method
            except Exception as e:
                _logger.info("Can't update payment method: %s" % (e.message or repr(e)))
                pass
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s: %s"' % (order_id.name, (e.message or repr(e)))}
        if type(subtract_money) is not dict or subtract_money.get('"code"') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s 1: %s"' % (order_id.name, (type(subtract_money) is dict and subtract_money.get('"msg"')))}
        try:
            if order_id.fully_paid:
                active_service = self.env['external.active.service'].active_service(order_id.name)
                # if reseller_code and active_service:
                #     reseller_id = self.env['reseller.customer'].search([('code', '=', reseller_code)], limit=1)
                #     if reseller_id:
                #         active_service.write({'reseller_id': reseller_id.id})
            else:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"SO %s have not yet fully paid"' % order_id.name}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s: %s"' % (order_id.name, (e.message or repr(e)))}
        if type(active_service) is not dict or active_service.get('code') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s 1: %s"' % (order_id.name, active_service.get('msg'))}
        if not flag and order_id.partner_id and order_id.partner_id.ref and order_id.partner_id.email:
            full_url = 'https://id.matbao.net/users/active-password?idpt=' + order_id.partner_id.ref + '&emailpt=' + order_id.partner_id.email
            try:
                response = urllib2.urlopen(full_url)
                        # urllib2.urlopen(full_url)
                _logger.info('--------------- Send Email Active Password Successfully : %s ======== Info %s  ----------------' % (full_url, response.info()))
            except Exception as e:
                _logger.info('--------------- Send Email Active Password Fail: %s  ----------------' % (e.message or repr(e)))
                pass
        return {'"code"': 1, '"msg"': '"Successfully!!!"'}

    @api.model
    def mix_function_with_so(self, name, team_code, payment_amount, payment_journal, payment_date, memo, lines=[], payment_method='', transaction_id=''):
        # Update SO
        # _logger.info('1111111111111111111111')
        try:
            update_so = self.env['external.so'].update_order_line_from_payment(name, team_code=team_code, lines=lines)
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create: %s"' % (e.message or repr(e))}
        if type(update_so) is not dict or update_so.get('"code"') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Order name can`t create 1: %s"' % (type(update_so) is dict and update_so.get('msg') or 'Func update_order_line_from_payment not return dict %s' % update_so)}
        order_id = update_so.get('data')
        if payment_amount > 0:
            try:
                receive_money = self.env['external.receive.money'].with_context(no_add_funds=True).receive_money(order_id.partner_id.ref, payment_amount, payment_journal, payment_date, memo, transaction_id)
            except Exception as e:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s: %s"' % (order_id.partner_id.name, (e.message or repr(e)))}
            if type(receive_money) is not dict or receive_money.get('"code"') <> 1:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"Cant`t add funds for customer %s 1: %s"' % (order_id.partner_id.name, (type(receive_money) is dict and receive_money.get('"msg"')))}
        try:
            subtract_money = self.env['external.subtract.money.so'].subtract_money_so(order_id.name)
            try:
                if order_id and 'payment_method_so' in order_id.fields_get() and payment_method:
                    order_id.payment_method_so = payment_method
            except Exception as e:
                _logger.info('"Can not update payment method: %s"' % (e.message or repr(e)))
                pass
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s: %s"' % (order_id.name, (e.message or repr(e)))}
        if type(subtract_money) is not dict or subtract_money.get('"code"') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t subtract money for SO %s 1: %s"' % (order_id.name, (type(subtract_money) is dict and subtract_money.get('"msg"')))}
        try:
            if order_id.fully_paid:
                active_service = self.env['external.active.service'].active_service(order_id.name)
                # if reseller_code and active_service:
                #     reseller_id = self.env['reseller.customer'].search([('code', '=', reseller_code)], limit=1)
                #     if reseller_id:
                #         active_service.write({'reseller_id': reseller_id.id})
            else:
                self._cr.rollback()
                return {'"code"': 0, '"msg"': '"SO %s have not yet fully paid"' % order_id.name}
        except Exception as e:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s: %s"' % (order_id.name, (e.message or repr(e)))}
        if type(active_service) is not dict or active_service.get('code') <> 1:
            self._cr.rollback()
            return {'"code"': 0, '"msg"': '"Can`t active service for SO %s 1: %s"' % (order_id.name, active_service.get('msg'))}
        return {'"code"': 1, '"msg"': '"Successfully!!!"'}