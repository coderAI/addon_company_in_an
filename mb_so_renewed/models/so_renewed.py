# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging as _logger
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF


class MBSORenewed(models.Model):
    _name = 'mb.so.renewed'

    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    days_to_renew = fields.Integer(string='Days to Renew', default=lambda self: self.env['ir.values'].get_default('sale.config.settings', 'days_to_renew'))
    service_line_ids = fields.One2many('mb.so.renewed.line', 'renew_id', string='Services Lines')
    count = fields.Integer(string='Number of Services')
    cus_count = fields.Integer(string='Number of Customer')
    order_count = fields.Integer(string='Number of Order')

    @api.multi
    def get_service(self):
        self.service_line_ids = False
        self.count = 0
        days = str(self.days_to_renew) + ' days'
        cr = self.env.cr
        cr.execute("""  INSERT INTO mb_so_renewed_line (create_uid, write_uid, create_date, write_date, service_id, renew_id, product_id)
                        SELECT %s,
                               %s,
                               now(),
                               now(),
                               sale_service.id,
                               %s,
                               sale_service.product_id
                        FROM sale_service
                        LEFT JOIN res_partner ON res_partner.id = sale_service.customer_id
                        LEFT JOIN product_category pc ON pc.id = sale_service.product_category_id
                        LEFT JOIN product_uom pu ON pu.id = pc.uom_id
                        WHERE sale_service.end_date = now()::date + INTERVAL %s
                          AND pc.to_be_renewed = TRUE
                          AND (sale_service.is_auto_renew is NULL OR sale_service.is_auto_renew = FALSE)
                          AND sale_service.status = 'active'
                          AND res_partner.company_type <> 'agency'""",
                   (self.env.user.id, self.env.user.id, self.id, days))
        cr.execute(
            """SELECT COUNT(*) FROM mb_so_renewed_line WHERE renew_id = %s""",
            (self.id,))
        objects = cr.dictfetchall()
        self.count = objects[0]['count']

    @api.multi
    def check_order(self):
        cr = self.env.cr
        cr.execute("""  UPDATE mb_so_renewed_line
                        SET order_id = so.name
                        FROM mb_so_renewed_line rl
                        LEFT JOIN sale_order_line l ON l.product_id = rl.product_id
                        LEFT JOIN sale_order so ON so.id = l.order_id
                        WHERE rl.renew_id = %s
                          AND (so.state IN ('not_received', 'draft', 'sale')
                               --OR (so.state = 'cancel' AND so.type = 'renewed')
                               OR so.state IS NULL)
                          AND so.type <> 'id'
                          AND mb_so_renewed_line.id = rl.id""",
                   (self.id,))

        try:
            self.cus_count = len(self.sudo().service_line_ids.filtered(lambda line: not line.order_id).mapped('customer_id'))

        except:
            self.cus_count = 0

    @api.multi
    def create_order_renewed(self):
        data = {}
        team = self.env['crm.team'].sudo().search([('type', '=', 'cs')])
        team_list={}
        for i in team:
            #add
            if team_list.get(i.company_id.id):
                team_list.get(i.company_id.id).update({
                                                        'count': team_list.get(i.company_id.id).get('count')+1,
                                                        'max_count': team_list.get(i.company_id.id).get('count')+1,
                                                        team_list.get(i.company_id.id).get('count')+1: i.id
                                                        })
            #new
            else:
                team_list.update({i.company_id.id:{
                                                    'max_count':0,
                                                    'count':0,
                                                    0:i.id
                                                   }
                                  })
        renew_service_ids = self.service_line_ids.filtered(lambda line: not line.order_id).mapped('service_id')
        for service in renew_service_ids:
            # if one of the parent categories has to_be_renewed = True
            customer_id = service.customer_id.id
            if service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name.lower() == u'năm':
                time = 1
            elif service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name.lower() == u'tháng':
                time = 12
            else:
                time = service.product_category_id.billing_cycle
            vals = {
                'register_type': 'renew',
                'product_category_id': service.product_category_id.id,
                'product_id': service.product_id.id,
                'parent_product_id': service.parent_product_id.id,
                'time': time,
                'product_uom': service.product_category_id.uom_id.id,
                'service_status': 'draft',
                'company_id': service.customer_id.company_id.id,
                # 'license': service.license and int(service.license) or 1
            }
            if service.product_category_id.parent_id and service.product_category_id.parent_id.code in ['MICROSOFT','License']:
                vals.update({
                    'license': service.license and int(service.license) or 1
                })

            if customer_id not in data:
                team_id = False
                if team_list.get(service.customer_id.company_id.id):
                    short_name = team_list.get(service.customer_id.company_id.id)
                    team_id = short_name.get(short_name.get('count'))
                    if short_name.get('max_count') == short_name.get('count'):
                        short_name.update({'count': 0})
                    else:
                        short_name.update({'count': short_name.get('count') + 1})

                data[customer_id] = {
                    'type': 'renewed',
                    'partner_id': customer_id,
                    'state': 'not_received',
                    'date_order': datetime.now(),
                    'order_line': [(0, 0, vals)],
                    'user_id': False,
                    'team_id': team_id,
                    'company_id': service.customer_id.company_id.id
                }
            else:
                # add to order_line in existing record
                data[customer_id]['order_line'].append((0, 0, vals))
            # # Update Addons lines to order line
        self.order_count = len(data)
        self._cr.commit()
        for index, order in enumerate(data):
            self.env['sale.order'].with_context(force_company=data[order].get('company_id')).sudo().create(data[order])
        self.check_order()

    @api.multi
    def get_order_renewed(self):
        data = {}
        # # Get Company, Team
        # arrs = []
        # companys = self.env['res.company'].sudo().search([])
        # for com in companys:
        #     dict = {}
        team = self.env['crm.team'].sudo().search([('type', '=', 'cs')])
        team_list={}
        for i in team:
            #add
            if team_list.get(i.company_id.id):
                team_list.get(i.company_id.id).update({
                                                        'count': team_list.get(i.company_id.id).get('count')+1,
                                                        'max_count': team_list.get(i.company_id.id).get('count')+1,
                                                        team_list.get(i.company_id.id).get('count')+1: i.id
                                                        })
            #new
            else:
                team_list.update({i.company_id.id:{
                                                    'max_count':0,
                                                    'count':0,
                                                    0:i.id
                                                   }
                                  })
        renew_service_ids = self.env['mb.so.renewed.line'].search([('renew_id', '=', self.id), ('order_id', '=', False)]).mapped('service_id')
        # _logger.info("4444444444444444444444444444444 %s 77777777777777777777777777777" % renew_service_ids)
        for service in renew_service_ids:
            # if one of the parent categories has to_be_renewed = True
            customer_id = service.customer_id.id
            if service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name.lower() == u'năm':
                time = 1
            elif service.product_category_id and service.product_category_id.uom_id and service.product_category_id.uom_id.name.lower() == u'tháng':
                time = 12
            else:
                time = service.product_category_id.billing_cycle
            vals = {
                '"register_type"': '"renew"',
                '"product_category_id"': service.product_category_id.id or '""',
                '"product_id"': service.product_id.id or '""',
                '"parent_product_id"': service.parent_product_id.id or '""',
                '"time"': time or '""',
                '"product_uom"': service.product_category_id.uom_id.id or '""',
                '"service_status"': '"draft"',
                '"company_id"': service.customer_id.company_id.id or '""'
            }
            if service.product_category_id.parent_id and service.product_category_id.parent_id.code == 'MICROSOFT':
                vals.update({
                    'license': service.license and int(service.license) or 1
                })


            if customer_id not in data:

                team_id = '""'
                if team_list.get(service.customer_id.company_id.id):
                    short_name = team_list.get(service.customer_id.company_id.id)
                    team_id = short_name.get(short_name.get('count'))
                    if team_id in (14, 10):
                        print team_id
                    if short_name.get('max_count') == short_name.get('count'):
                        short_name.update({'count': 0})
                    else:
                        short_name.update({'count': short_name.get('count') + 1})


                data[customer_id] = {
                    '"type"': '"renewed"' or '""',
                    '"partner_id"': customer_id or '""',
                    '"state"': '"not_received"',
                    '"date_order"': '\"' + datetime.now().strftime(DTF) + '\"',
                    '"order_line"': [vals],
                    '"user_id"': '""',
                    '"team_id"': team_id,
                    '"company_id"': service.customer_id.company_id.id or '""'
                }
            else:
                data[customer_id]['"order_line"'].append(vals)

        self.order_count = len(data)
        self._cr.commit()
        result = []
        for index, order in enumerate(data):
            result.append(data[order])
        return result


    @api.model
    def create_order(self, order):
        try:
            if order.get('order_line'):
                order_line = [(0, 0, line) for line in order.get('order_line')]
                order['order_line'] = order_line
            order['user_id'] = False
            order = self.env['sale.order'].with_context(force_company=order.get('company_id')).sudo().create(order)
            return {'"code"': 1, '"msg"': '"Create Order %s Successfully"' % order.name, '"order"': order.id}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t create order: %s"' % (e.message or repr(e))}

    @api.model
    def order_update_price(self, order):
        SaleOrder = self.env['sale.order']
        order_id = SaleOrder.browse(order)
        try:
            order_id.update_price_by_odoo()
            return {'"code"': 1, '"msg"': '"Update Price Order %s Successfully"' % order_id.name}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t update price order: %s"' % (e.message or repr(e))}

    @api.model
    def update_order(self, renew):
        try:
            renew_id = self.browse(renew)
            # _logger.info("++++++++++++++++++++ %s &&&&&&&&&&&&&&&&&&&&&" % renew_id)
            renew_id.check_order()
            return {'"code"': 1, '"msg"': '"Successfully"'}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t update order: %s"' % (e.message or repr(e))}

    @api.model
    def api_final_so_renewed(self, days):
        try:
            renew_id = self.create({
                'days_to_renew': days
            })
            return {'"renew_id"': renew_id.id}
        except Exception as e:
            return {'"Can`t Create SO Renewed: %s"' % (e.message or repr(e))}
        # try:
        #     renew_id.get_service()
        # except Exception as e:
        #     _logger.error("Can't get service: %s" % (e.message or repr(e)))
        # try:
        #     renew_id.check_order()
        # except Exception as e:
        #     _logger.error("Can't check order: %s" % (e.message or repr(e)))
        # try:
        #     # renew_id.create_order_renewed()
        #     _logger.info("00000000000000000000000000000 %s ///////////////////////" % self.env['mb.so.renewed.line'].search([('renew_id', '=', renew_id.id)]))
        #     data = renew_id.get_order_renewed()
        #     return {'"renew_id"': renew_id.id, '"data"': data}
        # except Exception as e:
        #     _logger.error("Can't create order: %s" % (e.message or repr(e)))

    @api.model
    def get_service_api(self, renew):
        renew_id = self.browse(renew)
        try:
            renew_id.get_service()
            return {'"code"': 1}
        except Exception as e:
            return {'"code"': 0, '"msg"': '"Can`t get service: %s"' % (e.message or repr(e))}

    @api.model
    def get_order_renewed_api(self, renew):
        renew_id = self.browse(renew)
        try:
            rsl = renew_id.get_order_renewed()
            # _logger.info("#################### %s $$$$$$$$$$$$$$$$$$" % rsl)
            return {'"data"': rsl}
        except Exception as e:
            return {'"msg"': '"Can`t get service: %s"' % (e.message or repr(e))}


class MBSORenewedLine(models.Model):
    _name = 'mb.so.renewed.line'

    service_id = fields.Many2one('sale.service', string='Service')
    product_id = fields.Many2one('product.product', string='Product', related='service_id.product_id', store=True)
    product_category_id = fields.Many2one('product.category', string='Product Category', related='service_id.product_category_id')
    end_date = fields.Date(string='End Date', related='service_id.end_date')
    customer_id = fields.Many2one('res.partner', string='Customer', related='service_id.customer_id')
    order_id = fields.Char(string='Sale Order')
    renew_id = fields.Many2one('mb.so.renewed')