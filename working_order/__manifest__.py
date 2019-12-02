# Copyright 2016-2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Working order',
    'author': 'Snow',
    'category': 'sale',
    'version': '1.0',
    'depends': [
        'base', 'sale', 'stock',
    ],
    'data': [
        # 'security/kop_security.xml',
        'security/ir.model.access.csv',
        #
        'views/menu.xml',
        # 'views/region_type_view.xml',
        # 'views/shift_time_view.xml',
        # 'views/fleet_vehicle_view.xml',
        'views/sale_order_view.xml',
        # 'views/transfer_order_view.xml',
        #### Config
        'views/reason_cancel_view.xml',
        'views/store_info_view.xml',
        'views/market_place_view.xml',
        'views/delivery_method_view.xml',
        'views/platfrom_list_view.xml',
    ],
    'installable': True,
}
