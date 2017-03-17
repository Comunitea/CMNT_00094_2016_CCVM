# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, _
from odoo import tools
from odoo.exceptions import ValidationError
import paramiko
import datetime


class AsteriskPhones(models.Model):

    _name = "asterisk.phone"

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner')
    phone_name = fields.Char("Phone name", required=True)
    phone_number = fields.Char("Phone number", required=True)

    @api.onchange('phone_name', 'partner_id')
    def get_name(self):
        self.name = u'%s (%s)'%(self.partner_id.name, self.phone_name or self.phone_number)


class AsteriskCDRFile(models.Model):

    _name = "asteriskcdr.file"

    name = fields.Char('File Name')
    date_created = fields.Datetime('File created date', default = datetime.datetime.now())
    date_imported = fields.Datetime('File imported date', default = datetime.datetime.now())

class SipChannels(models.Model):
    _name = "asterisksip.channel"

    name = fields.Char("Sip name")
    sip_number = fields.Char("Phone Number")
    sip_extension = fields.Boolean("Internal Extension")
    partner_id = fields.Many2one("res.partner")


class AsteriskCDRLine(models.Model):

    _name = "asteriskcdr.line"

    name = fields.Char("Line Name")
    file_id = fields.Many2one('asteriskcdr.file', string="File")
    call_id = fields.Char('Call id')
    call_from = fields.Many2one('asterisk.phone')
    call_to = fields.Many2one('asterisk.phone')
    call_date = fields.Datetime('Call date')
    call_to_sip = fields.Many2one("asterisksip.channel", string="From Sip Channel")
    call_to_extension = fields.Many2one("asterisksip.channel", string ="To Sip Channel")
    call_duration = fields.Float("Duration")
    call_type = fields.Selection([('INC', _('Incoming calls')), ('QUE', _('Queue calls')), ('OUT', _('Outgoing calls')), ('INT', _('Internal calls'))])
    call_result = fields.Selection([('A',_('ANSWERED')), ('N',_('NO ANSWER'))])
    call_to_id = fields.Many2one("asteriskcdr.line")
    call_text = fields.Text('Text')
    call_path = fields.Char("Call path")



class AsteriskActiveCalls(models.Model):
    _name ="asterisk.activecall"

    @api.multi
    def get_duration(self):
        for call in self:
            create_date =  datetime.datetime.strptime(call.create_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            now = datetime.datetime.now()
            seconds = (now-create_date).seconds
            call.wait_time = seconds


    call_number = fields.Char('Call Number')
    call_id = fields.Char("Call ID")
    active = fields.Boolean('Active', default=True)
    asterisk_phone_id = fields.Many2one('asterisk.phone')
    partner_id = fields.Many2one(related="asterisk_phone_id.partner_id")

    state = fields.Selection([('R', _('Ringing')), ('N', _('Talking')), ('A', _('Answered')), ('NA', _('Not answered'))], default="R")
    wait_time= fields.Float("Duration", compute="get_duration")
    talk_time = fields.Float("Duration")

    asterisk_dest_phone_id = fields.Many2one('asterisk.phone')
    dest_partner_id = fields.Many2one(related="asterisk_dest_phone_id.partner_id")
    description = fields.Text("Description")
    time_unit = fields.Selection([('S', _('Seconds')), ('M', _('Minutes'))], default="S")
    call_channel = fields.Char("Channel")
    call_cdrseconds = fields.Float("Duration")
    call_hangupcause = fields.Integer("Hangup cause")
    call_connectedline=fields.Char("Destination Line")
    call_dstring = fields.Char("Sip dest number")
    call_cdrchannel= fields.Char("CDR channel")
    call_cdrdest_channel = fields.Char("CDR Dest. channel")
    call_answer = fields.Char("Time Answer")
    call_start = fields.Char("Time Start")
    call_end = fields.Char("Time End")
    call_bilsec = fields.Float('CDR Talk Time')
    call_context = fields.Char("CDR Context")
    call_duration = fields.Float("CDR Call Time")
    call_lastapp = fields.Char("Channel From ...")
    call_lastdata = fields.Char("Channel To ...")
    call_src=fields.Char("CDR Phone Source")
    call_dst = fields.Char("CDR Phone Destination")
    sequence= fields.Char("CDR Phone Destination")
    from_e = fields.Char("from_e")
    #
    # val = {
    #     'call_number': call_number,
    #     'call_id': call_id,
    #     'call_cdrchannel': channel,
    #     'call_hangupcause': hangupcause,
    #     'call_connectedline': connectedline,
    #     'call_dstring': dstring,
    #     'call_cdrchannel': channel,
    #     'call_cdrdest_channel': dest_channel,
    #     'call_cdrseconds': seconds
    # }

    def get_next_action(self):
        return True


    def refresh(self, vals):
        return True

    @api.model
    def create(self, vals):
        print "--------------------------\nValores originasles %s\n"%vals

        call_channel = vals['call_channel']#, vals.get('call_cdrchannel', False))
        print "\n\nCreando llamada para el canal %s con vals \n %s" % (call_channel, vals)
        domain = [('call_channel', '=', vals['call_channel'])]
        ids = self.search(domain)
        #ids= False

        from_e = vals['from_e']

        call_context= vals['call_context']
        dest_phone_number = vals.get('call_dst', False)
        phone_number = vals.get('call_src', False)
        if call_context == "from-trunk":
            #Viene de una col.
            #La creo pq  la ncesito consultar despues
            vals['call_connectedline'] == ''
            vals['description'] = "Llamada exterior. Entra en cola de llamada"

        elif call_context == "from-queue":
            ##Jo
            vals['description'] = "Llamada desde cola a extension"

        elif call_context == "ext-local":
            #Es una llamada interna desde cola
            dest_phone_number = vals['call_dst']
            vals['description'] = "Respuesta de cola de llamada"



        elif call_context == "from-internal":
            if from_e == 'macro-auto-blkvm':
                # Llamada respondida a una cola entonces
                des21=21

                print "########################### Aqui"
                vals['description'] = "Llamada establecida cola-extension"
                domain = [('call_cdrchannel', '=', vals['call_cdrchannel'])]
                channel = self.search(domain, limit=1, order = 'id desc')
                if channel:
                    vals['call_dst']= vals['call_src']
                    vals['call_src'] = channel.call_src
                    dest_phone_number = vals.get('call_dst', False)
                    phone_number = vals.get('call_src', False)


            if from_e =="macro-dial-one":
                vals['description'] = "Llamada transferida"

        domain = [('phone_number','=', phone_number)]
        asterisk_phone_id = self.env['asterisk.phone'].search(domain, limit=1)
        vals['asterisk_phone_id']= asterisk_phone_id and asterisk_phone_id[0].id

        domain = [('phone_number', '=', dest_phone_number)]
        asterisk_dest_phone_id = self.env['asterisk.phone'].search(domain, limit=1)
        vals['asterisk_dest_phone_id'] = asterisk_dest_phone_id and asterisk_dest_phone_id[0].id

        if ids:

            ids.refresh(vals)
        else:
            ids = super(AsteriskActiveCalls, self).create(vals)

            print "                 Creada con id [%s]"%ids

        return ids


    def refresh(self, vals):


        print "                 Ya hay una llamada------------------------ACtualizo"
        #import ipdb; ipdb.set_trace()

        call_cdrchannel = self.call_cdrchannel
        if call_cdrchannel:
            domain = [('call_channel', '=', call_cdrchannel)]
            ids = self.search(domain, limit=1, order="id desc")
            write_vals = {
                'call_cdrseconds': vals['call_cdrseconds'],
                #'call_answer': vals['call_answer'],
                #'call_start': vals['call_start'],
                #'call_answer': vals['call_answer'],
                'call_duration': vals['call_duration'],
                'call_hangupcause': vals['call_hangupcause'],
                'call_bilsec': vals['call_bilsec'],
                'call_cdrdest_channel': vals['call_cdrdest_channel'],
                'call_end': datetime.datetime.now()

            }
            ids.write(write_vals)
            print "---------------------------------ACtualizada"



    @api.multi
    def hangup_call(self):
        vals = self._context.copy()
        call_channel = vals['call_channel']
        call_cdrchannel = self._context.get('call_cdrchannel', False)


        #print "\n\nColgando llamada %s" % call_cdrchannel
        #print "Colgando llamada %s"%self._context
        vals = self._context.copy()
        print "\n\nColgando llamada %s" % call_channel
        print "\n\n CON VALS \n%s"%vals
        write_vals = {
            'call_cdrseconds': vals['call_cdrseconds'],
            'call_answer': vals['call_answer'],
            'call_start': vals['call_start'],
            'call_answer': vals['call_answer'],
            'call_duration': vals['call_duration'],
            'call_hangupcause': vals['call_hangupcause'],
            'call_bilsec': vals['call_bilsec'],
            'call_cdrdest_channel': vals['call_cdrdest_channel'],
            'call_end': datetime.datetime.now()


        }

        res = False
        if call_channel:

            domain =[('call_channel', '=', call_channel)]
            ids = self.search(domain, limit=1, order ="id desc")
            #De momento quedan todas en activo para verlas
            # vals['active']=False
            call_hangupcause = vals.get('call_hangupcause',0)
            if call_hangupcause=='16':

                write_vals['state'] ='A'
            elif call_hangupcause == '26':
                write_vals['state'] = 'NA'
            else:
                write_vals['state'] ='NA'

            res = ids.write(write_vals)
            if res:
                print "Colgada llamada %s"%call_channel
                #ahora cuelgo las que tengan su cdr_channel()
                if ids.call_context=='from-trunk':
                    domain = [('call_cdrchannel', '=', ids.call_cdrchannel)]
                    ids = self.search(domain)
                    ids.write ({'state': write_vals['state']})
                res=True
        else:
            print "\n\n No la encuentro"
        return res

    @api.multi
    def write(self, vals):
        print vals

        if vals.get('active', False):
            create_date = datetime.datetime.strptime(self.create_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            now = datetime.datetime.now()
            seconds = (now - create_date).seconds
            talk_time = seconds
            vals['talk_time'] = talk_time
        return super(AsteriskActiveCalls, self).write(vals)

