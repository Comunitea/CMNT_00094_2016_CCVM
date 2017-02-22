{
    'name': 'Request Material',
    'category': 'Website',
    'sequence': 55,
    'summary': 'Request MaterialOnline',
    'website': 'http://www.comunitea.com',
    'version': '1.0',
    'description': """
Odoo E-Commerce
==================

        """,
    'depends': ['website'],
    'data': [
        'data/reqquest_data.xml',

        # 'security/ir.model.access.csv',
        # 'security/website_sale.xml',
        # 'data/data.xml',
        # 'data/web_planner_data.xml',
        # 'views/views.xml',
        # 'views/backend.xml',
        # 'views/templates.xml',
        # 'views/payment.xml',
        # 'views/product_attribute_views.xml',
        # 'views/sale_order.xml',
        # 'views/snippets.xml',
        # 'views/report_shop_saleorder.xml',
        # 'views/res_config_view.xml',
    ],
    'demo': [
        #'data/demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': False,
    'application': True,
}
