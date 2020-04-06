# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID


class ExternalActiveService(models.AbstractModel):
    _inherit = 'external.create.service'

    @api.model
    def update_service(self, po_name, start_date, end_date, ip_hosting, ip_email,
                       subscription_id=False, tenant_id=False, product_name=''):
        import logging
        # logging.info("---------------------")
        res = super(ExternalActiveService, self).update_service(
            po_name=po_name, start_date=start_date, end_date=end_date, ip_hosting=ip_hosting, ip_email=ip_email)
        # logging.info("----------- %s ----------", res)
        if res.get('"code"'):
            po = self.env['purchase.order'].search([('name', '=', po_name)], limit=1)
            if subscription_id:
                po_products = po.order_line.mapped('product_id')
                service = self.env['sale.service'].search([
                    ('product_id', '=', po_products and po_products[0].id or 0)
                ], limit=1)
                service.write({'subscription_id': subscription_id})
            if tenant_id:
                po.partner_id.write({'microsoft_customer_id': tenant_id})
        if res.get('"code"') == 1 and res.get('"data"') and product_name:
            # logging.info("++++++++++++++")
            service = self.env['sale.service'].browse(res.get('"data"'))
            service.product_id.write({'name': product_name})
            service.write({'name': '%s - %s' % (service.reference or '', product_name)})
        # logging.info("----------- %s ----------", res)
        return res
