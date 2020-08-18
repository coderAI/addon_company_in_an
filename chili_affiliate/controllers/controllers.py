# -*- coding: utf-8 -*-
from odoo import http

# class ChiliAffiliate(http.Controller):
#     @http.route('/chili_affiliate/chili_affiliate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/chili_affiliate/chili_affiliate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('chili_affiliate.listing', {
#             'root': '/chili_affiliate/chili_affiliate',
#             'objects': http.request.env['chili_affiliate.chili_affiliate'].search([]),
#         })

#     @http.route('/chili_affiliate/chili_affiliate/objects/<model("chili_affiliate.chili_affiliate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('chili_affiliate.object', {
#             'object': obj
#         })