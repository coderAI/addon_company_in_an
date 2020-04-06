{
    'name': 'MB Sale Target',
    'category': 'matbao',
    'author': 'Huy Snow',
    'description': '',
    'depends': [
        'sales_team',
        'sale',
        'mb_sale_invoice',
        'matbao_module',
        'mb_sale_contract',
        # 'mb_customer_contact',
        # 'mb_fix_milestone',
        'base',

    ],
    'data': [
        'views/sale_target_view.xml',
        'views/product_category_view.xml',
        'wizards/mass_create_lead_view.xml',
        # 'views/res_partner_view.xml',

        'security/ir.model.access.csv',
        'security/ir_rule.xml',


    ],

}