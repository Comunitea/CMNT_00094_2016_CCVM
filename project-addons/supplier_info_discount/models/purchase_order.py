# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp

class ProductSupplierinfo(models.Model):

    _inherit = "product.supplierinfo"

    discount = fields.Float(
        string='Descuento (%)', digits=dp.get_precision('Discount'), default=0.00)
    min_discount_qty = fields.Float("Cantidad min (%)", default=1.00)

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange('product_qty', 'product_id')
    def _onchange_quantity(self):
        self.discount = 0.00
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime('%Y-%m-%d')

        if not seller:
            return

        if self.product_qty >= seller.min_discount_qty:
            self.discount = seller.discount

        res = super(PurchaseOrderLine, self)._onchange_quantity()