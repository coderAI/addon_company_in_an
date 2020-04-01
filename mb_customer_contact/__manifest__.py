{
    'name': 'MB Customer Contact',
    'category': 'matbao',
    'author': '',
    'description': 'Split contact from Customer to new model',
    'depends': [
        'matbao_module',
        'matbao_support',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_contact.xml',
        'reports/organization_res_partner_report.xml',
        'reports/person_res_partner_report.xml',
    ],
    'installable': True,
}