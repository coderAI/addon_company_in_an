# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.matbao_module.model.sale.sale_service import STATUS

class SearchServiceWizard(models.TransientModel):
    _name = "search.service.wizard"
    _description = "Allows sales users to search service information"

    name = fields.Char()
    customer = fields.Char()
    product = fields.Char()
    product_category = fields.Many2one('product.category', "Product Category")
    service_ids = fields.Many2many("sale.service")
    status = fields.Selection(STATUS)

    @api.multi
    def search_service(self):
        self.ensure_one()
        args = []
        SaleService = self.env['sale.service']
        self.service_ids = False
        if self.name:
            args += ['|', ('reference', '=', self.name), ('name', 'like', self.name)]
        if self.customer:
            args += ['|', ('customer_id.ref', '=', self.customer), ('customer_id.name', 'like', self.customer)]
        if self.product:
            args += ['|', ('product_id.default_code', '=', self.product), ('product_id.name', 'like', self.product)]
        if self.product_category:
            args += [('product_category_id', '=', self.product_category.id)]
        if self.status:
            args += [('status', '=', self.status)]
        if args:
            services = SaleService.search(args)
            self.service_ids = services and [(6, 0, services and services.ids or [])] or False


