# -*- coding: utf-8 -*-
{
    'name': "CHILI Affiliate Report",

    'summary': """""",

    'description': """""",

    'author': "CHILI Company - Nguyễn Huỳnh Khanh",
    'website': "https://www.chili.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Apps',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','chili_affiliate'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'active': False,
    'application': True,
}