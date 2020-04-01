{
    'name': 'MB Custom accounting',
    'category': 'matbao',
    'author': 'Huy Snow',
    'description': 'Custom view and logic load page support preforment',
    'depends': [
        'account',
        'account_reports',
        'mb_promotion',

        'mb_outsource_hp',

    ],
    'data': [
        'views/account_invoice.xml',
        'wizards/report_jounal_invoice_line_wizard.xml',

    ],
    'installable': True,
}