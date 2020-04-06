from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning

class CancelSOWizard(models.TransientModel):
    _inherit = 'cancel.so.wizard'

    @api.model
    def default_get(self, fields_list):

        order_id = self.env.context.get('active_id')
        orders = self.env['sale.order'].browse(order_id)
        if orders and orders.inv_line_ids and \
           any(vat_status in ['to_export', 'exported'] for vat_status in orders.inv_line_ids.mapped('vat_status')):
            raise UserError(_('You can not cancel this Sale Order because the VAT Invoice was Open / Done.'))
        if orders.contract_id:
            if orders.contract_id.state not in ('new', 'cancel'):
                raise Warning(_('This Sale Order can not Cancel with this Contract'))
        return super(CancelSOWizard, self).default_get(fields_list)
