# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class ReasonFormOnSaleOrderWizard(models.TransientModel):
    _inherit = "reason.form.on.sale.order.wizard"

    @api.multi
    def action_apply(self):
        ctx = self._context
        reason_id = False
        for obj in self:
            reason_id = obj.reason_id
        if ctx.get('active_model') == 'sale.order.line':
            line_id = self.env[ctx.get('active_model')].browse(ctx.get('active_id'))
            current_so = line_id.order_id or False
            if current_so and current_so.state <> 'draft':
                return {'type': 'ir.actions.act_close_wizard_and_reload_view'}
            if line_id:
                msg = u"<p>Delete service: </p>" \
                      u"<ul><li>Register type: %s</li><li>Product: %s</li><li>Product Category: %s</li><li>Time: %s</li><li>UOM: %s</li><li>Reason: %s</li></ul>" \
                      % (line_id.register_type,
                         line_id.register_type != 'renew' and line_id.product_name or line_id.product_id.name,
                         line_id.product_category_id.display_name, line_id.time, line_id.product_uom.name, reason_id.name or '')
                current_so.message_post(body=msg, subtype="mail.mt_note")
                sale_order = line_id.order_id
                line_id.unlink()
                sale_order.order_line.write({'price_updated': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
