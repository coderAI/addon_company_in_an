{
    'name': 'MB Support 2',
    'category': 'matbao',
    'author': 'Nguyên Khang (khangdn@matbao.com)',
    'description': 'Module Support Mat Bao 2',
    'depends': [
        'matbao_support',
    ],
    'data': [
        # Securities
        'security/ir.model.access.csv',
        # Wizards
        # Views
        'views/base/res_partner.xml',
        'views/base/res_partner_history.xml',
        'views/sale/sale_order_view.xml',
        'views/sale/sale_config_settings_view.xml',
        # Reports
        # ============================================================
        # MENU
        # ============================================================
        # 'menu/',
        'menu/sale_menu.xml',
        # Templates
        'views/mb_templates.xml',
        # Datas
        'data/mail/email_template_data.xml',
    ],
    'installable': True,
    'active': False,
    'application': True,
}
