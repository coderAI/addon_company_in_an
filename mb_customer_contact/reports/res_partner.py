# -*- coding: utf-8 -*-
from odoo.osv import osv
from odoo.report import report_sxw
from odoo.tools.translate import _
from odoo.api import Environment
from datetime import datetime
import logging as _logger
from odoo.addons.matbao_support.reports.base.res_partner import report_base_partner_common

def get_payment_info(self, child_ids):
    # _logger.info("77777776666677777777 %s 7777777766666777777", child_ids)
    rs = {'domain_manager': '',
          'payment_manager': '',
          'technical_manager': '',
          'contact': ''}
    partner_env = self.env['customer.contact']
    if child_ids:
        for line_id in child_ids:
            vals = {
                'name': '',
                'address': '',
                'province': '',
                'country': '',
                'mobile': '',
                'fax': '',
                'email': '',
                'postcode': '',
                'indentify_number': ''}
            address = ''
            line_obj = partner_env.browse(line_id)
            if line_obj.street and line_obj.street2:
                address = '%s - %s' % (line_obj.street, line_obj.street2)
            elif not line_obj.street and line_obj.street2:
                address = line_obj.street2
            elif line_obj.street and not line_obj.street2:
                address = line_obj.street
            if line_obj.city:
                city = ' - ' + line_obj.city
                address += city
            vals.update(
                {'name': line_obj.name,
                 'address': address,
                 'province': line_obj.state_id and line_obj.state_id.name or '',
                 'country': line_obj.country_id and line_obj.country_id.name or '',
                 'mobile': line_obj.mobile or line_obj.phone or '',
                 'fax': line_obj.fax or '',
                 'email': line_obj.email or '',
                 'postcode': line_obj.zip or '',
                 'indentify_number': line_obj.indentify_number or ''})
            if(line_obj.type == 'domain_manager'):
                rs.update({'domain_manager': vals})
            elif(line_obj.type == 'payment_manager'):
                rs.update({'payment_manager': vals})
            elif(line_obj.type == 'technical_manager'):
                rs.update({'technical_manager': vals})
            elif(line_obj.type == 'contact'):
                rs.update({'contact': vals})
    return rs
    
report_base_partner_common.get_payment_info = get_payment_info
    
    