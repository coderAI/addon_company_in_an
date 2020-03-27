# -*- coding: utf-8 -*-
{
    'name': 'Project matbao installer',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
This module will install all module dependencies of matbao.
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'base_vat',
        'sale',
        'purchase'
    ],
    'data': [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        # 'security/',
        'security/ir.model.access.csv',
        'security/res_groups_data.xml',
        'security/sale_security_rule.xml',
        # ============================================================
        # DATA
        # ============================================================
        # 'data/',
        'data/ir_sequence_data.xml',
        'data/res_partner_data.xml',
        'data/res_partner_source_data.xml',
        'data/ir_cron_data.xml',
        'wizard/service_addon_order_lines_wizard.xml',
        'wizard/search_customer_wizard.xml',
        'wizard/match_payment_wizard.xml',
        'wizard/unreconcile_bank_transaction_wizard.xml',
        # ============================================================
        # VIEWS
        # ============================================================
        # 'view/',
        'views/sale/sale_order_view.xml',
        'views/sale/sale_service_view.xml',
        'views/sale/bank_transaction_view.xml',
        'views/sale/sale_config_settings_view.xml',
        'views/product/product_template_view.xml',
        'views/product/product_category_view.xml',
        'views/product/product_uom_view.xml',
        'views/base/res_partner_view.xml',
        'views/base/restrict_export_view.xml',
        'views/external/external_config_view.xml',
        'views/crm/crm_team_view.xml',
        'views/account/account_invoice_view.xml',
        'views/purchase/res_config_views.xml',
        'views/purchase/purchase_order_view.xml',
        # ============================================================
        # MENU
        # ============================================================
        # 'menu/',
        'menu/sale_menu.xml',
        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        'data/matbao_update_functions_data.xml',
    ],

    'test': [],
    'demo': [],

    'installable': True,
    'active': False,
    'application': True,
}
