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
from openerp import models, api, SUPERUSER_ID
from openerp.tools.translate import _
import logging as _logger
from odoo.tools.safe_eval import safe_eval
URL = "http://sandbox.matbao.net/api/values"


class MatbaoUpdateFunctionData(models.TransientModel):
    _name = "matbao.update.function.data"
    _description = "Mat Bao Module Post Object"

    @api.model
    def start(self):
        self.run_post_object_one_time(
            'matbao.update.function.data',
            ['_delete_native_states',
             '_create_service_sequence_auto',
             '_set_default_vendor',
             '_set_default_api_url',
             '_set_default_days_to_renew',
             '_set_default_partner',
             ])
        return True

    @api.model
    def run_post_object_one_time(self, object_name, list_functions=[]):
        """
        Generic function to run post object one time
        Input:
            + Object name: where you define the functions
            + List functions: to run
        Result:
            + Only functions which are not run before will be run
        """
        _logger.info('==START running one time functions for post object: %s'
                     % object_name)
        if isinstance(list_functions, (str, unicode)):  # @UndefinedVariable
            list_functions = [list_functions]
        if not list_functions\
                or not isinstance(list_functions, (list)):
            _logger.warning('Invalid value of parameter list_functions.\
                            Exiting...')
            return False

        ir_conf_para_env = self.env['ir.config_parameter']
        post_object_env = self.env[object_name]
        ran_functions = \
            ir_conf_para_env.get_param(
                'List_post_object_one_time_functions', '[]')
        ran_functions = safe_eval(ran_functions)
        if not isinstance(ran_functions, (list)):
            ran_functions = []
        for function in list_functions:
            if (object_name + ':' + function) in ran_functions:
                continue
            getattr(post_object_env, function)()
            ran_functions.append(object_name + ':' + function)
        if ran_functions:
            ir_conf_para_env.set_param('List_post_object_one_time_functions',
                                       str(ran_functions))
        _logger.info('==END running one time functions for post object: %s'
                     % object_name)
        return True

    @api.model
    def _delete_native_states(self):
        """
            TO DO:
            - Delete all native states, replace states by City/Province of
                Viet Nam
        """
        _logger.info("=== START:Delete all native states ===")
        sql = """UPDATE res_partner set state_id = null"""
        self._cr.execute(sql)
        states = self.env['res.country.state'].search([])
        states.unlink()
        _logger.info("=== END:Delete all native states ===")

    @api.model
    def _create_service_sequence_auto(self):
        """
            TO DO:
            - Create sequences for all product categories
        """
        _logger.info("=== START: create sequence for categories ===")
        IrSequence = self.env['ir.sequence']
        no_sequence_categories = self.env['product.category'].search(
            [('service_sequence_id', '=', False)])
        for category in no_sequence_categories:
            new_service_sequence = IrSequence.create({'name': category.name,
                                                      'padding': '7'})
            category.service_sequence_id = new_service_sequence
        _logger.info("=== END: create sequence for categories ===")

    @api.model
    def _set_default_vendor(self):
        """
            TO DO:
            - Set default vendor for purchase order
        """
        _logger.info("=== START: set default vendor ===")
        ir_values_obj = self.env['ir.values']
        default_vendor = self.env['res.partner'].search(
            [('name', '=', 'Default Vendor'), ('supplier', '=', True)],
            limit=1)
        if default_vendor:
            ir_values_obj.sudo().set_default(
                'purchase.order', "partner_id", default_vendor.id)
            ir_values_obj.sudo().set_default(
                'purchase.config.settings', 'partner_id', default_vendor.id)
        _logger.info("=== END: set default vendor ===")

    @api.model
    def _set_default_api_url(self):
        """
            TO DO:
            - Set default url of Mat Bao Api
        """
        _logger.info("=== START: set default Api URL ===")

        self.env['ir.values'].sudo().set_default(
                'sale.config.settings', 'url', URL)
        _logger.info("=== END: set default Api URL ===")

    @api.model
    def _set_default_days_to_renew(self):
        """
            TO DO:
            - Set default number of days to renew
        """
        _logger.info("=== START: set default number of days to renew ===")

        self.env['ir.values'].sudo().set_default(
                'sale.config.settings', 'days_to_renew', 30)
        _logger.info("=== END: set default number of days to renew ===")

    @api.model
    def _set_default_partner(self):
        """
            TO DO:
            - Set default Bank Transaction Customer
        """
        _logger.info("=== START: set defaultBank Transaction Customer ===")

        partner_id = \
            self.env.ref('matbao_module.default_bank_transaction_partner',
                         False) and \
            self.env.ref('matbao_module.default_bank_transaction_partner',
                         False).id or False
        self.env['ir.values'].sudo().set_default(
                'sale.config.settings', 'partner_id', partner_id)
        _logger.info("=== END: set default Bank Transaction Customer ===")