# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from lxml import etree
from odoo.osv.orm import setup_modifiers

from odoo.addons.base.res.res_partner import FormatAddress



_logger = logging.getLogger(__name__)

CRM_LEAD_FIELDS_TO_MERGE = [
    'name',
    'partner_id',
    'campaign_id',
    'company_id',
    'country_id',
    'team_id',
    'state_id',
    'stage_id',
    'medium_id',
    'source_id',
    'user_id',
    'title',
    'city',
    'contact_name',
    'description',
    'fax',
    'mobile',
    'partner_name',
    'phone',
    'probability',
    'planned_revenue',
    'street',
    'street2',
    'zip',
    'create_date',
    'date_action_last',
    'date_action_next',
    'email_from',
    'email_cc',
    'partner_name']



_logger = logging.getLogger(__name__)



class Lead2OpportunityMassConvert(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner'
    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()


    team_id = fields.Many2one('crm.team', string='Sales Team', default=_get_default_team, oldname='section_id', domain=lambda self: [('id', '=', self.env.user.sale_team_id.id)])
    user_id = fields.Many2one('res.users', 'Salesperson', index=True)


    @api.onchange('team_id')
    def _onchange_team_id(self):
        res = {}
        if self.team_id:
            domain = {'team_id': [('company_id', '=', self.env.user.company_id.id)]}
            if self.user_id.id not in self.team_id.member_ids.ids:
                self.user_id =False
            res['domain'] = domain
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Lead2OpportunityMassConvert, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            fields_to_options = doc.xpath("//field")
            for node in fields_to_options:
                if not self.user_has_groups('base.group_system') and not self.user_has_groups('sales_team.group_sale_manager') and \
                        (doc.xpath("//field[@name='team_id']") and node == doc.xpath("//field[@name='team_id']")[0]):
                    node.set('invisible', '1')
                    setup_modifiers(node)
                if not self.user_has_groups('base.group_system') and not self.user_has_groups(
                            'sales_team.group_sale_manager') \
                            and not self.user_has_groups('sales_team.group_sale_salesman_all_leads') and \
                            (doc.xpath("//field[@name='user_id']") and node == doc.xpath("//field[@name='user_id']")[
                                0]):
                        node.set('invisible', '1')
                        setup_modifiers(node)



        res['arch'] = etree.tostring(doc)
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    customer_source = fields.Many2one('lead.customer.source', 'Customer Source')




class get_sale_order(FormatAddress, models.Model):

    _inherit = "get.sale.order"

    @api.multi
    def update_salesperson_team(self):
        user = self.env.user
        order_id = self.env['sale.order'].sudo().search([('name', '=', self.order), ('type', '=', 'renewed')])
        order_id.with_context(default_author=user.partner_id.id).write({
            'renew_reason_id':self.renew_reason_id.id,
            'renew_reason_description':self.reason,
        })
        return super(get_sale_order, self).update_salesperson_team()



class Lead(FormatAddress, models.Model):

    _inherit = "crm.lead"

    @api.multi
    def close_dialog(self):
        if self._context.get('active_model') == 'sale.order':
            order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            order_id.customer_source = self.customer_source.id
        return super(Lead, self).close_dialog()


    @api.onchange('team_id')
    def _onchange_team_id(self):
        res = {}
        if self.team_id:
            domain = {
                      'team_id': [('company_id', '=', self.env.user.company_id.id)]
            }

            if self.user_id.id not in self.team_id.member_ids.ids:
                self.user_id =False
            res['domain'] = domain
        return res


