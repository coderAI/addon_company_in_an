from odoo import api, fields, models, _
from odoo.exceptions import Warning


class AgencyPrice(models.Model):
    _name = 'product.agency.price'
    _description = "Agency Price"
    _order = 'categ_id, level_id'

    categ_id = fields.Many2one('product.category', 'Category')
    code = fields.Char(related='categ_id.code')
    erm_code = fields.Char(related='categ_id.erm_code')
    level_id = fields.Many2one('mb.agency.level', string='Agency Level')
    setup_price_vendor = fields.Float('Setup price (Vendor)')
    setup_price_mb = fields.Float('Setup price (MB)')
    renew_price_vendor = fields.Float('Renew price (Vendor)')
    renew_price_mb = fields.Float('Renew price (MB)')
    transfer_price_mb = fields.Float('Transfer price (MB)')

    @api.constrains('categ_id', 'level_id')
    def check_no(self):
        if self.search([
            ('categ_id', '=', self.categ_id.id),
            ('level_id', '=', self.level_id.id),
            ('id', '!=', self.id),
        ]):
            raise Warning(_("The Agency Price with this level is exist."))
