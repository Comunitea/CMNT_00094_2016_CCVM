# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api


class StockLocation(models.Model):
    _inherit = "stock.location"
    outbuilding_location = fields.Boolean(
        "Outbuilding Location", help="Location to select in material request")


class ProductProduct(models.Model):
    _inherit = "product.template"

    request_type = fields.Selection(
        [('to_scrap', 'Scrap'), ('to_return', 'To return'), ('tool', 'Tool')],
        'Request type',
        help="What happen with this product by default when his requests"
        " are closed:\nScrap: Material will be moved to scrap location,"
        " \nTo return: Material must be returned (Quantities)\nTool : Must "
        "be returned always")


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"
    request_type_id = fields.Many2one('stock.picking.type', 'Request Type')
    expend_type_id = fields.Many2one('stock.picking.type', 'Expends Type')


class StockPicking(models.Model):
    _inherit = "stock.picking"
    request_material_id = fields.Many2one("request.material",
                                          "Request Material")

    @api.multi
    def write(self, vals):
        # TODO: Comprobar que no se puede mofificar si hay un
        # request_material_id
        return super(StockPicking, self).write(vals)


class StockMove(models.Model):
    _inherit = "stock.move"
    request_material_line_id = fields.Many2one("request.material.line",
                                               "Request Material Line")


class ResUser(models.Model):
    _inherit = "res.users"
    default_outbuilding_location_id = fields.Many2one(
        'stock.location', "Default Outbuilding Location",
        domain=[('outbuilding_location', '=', True)])


class StockPackOperationProduct(models.Model):
    _inherit = "stock.pack.operation"
    request_material_line_id = fields.Many2one("request.material.line",
                                               "Request Material Line")
