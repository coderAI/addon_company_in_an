# -*- coding: utf-8 -*-
# -------------------------------Design by Hai--------------------------------#
import xmlrpclib
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import Warning
from odoo.tools import float_compare


class ExternalActiveService(models.AbstractModel):
    _description = 'Active Service API'
    _name = 'external.active.service'

    @api.model
    def active_service(self, so_code):
        res = {'code': 0, 'msg': ''}
        if not so_code:
            res['msg'] = "SO Code could not be empty"
            return res
        so = self.env['sale.order'].search([('name', '=', so_code), ('state', 'in', ('sale', 'paid'))])
        if not so:
            res['msg'] = "SO must be state In progress"
            return res
            # Copy function from match payment wizard
        if not so.fully_paid:
            res['msg'] = 'Sale order must be fully paid'
            return res
        try:
            if so.order_line:
                for line in so.order_line:
                    # if line.reseller:
                    #     reseller_id = self.env['reseller.customer'].sudo().search([('code', '=', str(line.reseller))], limit=1)
                    #     if reseller_id:
                    #         service.write({'reseller_id': reseller_id.id})
                    if line.service_status == 'draft':
                        service = line.with_context(force_company=so.company_id.id).activate()
            res['code'] = 1
            return res
        except Exception as e:
            return {'code': 0, 'msg': 'Error: %s' % (e.message or repr(e))}