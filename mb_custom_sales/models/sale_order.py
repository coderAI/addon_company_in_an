# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import logging
from odoo.exceptions import Warning
from datetime import datetime,date, timedelta

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)
STATE=['sale', 'paid', 'completed', 'done','cancel']

class ServiceAddonOrderLinesWizard(models.TransientModel):
    _inherit = "service.addon.order.lines.wizard"

    def check_addon_list(self,product_category_id):
        res=[]
        if product_category_id:
            product_category = self.env['product.category'].search([('id','=',product_category_id)], limit=1)

            if product_category.parent_id:
                list=[]
                list.append(product_category.parent_id.id)
                while list != []:
                    list = self.env['product.category'].search(
                        [('parent_id', 'in', product_category.parent_id.id),('is_addons','=',False), ('active', '=', True)]).ids
                    if list == []:
                        break
                    else:
                        res=res+list
        return res

    @api.multi
    def write_service_orders(self):
        for line in self.line_ids:
            if line.register_type == 'register':
                is_add_service = self._context.get('service')
                add_product_category_config_id = self.env['add.product.category.config'].search(
                    [('product_category_id', '=', line.product_category_id.id), ('active', '=', True)], limit=1)
                if add_product_category_config_id.id:
                    _logger.info('null')
                else:
                    product_category_id_tmp = line.product_category_id
                    while product_category_id_tmp.parent_id:
                        add_product_category_config_id = self.env['add.product.category.config'].search(
                            [('product_category_id', '=', product_category_id_tmp.id), ('active', '=', True)], limit=1)
                        if add_product_category_config_id.id:
                            break
                        product_category_id_tmp = product_category_id_tmp.parent_id
                product_name_tmp=line.product_name
                product_id = self.create_product_when_add_service(line, is_add_service)
                product_name = is_add_service and line.product_name.strip() or \
                               line.parent_product_id and line.parent_product_id.name.strip()
                line.write({'product_id': product_id,
                            'product_name': product_name
                            })
                if add_product_category_config_id.id:
                    for product_category_config in add_product_category_config_id.product_category_ids:
                        if product_category_config.uom_id.id == 22:
                            time = 1
                        else:
                            time= line.time
                        vals = {
                            'parent_id' :self.ids[0],
                            'test': line.test,
                            'is_service': line.is_service,
                            'register_type': 'register',
                            'product_category_id':product_category_config.id,
                            'time': time,
                            'product_name': product_name_tmp,
                            'product_uom_id': product_category_config.uom_id.id,
                            'template': line.template,
                        }
                        if product_category_config.is_addons:
                            vals.update({'parent_product_id': product_id})
                        self.env['order.lines.wizard'].create(vals)
        return super(ServiceAddonOrderLinesWizard, self).write_service_orders()


class renew_reason(models.Model):
    _name = 'renew.reason'
    name = fields.Char('Reason')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('sequence')
    description = fields.Text('Short Description')

class CrmRating(models.Model):
    _name = 'crm.rating'
    name = fields.Char('Rating Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('sequence')
    description = fields.Text('Short Description')

class CrmLeadRating(models.Model):
    _name = 'crm.lead.rating'
    number_lock = fields.Integer('Number Lock')
    lead_id = fields.Many2one('crm.lead', 'Pipeline')
    team_id = fields.Many2one('crm.team', 'Sale Team')
    user_id = fields.Many2one('res.users', 'Salesperson')
    rating_id = fields.Many2one('crm.rating', 'Rating')
    date_lock = fields.Date(string='Date',default=datetime.today())

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        args.append(('user_id.company_id', '=', self.env.user.company_id.id))
        return super(CrmLeadRating, self).search(args, offset, limit, order, count=count)

class tmp_reason_cancel_so_update_data(models.Model):
    _name = 'tmp.reason.cancel.so.update.data'
    name = fields.Char('Reason Old Name')
    reason_cancel_so_id = fields.Many2one('reason.cancel.so', 'Reason Now')


    def btn_udpate_id(self):
        if self.name and self.reason_cancel_so_id:
            sql = '''	update sale_order_line_delete sold
				set reason_id =  %s
				where sold.reason = '%s' ''' % (self.reason_cancel_so_id.id, self.name)
            self.env.cr.execute(sql)




class CrmLeadRatingHistory(models.Model):
    _name = 'crm.lead.rating.history'
    number_lock = fields.Integer('Number Lock')
    lead_id = fields.Many2one('crm.lead', 'Pipeline')
    team_id = fields.Many2one('crm.team', 'Sale Team')
    user_id = fields.Many2one('res.users', 'Salesperson')
    rating_id = fields.Many2one('crm.rating', 'Rating')
    date_lock = fields.Date(string='Date',default=datetime.today())


class CrmLead(models.Model):
    _inherit = 'crm.lead'
    crm_rating_ids = fields.Many2many('crm.rating', 'crm_lead_rating_rel', 'lead_id', 'rating_id', string='Rating Check and Feedback',track_visibility='onchange', required=True)
    rating_check = fields.Text('Rating Check and Feedback note',track_visibility='onchange')
    crm_lead_rating_ids = fields.One2many('crm.lead.rating', 'lead_id')
    crm_lead_rating_history_ids = fields.One2many('crm.lead.rating.history', 'lead_id')
    description_rating = fields.Text('Short Description',track_visibility='onchange')

    @api.model
    def create(self, values):
        list_crm_lead_rating = []

        for i in values.get('crm_rating_ids')[0][2]:
            vals_crm_lead_rating = {
                'rating_id': i,
                'number_lock':1,
                'team_id':values.get('team_id'),
                'user_id':values.get('user_id') or self._uid,
            }
            list_crm_lead_rating.append([0,0,vals_crm_lead_rating])

        values.update({
            'crm_lead_rating_ids':list_crm_lead_rating,
            'crm_lead_rating_history_ids':list_crm_lead_rating,
        })
        return super(CrmLead, self).create(values)

    @api.multi
    def write(self, values):
        list_crm_lead_rating = []
        number_lock = False
        update_check = False
        for i in self.crm_lead_rating_ids:
            number_lock = i.number_lock
            break
        number_lock += 1

        if values.get('crm_rating_ids') and values.get('user_id'):
            for i in values.get('crm_rating_ids')[0][2]:
                vals_crm_lead_rating = {
                    'rating_id': i,
                    'number_lock': number_lock,
                    'team_id':values.get('team_id') or self.team_id.id,
                    'user_id':values.get('user_id'),
                }
                list_crm_lead_rating.append([0, 0, vals_crm_lead_rating])
            update_check = True
        elif values.get('user_id'):
            for i in self.crm_lead_rating_ids:
                vals_crm_lead_rating = {
                    'rating_id': i.rating_id.id,
                    'number_lock': number_lock,
                    'team_id':values.get('team_id') or self.team_id.id,
                    'user_id':values.get('user_id'),
                }
                list_crm_lead_rating.append([0, 0, vals_crm_lead_rating])
            update_check = True
        elif values.get('crm_rating_ids'):
            for i in values.get('crm_rating_ids')[0][2]:
                vals_crm_lead_rating = {
                    'rating_id': i,
                    'number_lock': number_lock,
                    'team_id':self.team_id.id,
                    'user_id':self.user_id.id,
                }
                list_crm_lead_rating.append([0, 0, vals_crm_lead_rating])
            update_check = True

        if update_check:
            self.crm_lead_rating_ids.unlink()
            values.update({
                'crm_lead_rating_ids': list_crm_lead_rating,
                'crm_lead_rating_history_ids': list_crm_lead_rating,
            })
        return super(CrmLead, self).write(values)

    @api.onchange('crm_rating_ids')
    def _onchange_crm_rating_ids(self):
        tmp_str=''
        for i in self.crm_rating_ids:
            tmp_str+=' '+i.name
        self.rating_check = tmp_str
        count = len(self.crm_rating_ids.ids)
        if count >= 6:
            self.priority = '3'
            self.probability = 80
        elif count > 2:
            self.priority='2'
            self.probability = 50
        else:
            self.priority='1'
            self.probability = 20

class SaleOrderLineDelete(models.Model):
    _inherit = 'sale.order.line.delete'

    order_id = fields.Many2one('sale.order',string="Sale Order")
    partner_id = fields.Many2one('res.partner')

    product_category_id = fields.Many2one('product.category',"Product Category")
    product_id = fields.Many2one('product.product',"Product")
    reason_id = fields.Many2one('reason.cancel.so',"Reason")

    user_id = fields.Many2one('res.users',"SalesPerson")
    team_id = fields.Many2one('crm.team', 'Sales Team')




class SaleOrder(models.Model):
    _inherit = 'sale.order'
    renew_reason_id = fields.Many2one('renew.reason','Renew Reason')
    renew_reason_description = fields.Text('Renew Reason Note')



    def btn_check_condition_with_this_order(self):
        sol=':'
        count=0
        checked = self.check_promotion_condition()
        if checked[0]:
            for part in checked[1]:
                count+=1
                sol+='(part'+str(count)
                for line in part:
                    sol+=' '+line.product_id.name+', '
                sol+=')'
            raise Warning( "sale order line pass this coupon condition"+sol)
        else:
            raise Warning("No sale order line pass this coupon condition")



    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if context.get('search_default_min_time') == 1:

            sql = '''
            select
            so.id
            from sale_order so
            where
            so.user_id is null
            and company_id = %s
            and so.id
            Not in
            (
                select so1.id
            from sale_order so1
            where
            so1.type = 'renewed'
            and now()::date - so1.create_date::date < 15
            and fully_paid = False
            )

            and so.id in
            (
                select so2.id
            from sale_order so2
            inner join sale_order_line sol1 on sol1.order_id = so2.id
            inner join product_category pc on pc.id = sol1.product_category_id
            where
            (now()::date - so2.create_date::date >= 32)
            or (now()::date - so2.create_date::date < 32 and pc.parent_id not in (5092, 4089, 4496))
            or (pc.parent_id in (5092, 4089, 4496) and so2.fully_paid = True)
            or so2.type != 'renewed'
            )
            '''% self.env.user.company_id.id
            self._cr.execute(sql)
            list_ids = [r[0] for r in self._cr.fetchall()]
            args += [('user_id','=',False),('id', 'in', list_ids)]
            return super(SaleOrder, self).search(args, offset, limit=len(list_ids), order=order, count=count)

        return super(SaleOrder, self).search(args, offset, limit=limit, order=order, count=count)

    def check_renew_reason(self,vals):
        res =False
        if vals.get('renew_reason_id') != None or  self.env.uid != SUPERUSER_ID or self.type != 'normal':
            if vals.get('renew_reason_id') == False:
                for i in self.order_line:
                    if i.register_type == 'renew':
                        raise Warning('Renew reason in sale order can not null with sale order line type RENEW')
                res =True
        else:
            res =False
        return res

    @api.multi
    def check_service_hddt(self):
        self.ensure_one()
        if any(categ.code and self.get_parent_product_category(self.env['product.category'].search([('code', '=', categ.code)], limit=1)).code == 'HDDT' for categ in self.order_line.mapped('product_category_id')):
            return True
        return False

    @api.multi
    def check_service_registry_lock(self):
        self.ensure_one()
        for categ in self.order_line.mapped('product_category_id'):
            if categ.code in ['HP20171904021902','HP20171904021901']:
                return True
        return False

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.state in STATE:
                raise Warning(_("This action not work please reload this page"))
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def action_send_request(self, order, date):
        for order in self:
            if order.date_order:
                dt_to = datetime.strptime(order.date_order, "%Y-%m-%d")
                raise Warning(_("This action not work please reload this page"))
        return super(SaleOrder, self).action_send_request(order, date)




    @api.multi
    def write(self, values):

        if values.get('partner_id'):
            for order in self:
                if order.state in STATE:
                    raise Warning(_("This action not work please reload this page"))
        return super(SaleOrder, self).write(values)


class get_sale_order(models.Model):
    _inherit = 'get.sale.order'

    renew_reason_id = fields.Many2one('renew.reason','Renew Reason')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_order_date_received = fields.Datetime(related='order_id.date_received',  string='Date Received', readonly=True)
    sale_order_team_id = fields.Many2one(related='order_id.team_id',  string='Sales team', readonly=True)
    sale_order_renew_reason_id = fields.Many2one(related='order_id.renew_reason_id',  string='Renew Reason', readonly=True)
    sale_order_renew_reason_description = fields.Text(related='order_id.renew_reason_description',  string='Renew Reason Note', readonly=True)
    sale_order_create_date = fields.Datetime(related='order_id.create_date', string='Creation Date', readonly=True)


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}

        if context.get('search_renew_reason_order_lines') == 1 and self._uid !=1:
            return self.sudo().search([('order_id.renew_reason_id','!=',False)]+ args)

            #return super(SaleOrderLine, self).sudo().search(args, offset, limit, order, count=count)
        res = super(SaleOrderLine, self).search(args, offset, limit, order, count=count)
        return res

    @api.multi
    def unlink(self):
        for sale_order_line in self:
            if sale_order_line.order_id.state in STATE:
                raise Warning(_("You can't delete this rec when Sale order in state is "+sale_order_line.order_id.status))
        if self._context.get('skip_delete_parent_product', True):
            for sale_order_line in self:
                self.search([('order_id','=',sale_order_line.order_id.id),('parent_product_id','=',sale_order_line.product_id.id)]).unlink()
        return super(SaleOrderLine, self).unlink()


    def check_renew_reason(self,vals):
        res =False
        if self.env.uid != SUPERUSER_ID:
            if vals.get('register_type') == 'renew':
                order =  self.env['sale.order'].browse(vals.get('order_id'))
                if order.renew_reason_id.id or order.type != 'normal':
                    pass
                else:
                    res =True
        return res

    @api.model
    def create(self, vals):
        if self.check_renew_reason(vals):
            raise Warning('Renew reason in sale order can not null with sale order line type RENEW')
        return super(SaleOrderLine, self).create(vals)