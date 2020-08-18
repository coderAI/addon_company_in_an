# -*- coding: utf-8 -*-
{
    'name': "CHILI Affiliate",

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
    'depends': ['base','crm','matbao_module','mb_fix_milestone3'],

    # always loaded
    'data': [

        'views/affiliate_views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [''],
    'installable': True,
    'active': False,
    'application': True,
}