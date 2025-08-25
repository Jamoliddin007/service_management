# -*- coding: utf-8 -*-
# from odoo import http


# class ServiceManagement(http.Controller):
#     @http.route('/service_management/service_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/service_management/service_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('service_management.listing', {
#             'root': '/service_management/service_management',
#             'objects': http.request.env['service_management.service_management'].search([]),
#         })

#     @http.route('/service_management/service_management/objects/<model("service_management.service_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('service_management.object', {
#             'object': obj
#         })

