# -*- coding: utf-8 -*-
from odoo import http

# class NcManagement(http.Controller):
#     @http.route('/nc_management/nc_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nc_management/nc_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nc_management.listing', {
#             'root': '/nc_management/nc_management',
#             'objects': http.request.env['nc_management.nc_management'].search([]),
#         })

#     @http.route('/nc_management/nc_management/objects/<model("nc_management.nc_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nc_management.object', {
#             'object': obj
#         })