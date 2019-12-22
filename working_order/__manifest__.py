# Copyright 2016-2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Working order',
    'author': 'Snow',
    'category': 'sale',
    'version': '1.0',
    'depends': [
        'base', 'sale','account', 'stock','sale_stock',
    ],
    'data': [
        # 'security/kop_security.xml',
        'security/ir.model.access.csv',
        # data
        'data/ir_sequence_data.xml',
        'views/web_assets.xml',
        #
        'views/menu.xml',
        # 'views/region_type_view.xml',
        # 'views/shift_time_view.xml',
        # 'views/fleet_vehicle_view.xml',
        'views/sale_order_view.xml',
        'wizards/loading_sale_order_view.xml',
        # 'views/transfer_order_view.xml',
        'views/working_order_view.xml',
        'views/check_product_view.xml',
        #### Config
        'views/reason_cancel_view.xml',
        'views/store_info_view.xml',
        'views/market_place_view.xml',
        'views/delivery_method_view.xml',
        'views/platform_list_view.xml',

    ],
    "qweb": [
        'static/src/xml/widget_view.xml',
    ],
    'installable': True,
}
