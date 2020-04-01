# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import xlrd
import itertools

import logging

_logger = logging.getLogger(__name__)

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')





class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def unreconcile(self):
        """ _inherit funtion reload data
        """
        self._get_payment_info_JSON
        return self

    @api.multi
    def open_payment(self):
        """ Open a window to account move """
        if self.payment_count > 1:
            list_move_id = [payment_move_line.move_id.id for payment_move_line in self.payment_move_line_ids]
            form_view = self.env.ref('account.view_move_form')
            tree_view = self.env.ref('account.view_move_tree')
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree, form',
                'views': [
                    (tree_view.id, 'tree'),
                    (form_view.id, 'form'),
                ],
                'view_type': 'form',
                'name':'Payment account move list',
                'domain': [('id', 'in', list_move_id or [])],
            }



        for payment in self.payment_move_line_ids:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': payment.move_id.id,
                'view_mode': 'form',
            }
        return self