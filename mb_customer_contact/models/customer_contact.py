# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
import pytz
import logging as _logger
from odoo.exceptions import Warning

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

@api.model
def _tz_get(self):
    return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_ids = fields.One2many('customer.contact', 'parent_id', "Customer Contacts", domain=[('active', '=', True)])
    parent_id_customer = fields.Boolean(compute="get_is_customer")

    @api.depends('parent_id', 'parent_id.customer')
    def get_is_customer(self):
        for contact in self:
            contact.customer = contact.parent_id and contact.parent_id.customer or False

    @api.model
    def create(self, vals):
        '''Check and update contact by company_type'''
        # IrSequence = self.env['ir.sequence']
        if (vals.get('customer', False) or vals.get('supplier', False)) and not vals.get('ref', False):
            vals.update({
                'ref': self.get_ref_partner() or '/',
            })
        res = super(ResPartner, self).create(vals)
        res.check_update_right(True)
        if self.env.context.get('fore_update_contact'):
            vals.update({'customer': False})
        if not self.env.context.get('fore_update_contact') and vals.get('customer'):
            res.update_contacts()
        return res

    @api.multi
    def write(self, vals):
        '''Check and update contact by company_type'''
        res = super(ResPartner, self).write(vals)
        for cus in self:
            if not cus.ref and (cus.customer or cus.supplier):
                # IrSequence = self.env['ir.sequence']
                cus.write({
                    'ref': self.get_ref_partner() or '/',
                })
        self.check_update_right()
        if not self.env.context.get('fore_update_contact'):
            self.update_contacts()
        return res

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
            for contact in r.contact_ids:
                if contact.type not in has_contacts:
                    has_contacts.append(contact.type)
            miss_contacts = list(set(required_contacts) - set(has_contacts))
            # _logger.info("--------------- %s ---------------", miss_contacts)
            for contact in miss_contacts:
                vals = {
                    'type': contact,
                    'parent_id': r.id,
                    'customer': False,
                    'company_type': 'person',
                    'supplier': False,
                    'phone': r.phone or False,
                    'mobile': r.mobile or False,
                    'email': r.email or False,
                    'fax': r.fax or False,
                    'title': r.title and r.title.id or False,
                    'lang': r.lang or False,
                    'street': r.street or False,
                    'street2': r.street2 or False,
                    'city': r.city or False,
                    'zip': r.zip or False,
                    'gender': r.gender or False,
                    'state_id': r.state_id and r.state_id.id or False,
                    'country_id': r.country_id and r.country_id.id or False,
                    'website': r.website or False,
                    'category_id': r.category_id and [(6, 0, r.category_id.ids)] or False,
                    'date_of_birth': r.date_of_birth or False,
                    'date_of_founding': r.date_of_founding or False,
                    'vat': r.vat or False,
                    'indentify_number': r.indentify_number or False,
                    'is_company': False,
                    'function': r.function or False,
                    'company_id': r.company_id and r.company_id.id or False,
                }
                if r.company_type in ['company', 'agency']:
                    vals.update({'name': r.representative})
                else:
                    vals.update({'name': r.name})
                self.with_context(fore_update_contact=True).env['customer.contact'].create(vals)
        return True

    @api.multi
    def get_info_customer(self):
        vals = super(ResPartner, self).get_info_customer()
        # _logger.info("---------------------- %s ----------------------", vals)
        for con in self.partner_id.contact_ids:
            if con.type == 'domain_manager':
                vals['domain'] = con
            elif con.type == 'technical_manager':
                vals['technical'] = con
            elif con.type == 'payment_manager':
                vals['payment'] = con
            elif con.type == 'helpdesk_manager':
                vals['helpdesk'] = con
        # _logger.info("********************** %s ----------------------", vals)
        return vals

    def get_payment_info(self, contact_ids):
        # _logger.info("88888888888888888888 %s 99999999999999999999999", contact_ids)
        rs = {'domain_manager': '',
              'payment_manager': '',
              'technical_manager': '',
              'contact': ''}
        # partner_env = self.env['customer.contact']
        if contact_ids:
            for line_id in contact_ids:
                if line_id is int:
                    line_id = self.env['customer.contact'].browse(line_id)
                # _logger.info("7777777777777777 %s 7777777777777777", line_id)
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
                if line_id.street and line_id.street2:
                    address = '%s - %s' % (line_id.street, line_id.street2)
                elif not line_id.street and line_id.street2:
                    address = line_id.street2
                elif line_id.street and not line_id.street2:
                    address = line_id.street
                if line_id.city:
                    city = ' - ' + line_id.city
                    address += city
                vals.update(
                    {'name': line_id.name,
                     'address': address,
                     'province': line_id.state_id and line_id.state_id.name or '',
                     'country': line_id.country_id and line_id.country_id.name or '',
                     'mobile': line_id.mobile or line_id.phone or '',
                     'fax': line_id.fax or '',
                     'email': line_id.email or '',
                     'postcode': line_id.zip or '',
                     'indentify_number': line_id.indentify_number or ''})
                if line_id.type == 'domain_manager':
                    rs.update({'domain_manager': vals})
                elif line_id.type == 'payment_manager':
                    rs.update({'payment_manager': vals})
                elif line_id.type == 'technical_manager':
                    rs.update({'technical_manager': vals})
                elif line_id.type == 'contact':
                    rs.update({'contact': vals})
        # _logger.info("88888888888888888888 %s 99999999999999999999999", rs)
        return rs


class CustomerContact(models.Model):
    _name = 'customer.contact'

    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    def _default_company(self):
        return self.env['res.company']._company_default_get('res.partner')

    name = fields.Char(index=True)
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    date = fields.Date(index=True)
    title = fields.Many2one('res.partner.title')
    parent_id = fields.Many2one('res.partner', string='Related Company', index=True)
    parent_name = fields.Char(related='parent_id.name', readonly=True, string='Parent name')
    ref = fields.Char(string='Internal Reference', index=True)
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'),
                          help="The partner's timezone, used to output proper date and time values "
                               "inside printed reports. It is important to set a value for this field. "
                               "You should use the same timezone that is otherwise used to pick and "
                               "render date and time values: your computer's timezone.")
    tz_offset = fields.Char(compute='_compute_tz_offset', string='Timezone offset', invisible=True)
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help='The internal user that is in charge of communicating with this contact if any.')
    vat = fields.Char(string='TIN', help="Tax Identification Number. "
                                         "Fill it if the company is subjected to taxes. "
                                         "Used by the some of the legal statements.")
    website = fields.Char(help="Website of Partner or Company")
    comment = fields.Text(string='Notes')

    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                   column2='category_id', string='Tags', default=_default_category)
    barcode = fields.Char(oldname='ean13')
    active = fields.Boolean(default=True)
    customer = fields.Boolean(string='Is a Customer', default=True,
                              help="Check this box if this contact is a customer.")
    supplier = fields.Boolean(string='Is a Vendor',
                              help="Check this box if this contact is a vendor. "
                                   "If it's not checked, purchase people will not see it when encoding a purchase order.")
    employee = fields.Boolean(help="Check this box if this contact is an Employee.")
    function = fields.Char(string='Job Position')
    type = fields.Selection(
        [('contact', 'Contact'),
         ('payment_manager', 'Payment Manager'),
         ('technical_manager', 'Technical Manager'),
         ('domain_manager', 'Domain Manager'),
         ('helpdesk_manager', 'Helpdesk Manager'),
         ('other', 'Other address')], string='Address Type',
        default='contact',
        help="Used to select automatically the right address according to the context in sales and purchases documents.")
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char()
    phone = fields.Char()
    fax = fields.Char()
    mobile = fields.Char()
    is_company = fields.Boolean(string='Is a Company', default=False,
                                help="Check if the contact is a company, otherwise it is a person")
    # company_type is only an interface field, do not use it in business logic
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company'), ('agency', 'Agency')],
                                    readonly=False)
    company_id = fields.Many2one('res.company', 'Company', index=True, default=_default_company)
    color = fields.Integer(string='Color Index', default=0)
    contact_address = fields.Char(compute='_compute_contact_address', string='Complete Address')
    company_name = fields.Char('Company Name')

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as avatar for this contact, limited to 1024x1024px", )
    image_medium = fields.Binary("Medium-sized image", attachment=True,
                                 help="Medium-sized image of this contact. It is automatically " \
                                      "resized as a 128x128px image, with aspect ratio preserved. " \
                                      "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
                                help="Small-sized image of this contact. It is automatically " \
                                     "resized as a 64x64px image, with aspect ratio preserved. " \
                                     "Use this field anywhere a small image is required.")
    # hack to allow using plain browse record in qweb views, and used in ir.qweb.field.contact
    self = fields.Many2one(comodel_name=_name, compute='_compute_get_ids')
    parent_id_state = fields.Selection(related="parent_id.state")
    parent_id_customer = fields.Boolean(related="parent_id.customer")
    indentify_number = fields.Char(string='Indentify Card/Passport Number')
    date_of_birth = fields.Date(string='Date of Birth')
    date_of_founding = fields.Date(string='Date of Founding')
    gender = fields.Selection(
        [('male', 'Male'),
         ('female', 'Female'),
         ('others', 'Others')],
        string='Gender')
    info_types = fields.Many2one('mb.data.contact.type', string='Info Types')
    info_types_organization = fields.Many2one('mb.data.contact.type', string='Info Types')
    contact_type = fields.Many2one('mb.data.contact.type', string='Contact Type', compute='_get_contact_type')
    parent_company_type_com = fields.Selection(
        selection=[('person', 'Individual'), ('company', 'Company'), ('agency', 'Agency')],
        default='person', compute='get_company_type', string="Parent Company Type")
    parent_id_customer_com = fields.Boolean(compute="get_is_customer", string="Parent Is Customer")
    mobile_show = fields.Char(related='mobile')
    email_show = fields.Char(related='email')

    @api.depends('parent_id', 'parent_id.customer')
    def get_is_customer(self):
        for contact in self:
            contact.customer = contact.parent_id and contact.parent_id.customer or False

    @api.depends('parent_id', 'parent_id.company_type')
    def get_company_type(self):
        for contact in self:
            contact.parent_company_type_com = contact.parent_id and contact.parent_id.company_type or False

    # @api.depends('parent_id', 'parent_id.company_type')
    # def _compute_parent_company_type_com(self):
    #     for line in self:
    #         line.parent_company_type_com = line.parent_id and line.parent_id.company_type
    #
    # @api.depends('parent_id', 'parent_id.customer')
    # def _compute_parent_id_customer_com(self):
    #     for line in self:
    #         line.parent_id_customer_com = line.parent_id and line.parent_id.customer

    @api.depends('type')
    def _get_contact_type(self):
        for contact in self:
            contact.contact_type = contact.type and self.env['mb.data.contact.type'].search(
                [('code', '=', contact.type)], limit=1).id or self.env['mb.data.contact.type'].search(
                [('code', '=', 'contact')], limit=1).id

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    @api.one
    def _compute_get_ids(self):
        self.self = self.id

    @api.depends(lambda self: self._display_address_depends())
    def _compute_contact_address(self):
        for partner in self:
            partner.contact_address = partner._display_address()

    def _display_address_depends(self):
        # field dependencies of method _display_address()
        return self._address_fields() + [
            'country_id.address_format', 'country_id.code', 'country_id.name',
            'company_name', 'state_id.code', 'state_id.name',
        ]

    @api.multi
    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self.country_id.address_format or \
                         "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',
            'company_name': self.commercial_company_name or '',
        }
        for field in self._address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    @api.onchange('info_types')
    def onchange_info_types(self):
        import logging
        logging.info("-------------------------")
        active_id = self.env.context.get('default_parent_id')
        partner_env = self.env['res.partner']
        if not self.info_types:
            return
        else:
            if active_id:
                parnert_obj = partner_env.browse(active_id)
                obj_info = False
                if self.info_types and self.info_types.code == 'customer':
                    obj_info = parnert_obj or False
                elif self.info_types and self.info_types.code != 'customer':
                    children_customer = parnert_obj.contact_ids.filtered(
                        lambda c: c.type == self.info_types.code)
                    obj_info = children_customer and children_customer[0] or False
                logging.info("************** %s ****************", obj_info)
                if obj_info:
                    self.update({
                        'date_of_birth': obj_info.date_of_birth or False,
                        'gender': obj_info.gender or '',
                        'street': obj_info.street or '',
                        'street2': obj_info.street2 or '',
                        'city': obj_info.city or '',
                        'state_id': obj_info.state_id and obj_info.state_id.id or False,
                        'zip': obj_info.zip or '',
                        'country_id': obj_info.country_id and obj_info.country_id.id or False,
                        'name': obj_info.name or '',
                        'indentify_number': obj_info.indentify_number or '',
                        'function': obj_info.function or '',
                        'email': obj_info.email or '',
                        'phone': obj_info.phone or '',
                        'mobile': obj_info.mobile or '',
                        'fax': obj_info.fax or '',
                        'comment': obj_info.comment or '',
                    })

    @api.onchange('info_types_organization')
    def onchange_info_types_organization(self):
        active_id = self.env.context.get('active_id_from_wizard')
        if not self.info_types_organization:
            return
        else:
            if active_id:
                parnert_obj = self.browse(active_id)
                obj_info = False
                if self.info_types_organization and self.info_types_organization.code == 'customer':
                    obj_info = parnert_obj and parnert_obj.parent_id or False
                elif self.info_types_organization and self.info_types_organization.code != 'customer':
                    children_customer = parnert_obj.parent_id.contact_ids.filtered(
                        lambda c: c.type == self.info_types_organization.code)
                    obj_info = children_customer and children_customer[0] or False
                if obj_info:
                    self.date_of_birth = obj_info.date_of_birth or False
                    self.gender = obj_info.gender or ''
                    self.street = obj_info.street or ''
                    self.street2 = obj_info.street2 or ''
                    self.city = obj_info.city or ''
                    self.state_id = obj_info.state_id and obj_info.state_id.id or False
                    self.zip = obj_info.zip or ''
                    self.country_id = obj_info.country_id and obj_info.country_id.id or False
                    self.name = obj_info.name or ''
                    self.indentify_number = obj_info.indentify_number or ''
                    self.function = obj_info.function or ''
                    self.email = obj_info.email or ''
                    self.phone = obj_info.phone or ''
                    self.mobile = obj_info.mobile or ''
                    self.fax = obj_info.fax or ''
                    self.comment = obj_info.comment or ''


