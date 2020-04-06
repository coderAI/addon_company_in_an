from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_cancel(self):
        if any(vat_status in ['to_export', 'exported'] for vat_status in self.filtered(lambda inv: inv.type not in ('out_refund', 'in_refund')).mapped('invoice_line_ids').mapped('vat_status')):
            raise UserError(_("You can not cancel this Account Invoice because the VAT Invoice was Open / Done."))
        return super(Invoice, self).action_invoice_cancel()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        values = super(Invoice, self)._prepare_refund(
            invoice=invoice, date_invoice=date_invoice, date=date, description=description, journal_id=journal_id)
        if values.get('team_id') and values.get('user_id'):
            user = self.env['res.users'].browse(values['user_id'])
            if user.sale_team_id:
                values['team_id'] = user.sale_team_id.id
        return values
