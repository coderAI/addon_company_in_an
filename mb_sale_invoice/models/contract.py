import base64
from odoo import api, fields, models, _


class Contract(models.Model):
    _inherit = 'mb.sale.contract'

    @api.model
    def api_get_contract(self, contract_id):
        contract = self.browse(contract_id)
        if not contract:
            return _('Contract is not exist')
        pdf = self.env['report'].get_pdf([contract.order_id.id], 'mb_sale_contract.sale_contract_mb')
        result = base64.b64encode(pdf)
        return {
            "mime-type": '"base64/pdf"',
            "payload": '"' + result + '"',
        }
    # "hash": {
    #     "sha1": 'hash file',
    #     "sha266": 'hash file',
    #     "sha512": 'hash file'
    # }
