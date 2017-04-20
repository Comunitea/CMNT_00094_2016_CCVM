# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


{
    'name': 'Modulo CCVM Request Material',
    'version': '10.0',
    'author': 'Comunitea, ',
    "category": "",
    'license': 'AGPL-3',
    'description': 'Request Material',
    'depends': [
        'product', 'stock', 'purchase_requisition'
    ],
    'contributors': [
        "Comunitea",
        "Kiko Sanchez<kiko@comunitea.com>", ],
    "data": [
        'security/request_material_security.xml',
        'security/ir.model.access.csv',
        'views/request_material.xml',
        'views/stock_location.xml',
        'wizard/request_material_wz.xml',
        'report/report_stock_inventory.xml',
        'report/report_request_material.xml'
    ],
    "demo": [

    ],
    'test': [

    ],
    'installable': True
}
