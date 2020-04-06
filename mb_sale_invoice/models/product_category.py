from odoo import api, fields, models


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = ['product.category', 'mail.thread', 'ir.needaction_mixin']

    setup_price_vendor = fields.Float('Setup price (Vendor)', track_visibility='onchange')
    setup_price_mb = fields.Float('Setup price (MB)', track_visibility='onchange')
    renew_price_vendor = fields.Float('Renew price (Vendor)', track_visibility='onchange')
    renew_price_mb = fields.Float('Renew price (MB)', track_visibility='onchange')
    transfer_price_mb = fields.Float('Transfer price (MB)', track_visibility='onchange')
    setup_price_vendor_tax_id = fields.Char('Tax (Setup price - Vendor)')
    setup_price_mb_tax_id = fields.Char('Tax (Setup price - MB)')
    renew_price_vendor_tax_id = fields.Char('Tax (Renew price - Vendor)')
    renew_price_mb_tax_id = fields.Char('Tax (Renew price - MB)')
    transfer_price_mb_tax_id = fields.Char('Tax (Transfer price - MB)')
