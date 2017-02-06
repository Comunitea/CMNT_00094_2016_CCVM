# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class WzRequestMaterial(models.TransientModel):
    _name = 'request.material.wz'

    user_id = fields.Many2one('res.users', default=lambda self: self._uid, required = True)
    line_ids = fields.One2many('request.material.wz.line', 'request_material_wz_id')
    request_date = fields.Datetime(string="Request date", default=fields.Datetime.now)
    wz_type = fields.Selection([('request', 'Request'),
                                ('return', 'Return')],
                               default='request', required = True)
    location_dest_id = fields.Many2one('stock.location', string="Outbuilding", required = True,
                                       domain=[('outbuilding_location', '=', True)],
                                       default=lambda self: self.env.user.default_outbuilding_location_id.id)

    @api.model
    def default_get(self, fields):

        res = super(WzRequestMaterial, self).default_get(fields)
        return res
        #TODO COmprobar si es necesario recuperar solicitudes anteriores.
        #
        #
        # line_ids = []
        # vals = []
        #
        # domain = [('user_id', '=', self._uid), ('state', '=', 'new')]
        # lines = self.env['request.material.line'].search(domain)
        #
        # for line in lines:
        #     vals.append((0, 0, {'selected': line.selected,
        #                         'user_id': line.user_id.id,
        #                         'product_id': line.product_id.id,
        #                         'uom_id': line.product_id.uom_id.id,
        #                         'requested_qty': line.requested_qty,
        #                         'returned_qty': line.returned_qty,
        #                         'request_type': line.request_type,
        #                         'location_dest_id': line.location_dest_id.id,
        #                         'request_date': line.request_date,
        #                         'request_material_line_id': line.id,
        #                         'state': line.state,
        #                         'notes': line.notes}))
        #
        # res.update({'line_ids': vals})
        # return res
        #

    # @api.multi
    # def create_return_(self):
    #     if not self.line_ids:
    #         raise ValidationError(_('No lines to create returns'))
    #     return self.create_returns()
    #
    #
    # @api.multi
    # def create_return(self):
    #     if not self.line_ids:
    #         raise ValidationError(_('No lines to create returns'))
    #
    #     return_line_vals = []
    #     context = dict(self.env.context or {})
    #     expended_qty = 0.0
    #     create_scrap = False
    #     for line in self.line_ids:
    #         if line.selected:
    #             if line.state != 'done':
    #                 raise ValidationError(_('You can only return delivered material'))
    #             line.request_material_line_id.returned_qty = line.returned_qty
    #
    #             if line.expended_qty:
    #                 create_scrap = True
    #
    #             line.state = 'done'
    #             return_line_vals += line.id
    #
    #     request_id = self.line_ids[0].request_material_id
    #     request_id.create_pick(type='return')
    #     if create_scrap:
    #         request_id.create_pick(type='scrap')
    #
    #     return {
    #         'name': _('Request Material'),
    #         'view_type': 'form',
    #         'view_mode': 'kanban,tree,form',
    #         'res_model': 'request.material.line',
    #         'type': 'ir.actions.act_window',
    #         'res_id': return_line_vals,
    #         'context': context,
    #     }
    #
    #     return

    @api.multi
    def create_requests(self):

        request = self.env['request.material']
        request_vals = {'location_dest_id': self.location_dest_id.id}
        new_request_ids = []
        for line in self.line_ids:
            if line.requested_qty == 0.00 or line.product_id.qty_available == 0.00:
                raise ValidationError (_('Request with qty = 0 or stock = 0'))

            new_request_ids = []
            new_request = request.create(request_vals)
            create_pick = True
            line.request_type = line.request_type or 'to_return'

            if line.request_type == 'to_scrap':
                returned_qty = 0.00
            else:
                returned_qty = line.requested_qty

            request_line_vals = {'selected': line.selected,
                                 'user_id': line.user_id.id,
                                 'product_id': line.product_id.id,
                                 'requested_qty': line.requested_qty,
                                 'request_type': line.request_type,
                                 'returned_qty': returned_qty,
                                 'location_dest_id': self.location_dest_id.id,
                                 'request_date': line.request_date,
                                 'notes': line.notes,
                                 'state': line.state,
                                 'request_material_id': new_request.id}

            if line.request_material_line_id:
                new_request_ids.append((1, line.request_material_line_id.id, request_line_vals))
            else:
                new_request_ids.append((0, 0, request_line_vals))

            if not new_request_ids:
                raise ValidationError(_('No lines'))

            new_request.write({'line_ids': new_request_ids})

            if create_pick and False:
                new_pick = new_request.create_pick()

                #new_request.do_requested_pick()

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

    request_material_wz_id = fields.Many2one('request.material.wz')
    selected = fields.Boolean("Selected", default=True)
    user_id = fields.Many2one('res.users', default=lambda self: self._uid)
    product_id = fields.Many2one('product.product', required = True)#, domain = [('qty_available', '>', 0)])
    uom_id = fields.Many2one(related='product_id.uom_id')
    requested_qty = fields.Float("Request quantity", default=1.00, required = True)
    returned_qty = fields.Float("Return quantity", default=0.00)
    request_type = fields.Selection([('to_scrap', 'Scrap'),
                                     ('to_return', 'To return'),
                                     ('tool', 'Tool')
                                     ], string='To scrap'
                                    , default=lambda self: self.product_id.request_type or 'to_return',
                                    help="Scrap: Material will be moved to scrap location, \n"
                                         "To return: Material must be returned (Quantities)\n"
                                         "Tool : Must be returned always")
    request_date = fields.Datetime(string="Request date", default=fields.Datetime.now)
    location_dest_id = fields.Many2one(related='request_material_wz_id.location_dest_id')

    notes = fields.Text(
        'Notes', translate=True,
        help="Comments about this request")
    request_material_line_id = fields.Many2one('request.material.line')
    state = fields.Selection([('new', 'New'),
                              ('open', 'Open'),
                              ('done', 'Delivered'),
                              ('closed', 'Closed')
                              ],
                             string='Status', required=True, readonly=True,
                             copy=False, default='new')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            if self.product_id.qty_available == 0.00:
                raise ValidationError (_('No qty available. Stock = 0'))

            self.request_type = self.product_id.product_tmpl_id.request_type

    @api.multi
    def create(self, vals):
        return super(RequestMaterialWzLine, self).create(vals)
