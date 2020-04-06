{
    'name': 'MB Sale Invoice',
    'category': 'matbao',
    'author': 'congdpt',
    'description': 'Module for Invoice, Contract and Sale Order',
    'depends': [
        'matbao_module',
        'matbao_support2',
        'mbcorp_general',
        'mb_account_report',
        'mb_cs_bugs',
        'mb_fix_milestone4',
        'mb_outsource_hp',
        'mb_service_report',
        'mb_report',
        'mb_vat_invoice_custom',
        'stock',
    ],
    'data': [
        # Reports
        'reports/contract_mb.xml',
        'reports/receipt_report_template.xml',
        'reports/sale_report.xml',
        # Data
        'data/mail_template.xml',
        # Wizards
        'wizards/sale_order_receipt_wizard.xml',
        # Views
        'views/bank_transaction.xml',
        'views/mb_sale_contract.xml',
        'views/product_agency_price.xml',
        'views/product_category.xml',
        'views/res_partner.xml',
        'views/reseller_customer.xml',
        'views/sale_order.xml',
        'views/sale_order_line.xml',
        'views/sale_phone_history.xml',
        'views/sale_service.xml',
        'views/web_assets.xml',
        # Menu
        'menu/menu.xml',
        # Security
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
    ],
    "qweb": [
        'static/src/xml/*.xml',
    ],
    'installable': True,
}