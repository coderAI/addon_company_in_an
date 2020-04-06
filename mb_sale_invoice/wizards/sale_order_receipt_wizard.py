from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrderReceiptWizard(models.Model):
    _name = 'sale.order.receipt.wizard'

    send_mail_receipt_a4 = fields.Boolean('Send Receipt (A4) via mail')
    print_selection = fields.Selection([
        ('receipt', 'Receipt'),
        ('receipt_a4', 'Receipt (A4)')
    ])
    mail_to = fields.Char('Mail to (add)')

    @api.onchange('print_selection')
    def onchange_print_selection(self):
        if self.print_selection and self.print_selection == 'receipt':
            self.update({
                'send_mail_receipt_a4': False,
                'mail_to': '',
            })

    @api.multi
    def handle_selection(self):
        order_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if self.send_mail_receipt_a4:
            order_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            if order_id.state in ['paid', 'completed', 'done'] and order_id.invoice_ids and all(inv.payment_method == 'cash' for inv in order_id.invoice_ids):
                order_id.with_context(mail_to=self.mail_to).send_mail_receipt_report()
            else:
                raise UserError(_("Sale Order has been not paid, or wasn't paid by cash"))
        if self.print_selection == 'receipt':
            return order_id.print_receipt_report()
        if self.print_selection == 'receipt_a4':
            return order_id.print_receipt_report_2()
