# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2009-2017 Trobz (<http://trobz.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re
from odoo.exceptions import Warning
from odoo.tools.float_utils import float_compare
from odoo.osv.orm import setup_modifiers
from odoo.tools.safe_eval import safe_eval
from lxml import etree


class ResPartner(models.Model):
    """
        Custom customer
    """
    _inherit = "res.partner"

    indentify_number = fields.Char(string='Indentify Card/Passport Number')
    date_of_birth = fields.Date(string='Date of Birth')
    date_of_founding = fields.Date(string='Date of Founding')
    sub_email_1 = fields.Char(string='Sub Email 1')
    sub_email_2 = fields.Char(string='Sub Email 2')
    representative = fields.Char(string='Representative')
    source_id = fields.Many2one(
        'res.partner.source',
        string='Source', readonly=True)
    ir_attachment_ids = fields.One2many('ir.attachment', 'partner_id',
                                        string='Attached Documents')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_for_approval', "Waiting for Approval"),
         ('approved', 'Approved'),
         ('refused', 'Refused')],
        default='draft', readonly=True, string='Status')
    main_account = fields.Float(string='Main account')
    promotion_account = fields.Float(string='Promotion account')
    gender = fields.Selection(
        [('male', 'Male'),
         ('female', 'Female'),
         ('others', 'Others')],
        string='Gender')
    country_id = fields.Many2one(
        'res.country', string='Country',
        ondelete='restrict', required=True,
        default=lambda self:
        self.env['res.country'].search([('code', '=', 'VN')], limit=1))
    street = fields.Char(required=True)
    email = fields.Char(required=True)
    city = fields.Char()
    company_type = fields.Selection(selection_add=[('agency', 'Agency')],
                                    default='person', compute=False)
    type = fields.Selection(
        selection_add=[('payment_manager', 'Payment Manager'),
                       ('technical_manager', 'Technical Manager'),
                       ('domain_manager', 'Domain Manager'),
                       ('helpdesk_manager', 'Helpdesk Manager')])
    ref = fields.Char(readonly=True, copy=False)
    accounting_ref = fields.Char(string="Accounting Reference")
    parent_company_type = fields.Selection(related='parent_id.company_type', string="Parent Company Type")

    payment_count = fields.Integer(compute='_compute_payment_count',
                                   string='# of Payment')

    service_count = fields.Integer(compute='_compute_service_count',
                                   string='# of Service')
    vat = fields.Char(string='Tax Code')
    parent_id_state = fields.Selection(related="parent_id.state", string='Parent Status')
    parent_id_customer = fields.Boolean(related="parent_id.customer", string="Parent Is Customer")

    @api.multi
    def _validate_email(self):
        """
            TO DO:
            - Validate the format of emails
        """
        for partner in self:
            email_list = []
            if partner.email:
                email_list.append(partner.email)
            if partner.sub_email_1:
                email_list.append(partner.sub_email_1)
            if partner.sub_email_2:
                email_list.append(partner.sub_email_2)
            if any(re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email) == None for email in email_list):
                return False
        return True

    _constraints = [
        (_validate_email, 'Please enter a valid email address.',
         ['email', 'sub_email_1', 'sub_email_2']),
    ]

    def _compute_payment_count(self):
        AccoutPayment = self.env['account.payment']
        for r in self:
            r.payment_count = AccoutPayment.search_count([('partner_id', '=', r.id)])

    def _compute_service_count(self):
        SaleService = self.env['sale.service']
        for r in self:
            r.service_count = SaleService.search_count([('customer_id', '=', r.id)])

    @api.multi
    def button_submit_to_operation(self):
        customer = self.sudo().filtered(lambda c: c.state == 'draft')
        if customer:
            customer.write({'state': 'waiting_for_approval'})
        return True

    @api.multi
    def button_approve(self):
        customer = self.filtered(lambda c: c.state == 'waiting_for_approval')
        if customer:
            customer.write({'state': 'approved'})
        return True

    @api.multi
    def button_refuse(self):
        customer = self.filtered(lambda c: c.state in ('waiting_for_approval', 'approved'))
        if customer:
            customer.write({'state': 'refused'})
        return True

    @api.multi
    def button_set_to_draft(self):
        customer = self.filtered(lambda c: c.state == 'refused')
        if customer:
            customer.write({'state': 'draft'})
        return True

    @api.constrains("vat")
    def check_vat(self):
        '''Remove the TAX constraint by country'''
        return True

    @api.multi
    def unlink(self):
        for customer in self:
            if customer.parent_id.state == 'approved' \
                    and customer.parent_id.customer == "True":
                raise Warning('''
                Cannot delete from CONTACTS & ADDRESSES
                when the customer status is approved ''')

        return super(ResPartner, self).unlink()

    def get_ref_partner(self):
        IrSequence = self.env['ir.sequence']
        ref = IrSequence.next_by_code('res.partner')
        if self.search_count([('ref', '=', ref)]) > 0:
            return self.get_ref_partner()
        return ref

    # @api.model
    # def create(self, vals):
    #     '''Check and update contact by company_type'''
    #     # IrSequence = self.env['ir.sequence']
    #     if (vals.get('customer', False) or vals.get('supplier', False)) and not vals.get('ref', False):
    #         vals.update({
    #             'ref': self.get_ref_partner() or '/',
    #         })
    #     res = super(ResPartner, self).create(vals)
    #     res.check_update_right(True)
    #     if self.env.context.get('fore_update_contact'):
    #         vals.update({'customer': False})
    #     if not self.env.context.get('fore_update_contact') and \
    #             vals.get('customer'):
    #         res.update_contacts()
    #
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     '''Check and update contact by company_type'''
    #     res = super(ResPartner, self).write(vals)
    #     for cus in self:
    #         if not cus.ref and (cus.customer or cus.supplier):
    #             # IrSequence = self.env['ir.sequence']
    #             cus.write({
    #                 'ref': self.get_ref_partner() or '/',
    #             })
    #     self.check_update_right()
    #     if not self.env.context.get('fore_update_contact'):
    #         self.update_contacts()
    #     return res

    @api.multi
    def check_update_right(self, no_except=False):
        allows = ['contact', 'invoice']
        if no_except:
            allows = []
        for r in self:
            if not r.parent_id or r.parent_id.state != 'approved' or \
                    (not r.parent_id.customer and not r.parent_id.supplier) or \
                    r.type in allows or self.user_has_groups('mb_sale_contract.group_operator_mb_sale_contract'):
                continue
            raise Warning('''
            Cannot add a new contact to CONTACTS & ADDRESSES when the
            customer status is approved''')
        return True

    @api.multi
    def update_contacts(self):
        for r in self:
            if not r.customer:
                continue
            if r.parent_id:
                continue
            has_contacts = required_contacts = []
            if r.company_type == 'person':
                required_contacts = ['payment_manager', 'technical_manager',
                                     'domain_manager', 'contact']
            if r.company_type in ['company', 'agency']:
                required_contacts = ['payment_manager', 'technical_manager',
                                     'domain_manager', 'helpdesk_manager',
                                     'contact']
            for contact in r.child_ids:
                if contact.type not in has_contacts:
                    has_contacts.append(contact.type)
            miss_contacts = list(set(required_contacts) - set(has_contacts))
            for contact in miss_contacts:
                vals = {
                    'name': r.name,
                    'type': contact,
                    'parent_id': r.id,
                    'customer': False
                }
                new_contact = r.sudo().copy(vals)
                if r.company_type in ['company', 'agency']:
                    new_contact.write({
                        'name': r.representative,
                        'company_type': 'person',
                        'is_company': False,
                    })
                else:
                    new_contact.write({'name': r.name})
        return True

    @api.model
    def default_get(self, fields):
        rec = super(ResPartner, self).default_get(fields)
        source_id = self.env.ref('matbao_module.partner_source_sale',
                                 False) and \
            self.env.ref('matbao_module.partner_source_sale',
                         False).id or False

        rec.update({
            'source_id': source_id,
        })
        return rec

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form',
    #                     toolbar=False, submenu=False):
    #
    #     result = super(ResPartner, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar,
    #         submenu=submenu)
    #
    #     if view_type not in ('form', 'kanban'):
    #         return result
    #
    #     doc = etree.XML(result['arch'])
    #
    #     except_fields = ['child_ids']
    #
    #     check_state = doc.xpath("//field[@name='state']")
    #     if check_state:
    #         args = [('state', '=', 'approved'), ('customer', '=', True)]
    #         fields_to_readonly = doc.xpath("//field")
    #         for node in fields_to_readonly:
    #             if node.get('name') == 'state' or \
    #                     node.get('name') in except_fields:
    #                 continue
    #             if node.get('modifiers'):
    #                 modif = {}
    #                 try:
    #                     modif = node.get('modifiers')
    #                     modif = modif.replace('true', 'True')
    #                     modif = modif.replace('false', 'False')
    #                     modif = safe_eval(modif)
    #                 except:
    #                     modif = {}
    #                 if modif.get('readonly') is True:
    #                     continue
    #             attrs = {}
    #             if node.get('attrs'):
    #                 attrs = safe_eval(node.get('attrs'))
    #             if 'readonly' in attrs and \
    #                     isinstance(attrs['readonly'], (list, tuple)):
    #                 attrs['readonly'] = [
    #                     '|', '&'] + args + ['&'] + attrs['readonly']
    #             else:
    #                 attrs.update({'readonly': args})
    #             node.set('attrs', str(attrs))
    #             setup_modifiers(node)
    #
    #     result['arch'] = etree.tostring(doc)
    #
    #     return result

    @api.multi
    def view_customer(self):
        """
            Open Customer Form
        """
        partner_form = self.env.ref(
            'matbao_module.view_res_partner_form_inherit', False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'matbao_module.view_res_partner_form_inherit',
            'res_model': 'res.partner',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'self',
            'view_id': partner_form.id,
            }
