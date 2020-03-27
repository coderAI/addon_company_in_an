# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class SearchCustomerWizard(models.TransientModel):
    _name = "search.customer.wizard"
    _description = "Allows sales users to search customer information"

    name = fields.Char("Name", default="Search Customer")
    customer_code = fields.Char(string="Customer Code")
    customer_name = fields.Char(string="Customer Name")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile_phone = fields.Char(string="Mobile Phone")
    customer_ids = fields.Many2many("res.partner")

    @api.multi
    def search_customer(self):
        """
            TO DO:
            - Allow users to search customers
        """
        self.ensure_one()
        args = []
        ResPartner = self.env['res.partner']
        customers = False
        domain = [('customer', '=', True)]
        if self.customer_code:
            args += [('ref', '=', self.customer_code)]
        if self.customer_name:
            args += [('name', '=', self.customer_name)]
        if self.email:
            args += [('email', '=', self.email)]
        if self.phone:
            args += [('phone', '=', self.phone)]
        if self.mobile_phone:
            args += [('mobile', '=', self.mobile_phone)]
        if args:
            customers = ResPartner.sudo().search(args+domain)
        self.customer_ids = [(6, 0, customers and customers.ids or [])]
