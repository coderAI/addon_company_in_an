from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_tax = fields.Monetary(string='Price Tax')
    fix_subtotal = fields.Float(string='Fix Subtotal')
    team_id = fields.Many2one('crm.team', related='order_id.team_id', string='Sales Team', readonly=True)

    @api.multi
    def activate(self):
        res = super(SaleOrderLine, self).activate()
        contract_obj = self.env['mb.sale.contract']
        for line in self:
            if line.order_id.partner_id.state == 'draft':
                line.order_id.partner_id.write({'state': 'edited'})
            # if line.register_type == 'register' \
            #    and line.product_category_id.parent_id and \
            #    line.product_category_id.parent_id.code == 'TMVN':
            if line.register_type == 'register' \
               and line.product_category_id.code and line.product_category_id.code[:1] == '.':
                if not line.order_id.contract_id and \
                        not contract_obj.search([('order_id', '=', line.order_id.id)], order='id desc', limit=1):
                    contract_id = contract_obj.with_context(force_company=line.order_id.company_id.id).create({
                        'partner_id': line.order_partner_id.id,
                        'order_id': line.order_id.id,
                        'state': 'new',
                        'company_id': line.order_id.company_id.id,
                        'user_id': self.env.user.id
                    })
                    line.order_id.write({'contract_id': contract_id.id or False, })
        return res
