# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class RequestMaterial(models.Model):
    _name = "request.material"

    user_id = fields.Many2one('res.users', default=lambda self: self._uid)
    request_date = fields.Datetime(string="Request date", default=fields.Datetime.now)
    line_ids = fields.One2many('request.material.line', 'request_material_id')
    display_name = fields.Char(compute='_compute_display_name')
    location_dest_id = fields.Many2one('stock.location', string="Outbuilding",
                                       domain=[('outbuilding_location', '=', True)])
    picking_ids = fields.One2many('stock.picking', 'request_material_id')

    @api.one
    @api.depends('line_ids')
    def _compute_display_name(self):
        if self.line_ids:
            self.display_name = self.request_date + ' / ' + self.line_ids[0].outbuilding
        else:
            self.display_name = self.request_date + ' / ' + "Outbuilding"

    def create_pick(self, type='request'):
        # Crea un picking adecuado, con sus stock_moves
        # los valida, reserva y crea stock_pack_operation
        print 'Crear un pick para %s: %s' % (self.id, type)

        new_picking = self.env['stock.picking']
        request_line_vals = []
        pick = self.env['stock.picking']
        wh = self.env['stock.warehouse'].browse([1])
        request_picking_type = wh.request_type_id
        return_picking_type = request_picking_type.return_picking_type_id
        expend_picking_type = wh.expend_type_id
        origin = False
        if type == 'request':
            picking_type = request_picking_type
        elif type == 'return':
            picking_type = return_picking_type
            origin = self.picking_ids and self.picking_ids[0].name or ''
        else:
            picking_type = expend_picking_type
            origin = self.picking_ids and self.picking_ids[0].name or ''

        if not request_picking_type:
            raise ValidationError(_('Request picking type not found'))

        if not return_picking_type:
            raise ValidationError(_('Return picking type not found'))

        if not expend_picking_type:
            raise ValidationError(_('Expend picking type not found'))
        line = []

        for product_line in self.line_ids:
            product_line.location_id = request_picking_type.default_location_src_id.id
            if product_line.state != 'new' and type == 'request':
                raise ValidationError(_('Incorrect request state to ceate a request pick'))
            if product_line.selected:
                line_vals = {
                    'date_expected': product_line.request_date,
                    'location_dest_id': product_line.location_dest_id.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'name': product_line.product_id.name,
                    'picking_type_id': picking_type.id,
                    'product_id': product_line.product_id.id,
                    'product_uom': product_line.product_id.uom_id.id,
                    'product_uom_qty': product_line.requested_qty,
                    'request_material_line_id': product_line.id,
                    'state': 'draft'}
                if type == 'return':
                    line_vals['location_id'] = product_line.location_dest_id.id
                    line_vals['location_dest_id'] = product_line.location_id.id
                    line_vals['product_uom_qty'] = product_line.returned_qty

                if type == 'scrap':
                    line_vals['location_id'] = product_line.location_dest_id.id
                    line_vals['location_dest_id'] = picking_type.default_location_dest_id.id
                    line_vals['product_uom_qty'] = product_line.expended_qty

            line += [[0, False, line_vals]]

        if not line:
            return False

        vals = {
            'request_material_id': self.id,
            'picking_type_id': picking_type.id,
            'min_date': self.request_date,
            'move_lines': line,
            'origin': origin
        }
        # busco pick y si no lo creo
        if type == 'request':
            vals['location_id'] = picking_type.default_location_src_id.id
            vals['location_dest_id'] = self.location_dest_id.id
        elif type == 'return':
            vals['location_id'] = self.location_dest_id.id
            vals['location_dest_id'] = request_picking_type.default_location_src_id.id
        elif type == 'scrap':
            vals['location_id'] = self.location_dest_id.id
            vals['location_dest_id'] = picking_type.default_location_dest_id.id

        domain = [('request_material_id', '=', self.id), ('picking_type_id', '=', picking_type.id)]
        request_picking = pick.search(domain, limit=1)
        if not request_picking:
            request_picking = pick.create(vals)
            self.picking_ids = [(4, request_picking.id)]

        return request_picking



        # asignamos operations y moves a cada linea de request.material.line

    def do_requested_pick(self):
        # busco el picking asociado
        wh = self.env['stock.warehouse'].browse([1])
        request_picking_type = wh.request_type_id
        domain = [('request_material_id', '=', self.id), ('picking_type_id', '=', request_picking_type.id)]
        pick = self.env['stock.picking'].search(domain, limit=1)

        if not pick:
            raise ValidationError(_('Pick Error'))
            # confimamos picking
        if not pick.action_confirm():
            raise ValidationError(_('Error en action confirm'))

        # creamos operaciones
        if not pick.action_assign():
            raise ValidationError(_('Error en action assign. No stock'))


        for line in self.line_ids:
            product_id = line.product_id

            for op in pick.pack_operation_product_ids:

                if op.product_id == product_id:
                    line.pack_operation_product_ids = [(4, op.id)]
                    # line.picking_id = pick.id
                    line.location_id = op.location_id

                    #line.pack_operation_product_id = op.id
                    # line.state='new'
            for move in pick.move_lines:
                if move.product_id == product_id:

                    line.move_line_ids = [(4, move.id)]
                    move.location_id = line.location_id
        for op in pick.pack_operation_product_ids:
            op.qty_done = op.product_qty

        res = pick.do_transfer()
        if res:
            for line in self.line_ids:
                line.state = "open"
        return True

    def do_return_pick2(self, type='return', force=False):

        return self.do_return(type=type)

        if force:
            return self.do_return()

            # do_return = True
            # for line in self.line_ids:
            #     if line.request_type!="to_return":
            #         do_return=False
            #
            # if do_return:
            #     return self.do_return()
            #
            #
            # view = self.env.ref('request.view_immediate_transfer')
            # wiz = self.env['request.immediate.transfer'].create({'request_id': self.id})
            # return {
            #     'name': _('Request transfer?'),
            #     'type': 'ir.actions.act_window',
            #     'view_type': 'form',
            #     'view_mode': 'form',
            #     'res_model': 'request.immediate.transfer',
            #     'views': [(view.id, 'form')],
            #     'view_id': view.id,
            #     'target': 'new',
            #     'res_id': wiz.id,
            #     'context': self.env.context,
            # }

    def do_return_pick(self, type='return'):
        wh = self.env['stock.warehouse'].browse([1])
        request_picking_type = wh.request_type_id
        return_picking_type = request_picking_type.return_picking_type_id
        expend_picking_type = wh.expend_type_id
        if type == 'return':
            picking_type_id = return_picking_type
            location_dest_id = False
        elif type == 'scrap':
            picking_type_id = expend_picking_type
            location_dest_id = expend_picking_type.default_location_dest_id.id

        domain = [('request_material_id', '=', self.id), ('picking_type_id', '=', picking_type_id.id)]
        pick = self.env['stock.picking'].search(domain, limit=1)

        if not pick:
            raise ValidationError(_('Pick Error'))

        for line in self.line_ids:
            for op in pick.pack_operation_product_ids:
                if op.product_id == line.product_id:
                    line.pack_operation_product_ids = [(4, op.id)]
                    qty_done = line.returned_qty if type == 'return' else line.expended_qty
                    op.qty_done = qty_done
                    op.location_dest_id = location_dest_id or line.location_id
            for move in pick.move_lines:
                if move.product_id == line.product_id:
                    line.move_line_ids = [(4, move.id)]



        res = pick.do_transfer()
        return
        return {
            'name': _('Request Material'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'request.material.line',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'context': self.env.context}


class RequestMaterialLine(models.Model):
    _name = "request.material.line"
    _description = 'Request Material'
    _order = 'request_date, id'

    def _get_request_type(self):
        return self.product_id and self.product_id.request_type or 'to_return'

    @api.multi
    @api.depends('returned_qty', 'requested_qty')
    def _get_expended_qty(self):
        self.expended_qty = self.requested_qty - self.returned_qty

    def _get_returned_qty(self):
        if self.request_type == 'tool':
            return self.requested_qty
        else:
            return 0.00

    def get_color(self):

        for line in self:
            if line.state == "open":
                line.color = 2
            elif line.state == "done":
                line.color = 1
            elif line.state == "new":
                line.color = 3
            else:
                line.color = 0

    request_material_id = fields.Many2one('request.material', required=True)
    user_id = fields.Many2one(related='request_material_id.user_id')
    selected = fields.Boolean("Selected")
    product_id = fields.Many2one('product.product', required=True)
    name = fields.Char(related='product_id.name')
    default_code = fields.Char(related='product_id.default_code')
    location_id = fields.Many2one('stock.location')
    location_name = fields.Char(related='location_id.name')
    requested_qty = fields.Float(string="Requested quantity", default=1.00)
    by_us = fields.Boolean('In use by us', help="if check, we use the material, else partners use the material",
                           default=True)
    partner_id = fields.Many2one('res.partner')
    request_type = fields.Selection([('to_scrap', 'Scrap'),
                                     ('to_return', 'To return'),
                                     ('tool', 'Tool')
                                     ], string='To scrap',
                                    default=_get_request_type,
                                    help="Scrap: Material will be moved to scrap location, \n"
                                         "To return: Material must be returned (Quantities)\n"
                                         "Too : Must be returned always")
    request_date = fields.Datetime(string="Request date", default=fields.Datetime.now)
    uom_id = fields.Many2one(related="product_id.uom_id")
    location_dest_id = fields.Many2one(related='request_material_id.location_dest_id')
    outbuilding = fields.Char(related='location_dest_id.name', string="Outbuilding")
    notes = fields.Text(
        'Notes', translate=True,
        help="Comments about this request")
    state = fields.Selection([('new', 'New'),
                              ('open', 'Delivered'),
                              ('done', 'Returned'),
                              ('closed', 'Closed')
                              ],
                             string='Status', required=True, readonly=True,
                             copy=False, default='new')
    color = fields.Integer('Kanban State Color Index', compute="get_color")

    expended_qty = fields.Float('Expended quantity', compute=_get_expended_qty)
    returned_qty = fields.Float('Returned quantity', default=_get_returned_qty)

    picking_ids = fields.One2many(related='request_material_id.picking_ids')
    move_line_ids = fields.One2many('stock.move', 'request_material_line_id')
    pack_operation_product_ids = fields.One2many('stock.pack.operation','request_material_line_id')
    active = fields.Boolean('Active', default=True)

    # @api.onchange('requested_qty', 'returned_qty')
    # def onchange_qties(self):
    #     if self.request_type != 'to_scrap' and self.state=='new':
    #         self.returned_qty = self.requested_qty
    #
    #     self.expended_qty = self.requested_qty - self.returned_qty

    @api.onchange('product_id')
    def onchange_product_id(self):

        if self.product_id:
            self.request_type = self.product_id.product_tmpl_id.request_type

    def return_line(self):
        return

    @api.multi
    def _get_action(self, action_xmlid):

        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['res_id'] = self.id
            action['display_name'] = self.display_name
        return action

    @api.multi
    def get_action_request_material_form(self):
        return self._get_action('request_material.action_request_material_form')

    @api.multi
    def get_next_action(self):

        if self.state == 'new':

            self.selected = True
            pick = self.request_material_id.create_pick(type='request')
            self.request_material_id.do_requested_pick()

        elif self.state == 'open':
            self.check_return_picks()

        elif self.state == 'done':
            self.active = False

        return {
            'name': _('Request Material'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'request.material.line',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'context': self.env.context}

    def check_return_picks(self):

        print "returned qty : %s. Expended_qty: %s" % (self.returned_qty, self.expended_qty)
        if self.returned_qty > 0.00:
            return_pick = self.request_material_id.create_pick(type='return')
            self.picking_ids = [(4,return_pick.id)]
            if not return_pick.action_confirm():
                raise ValidationError(_('Error en action confirm'))
            if not return_pick.action_assign():
                raise ValidationError(_('Error en action assign. No stock'))
            self.request_material_id.do_return_pick(type='return')

        if self.expended_qty > 0.00:
            return_pick = self.request_material_id.create_pick(type='scrap')
            self.picking_ids = [(4, return_pick.id)]
            if not return_pick.action_confirm():
                raise ValidationError(_('Error en action confirm'))
            if not return_pick.action_assign():
                raise ValidationError(_('Error en action assign. No stock'))
            self.request_material_id.do_return_pick(type='scrap')
        self.state = "done"
        return True

    @api.multi
    def change_qty(self):
        view = self.env.ref('request_material.view_request_change_qties')
        wiz = self.env['request.change.qties'].create({'request_line_id': self.id})
        return {
            'name': _('Request change quantity?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'request.change.qties',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }


class RequestChangeQtWz(models.TransientModel):

    _name = "request.change.qties"
    _description = 'Request change quantities'

    request_line_id = fields.Many2one('request.material.line')
    requested_qty = fields.Float(related='request_line_id.requested_qty')
    returned_qty = fields.Float(related='request_line_id.returned_qty')

    product_id = fields.Many2one(related='request_line_id.product_id', readonly=1)
    location_id = fields.Char(related='request_line_id.location_id.name', readonly=1)
    location_dest_id = fields.Char(related='request_line_id.request_material_id.location_dest_id.name', readonly=1)
    uom_id = fields.Many2one(related="product_id.uom_id")
    state = fields.Selection(related='request_line_id.state')

    @api.onchange('requested_qty')
    def onchange_qties(self):
        if self.request_line_id.request_type != 'to_scrap' and self.state == 'new':
            self.returned_qty = self.requested_qty

    @api.multi
    def apply_changes(self):
        if self.returned_qty > self.requested_qty:
            raise ValidationError(_('Error. You can not return more quatity than delivered'))

        return {
            'name': _('Request Material'),
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'request.material.line',
            'type': 'ir.actions.act_window',
            'context': self.env.context}


class requestImmediateTransfer(models.TransientModel):
    _name = 'request.immediate.transfer'
    _description = 'Request transfer'

    pick_id = fields.Many2one('request.material')

    @api.model
    def default_get(self, fields):
        res = super(requestImmediateTransfer, self).default_get(fields)
        if not res.get('request_id') and self._context.get('active_id'):
            res['request_id'] = self._context['active_id']
        return res

    @api.multi
    def process(self):
        self.ensure_one()

        return self.pick_id.do_return(force=True)
