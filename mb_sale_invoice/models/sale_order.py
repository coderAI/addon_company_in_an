from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_draft(self):
        if self.contract_id and self.contract_id.state not in ['new', 'refuse_ac', 'cancel']:
            raise UserError(_(
                'You just can Set to Quotation for Sale Order '
                'what have Contract with state Draft / Signing Refused / Canceled'))
        super(SaleOrder, self).action_draft()

    # Report
    @api.multi
    def check_service_ssl(self):
        self.ensure_one()
        if any(categ.code and self.get_parent_product_category(self.env['product.category'].search([
            ('code', '=', categ.code)
        ], limit=1)).code == 'SSL' for categ in self.order_line.mapped('product_category_id')):
            return True
        return False

    @api.multi
    def check_service_microsoft(self):
        self.ensure_one()
        if any(categ.code and self.get_parent_product_category(self.env['product.category'].search([
            ('code', '=', categ.code)
        ], limit=1)).code == 'MICROSOFT' for categ in self.order_line.mapped('product_category_id')):
            return True
        return False

    @api.multi
    def check_service_cloud_server(self):
        self.ensure_one()
        if any(categ.code and self.get_parent_product_category(self.env['product.category'].search([
            ('code', '=', categ.code)
        ], limit=1)).code == 'CLOUDSERVER' for categ in self.order_line.mapped('product_category_id')):
            return True
        return False

    @api.multi
    def print_receipt_report_2(self):
        self.ensure_one()
        if not self.invoice_ids.filtered(lambda inv: inv.state != 'cancel'):
            raise UserError(_("Please create Invoice first!!!"))
        return self.env['report'].get_action(self, 'mb_sale_invoice.account_receipt_template_report')

    @api.multi
    def send_mail_receipt_report(self):
        ctx = self.env.context
        template = self.env.ref('mb_sale_invoice.email_template_send_receipt')
        if ctx.get('mail_to'):
            template.send_mail(res_id=self.id, force_send=True, email_values={'email_to': ctx['mail_to']})
        else:
            template.send_mail(res_id=self.id, force_send=True, email_values={'email_to': ctx['mail_to']})

    @api.model
    def api_cancel_so_not_assign(self, num_date=0):
        search_date = date.today() - timedelta(days=int(num_date))
        orders = self.search([
            ('user_id', '=', False),
            ('team_id', '=', False),
            ('type', '=', 'renewed'),
            ('create_date', '<', fields.Date.to_string(search_date) + " 00:00:00"),
            ('state', '=', 'not_received'),
        ])
        if orders:
            try:
                self.env.cr.execute("UPDATE sale_order SET state='cancel' WHERE id in " + str(tuple(orders.ids)))
                return "Cancelled the Orders is not assign and not paid!"
            except:
                return 'Some problem'
        return 'No orders found'
