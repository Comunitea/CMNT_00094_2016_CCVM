# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class WzRequestMaterial(models.TransientModel):
    _name = 'request.material.wz'

    user_id = fields.Many2one('res.users',
                              default=lambda self: self._uid, required=True)
    line_ids = fields.One2many('request.material.wz.line',
                               'request_material_wz_id')
    request_date = fields.Datetime(string="Request date",
                                   default=fields.Datetime.now)
    wz_type = fields.Selection([('request', 'Request'), ('return', 'Return')],
                               default='request', required=True)
    location_dest_id = fields.Many2one(
        'stock.location', string="Outbuilding", required=True,
        domain=[('outbuilding_location', '=', True)],
        default=lambda self: self.env.user.default_outbuilding_location_id.id)

    @api.multi
    def create_requests(self):

        request = self.env['request.material']
        request_vals = {'location_dest_id': self.location_dest_id.id}
        new_request_ids = []
        purchase_lines = []
        for line in self.line_ids:

            if line.requested_qty == 0.00:
                raise ValidationError(_('Request with qty = 0 or stock = 0'))
            if line.requested_qty > line.product_id.qty_available:
                line.state = 'stock_error'
                purchase_lines.append(
                    {'product_id': line.product_id.id,
                     'product_uom_id': line.uom_id.id,
                     'product_qty': line.requested_qty - line.product_id.qty_available})

            new_request_ids = []
            new_request = request.create(request_vals)
            create_pick = True
            line.request_type = line.request_type or 'to_return'

            request_line_vals = {'selected': line.selected,
                                 'user_id': line.user_id.id,
                                 'product_id': line.product_id.id,
                                 'requested_qty': line.requested_qty,
                                 'pending_qty': 0.00,
                                 'request_type': line.request_type,
                                 'returned_qty': 0.00,
                                 'location_dest_id': self.location_dest_id.id,
                                 'request_date': line.request_date,
                                 'notes': line.notes,
                                 'state': line.state,
                                 'request_material_id': new_request.id,
                                 'move_qty': line.requested_qty}

            if line.request_material_line_id:
                new_request_ids.append(
                    (1, line.request_material_line_id.id, request_line_vals))
            else:
                new_request_ids.append((0, 0, request_line_vals))

            if not new_request_ids:
                raise ValidationError(_('No lines'))

            new_request.write({'line_ids': new_request_ids})

            if create_pick:
                new_pick = new_request.create_pick()
        if purchase_lines:
            self.env['purchase.requisition'].create(
                {'line_ids': [(0, 0, x) for x in purchase_lines],
                 'origin': 'solicitud'})


        context = dict(self.env.context or {})
        return {
            'name': _('Request Material'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'request.material.line',
            'type': 'ir.actions.act_window',
            'res_id': new_request_ids,
            'context': context}

    @api.multi
    def create_request(self):
        if not self.line_ids:
            raise ValidationError(_('No lines to create request'))
        return self.create_requests()


class RequestMaterialWzLine(models.TransientModel):
    _name = 'request.material.wz.line'

    @api.model
    def default_get(self, fields):
        res = super(RequestMaterialWzLine, self).default_get(fields)
        return res

    request_material_wz_id = fields.Many2one('request.material.wz')
    selected = fields.Boolean("Selected", default=True)
    user_id = fields.Many2one('res.users', default=lambda self: self._uid)
    product_id = fields.Many2one('product.product', required=True)
    uom_id = fields.Many2one(related='product_id.uom_id')
    requested_qty = fields.Float("Request quantity", default=1.00,
                                 required=True)
    returned_qty = fields.Float("Return quantity", default=0.00)
    request_type = fields.Selection(
        [('to_scrap', 'Scrap'), ('to_return', 'To return'), ('tool', 'Tool')],
        string='To scrap',
        default=lambda self: self.product_id.request_type or 'to_return',
        help="Scrap: Material will be moved to scrap location, \nTo return: "
             "Material must be returned (Quantities)\nTool : "
             "Must be returned always")
    request_date = fields.Datetime(string="Request date",
                                   default=fields.Datetime.now)
    location_dest_id = fields.Many2one('stock.location')

    notes = fields.Text(
        'Notes', translate=True,
        help="Comments about this request")
    request_material_line_id = fields.Many2one('request.material.line')
    state = fields.Selection([('new', 'New'),
                              ('open', 'Open'),
                              ('done', 'Delivered'),
                              ('stock_error', 'Stock error'),
                              ('closed', 'Closed')
                              ],
                             string='Status', required=True, readonly=True,
                             copy=False, default='new')

    @api.onchange('requested_qty', 'product_id')
    def onchange_requested_qty(self):
        if self.product_id:
            if self.requested_qty > self.product_id.qty_available:
                raise ValidationError(
                    _('No hay cantidad suficiente. \nStock de %s %s' %
                        (self.product_id.name, self.product_id.uom_id.name)))

            self.request_type = self.product_id.product_tmpl_id.request_type
