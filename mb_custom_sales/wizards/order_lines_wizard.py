# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.tools.float_utils import float_compare
from datetime import datetime, timedelta

class SaleContractReason(models.TransientModel):
    _inherit   = 'mb.contract.reason.wizard'
    check_send_to_customer = fields.Boolean(string = 'send to customer',default=False)



class OrderLinesWizard(models.TransientModel):
    _inherit = "order.lines.wizard"


    def check_addon_list(self, product_category_id):
        res = [0,00,000]
        if product_category_id:
            #product_category = self.env['product.category'].search([('id', '=', product_category_id)], limit=1)
            if product_category_id.parent_id:
                list = []
                #list.append(product_category_id.parent_id.id)
                while True:
                    if list == []:
                        list.append(product_category_id.parent_id.id)
                    list = self.env['product.category'].search(
                        [('parent_id', 'in', list), ('is_addons', '=', False)
                         ]).ids
                    if list:
                        res = res + list
                    else:
                        break

        return res



    @api.onchange('product_category_id')
    def onchange_product_category_id(self):
        res = super(OrderLinesWizard, self).onchange_product_category_id()
        if res:
            domain= res.get('domain')
            if domain.get('parent_product_id'):
                domain_parent_product_id= domain.get('parent_product_id')[0][2]
                #for i_domain_parent_product_id in domain_parent_product_id:
                #if i_domain_parent_product_id:
                tmp_i_domain_parent_product_id=[]
                product_category_id_list_check = self.check_addon_list(self.product_category_id)
                if product_category_id_list_check:
                    for i in domain_parent_product_id:
                        product_data = self.env['product.product'].search([('id', '=', i)], limit=1)
                        if product_data.id:
                            if product_data.product_tmpl_id.categ_id.id in product_category_id_list_check:
                                tmp_i_domain_parent_product_id.append(i)



                res['domain']['parent_product_id'][0]=('id','in',tmp_i_domain_parent_product_id)
            return res

        else:
            return res


