{
    'name': 'MB Custom Pipeline',
    'category': 'matbao',
    'author': 'Huy Snow',
    'description': 'Custom view and logic load page support preforment',
    'depends': [
        'base',
        'crm',
        'matbao_module',
        'sales_team',
        'mb_cs_bugs',
        'mb_fix_milestone4',

    ],
    'data': [
        'views/crm_case_form_view_leads_view.xml',
        'views/res_partner_category_view.xml',


    ],
    'installable': True,
}