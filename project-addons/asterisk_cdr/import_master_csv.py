
# -*- coding: utf-8 -*-
import sys
import xmlrpclib
import socket
import traceback
import re
import base64
import time
import csv
import datetime as datetime
import paramiko

class BuImport:
    """
    Se pasan las listas de materiales a packs
    """

    def __init__(self):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = "localhost"
        self.port = 8069
        self.dbname = 'ASTERISK'
        self.user_name = 'admin'
        self.user_passwd = 'admin'
        self.user_id = 0

        #
        # Conectamos con OpenERP
        #
        login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
        self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
        self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

        #
        # Fichero Log de Excepciones
        #

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del método create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'create', data, context)

            if isinstance(res, list):
                res = res[0]

            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))

    def search(self, model, query, context={}):
        """
        Wrapper del método search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, context)
            return ids
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))

    def read(self, model, ids, fields, context={}):
        """
        Wrapper del método read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'read', ids, fields, context)
            return data
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))

    def write(self, model, ids, field_values, context={}):
        """
        Wrapper del método write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))

    def unlink(self, model, ids, context={}):
        """
        Wrapper del método unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del método default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, ids, context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, method, ids, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))


    def get_cdr_file(self):
        now_ = datetime.datetime.now()
        woy = now_.isocalendar()[1]
        year = now_.isocalendar()[0]
        extension = ".csv"
        file_name = "Master01"
        remote_path = "/var/log/asterisk/cdr-csv/"
        local_path = "asteriskcdr_files/in/"

        new_file_name= "%s_%s_%s%s"%(file_name, year, woy, extension)
        old_file_name = "%s%s"%(file_name, extension)
        old_path = "%s%s"%(remote_path, old_file_name)
        new_path="%s%s"%(remote_path, new_file_name)
        local_file = "%s%s" % (local_path, new_file_name)
        remote_host = "192.168.0.10"
        port =22
        usuario ="root"
        password = "comunitaopen(ol"

        datos = dict (hostname=remote_host, port=port,username=usuario, password=password)
        ssh_client= paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(**datos)
        sftp = ssh_client.open_sftp()  # Crea un objeto SFTPClient()
        print "OK AQUI"
        try:
            import ipdb; ipdb.set_trace()
            res = sftp.rename(old_path, new_path)
            new1 = sftp.file(old_path, mode='w')
            new1.close
            res = sftp.get(new_path, local_file)
            print "Copiado %s a %s "%(new_path, local_path)
            return new_file_name, local_path



        except Exception, ex:

            print "Error al sftp", (ex)
            sys.exit()








    def process_data(self, path, file):

        def check_phone(phone_name):
            phone_id = self.search('asterisk.phone', [('phone_number', '=', phone_name)])
            phone_id = phone_id and phone_id[0]
            if not phone_id:
                val = {
                    'name': phone_name,
                    'phone_number': phone_name
                }
                phone_id = self.create('asterisk.phone', val)
            return phone_id

        def check_sip(sip_name):
            path, sip_number = sip_name.split('/')

            sip_id = self.search('asterisksip.channel', [('sip_number','=',sip_number)])
            sip_id = sip_id and sip_id[0]
            if not sip_id:
                val = {
                    'name': "SIP/%s"%sip_number,
                    'sip_number': sip_number,
                    'sip_extension': sip_number
                }
                sip_id = self.create('asterisksip.channel', val)
            return sip_id

        def check_id(call_id):
            sip_id = self.search('asteriskcdr.line', [('call_id', '=', call_id)])
            sip_id = sip_id and sip_id[0]
            if not sip_id:
                val = {
                    'call_id': call_id
                }
                sip_id = self.create('asteriskcdr.line', val)
            return sip_id


        def saca_sip (cid):
            #Local/501@from-queue-0000024e;2","SIP/501-0000026e"

            if cid.find(';')==-1:
                cid = '%s;1'%cid

            path, orden = cid.split(';')
            orden = orden or 1
            cid = path.replace("from-queue", "from_queue")
            cid, id = cid.split('-')
            if cid.find('@')==-1:
                cid = '%s@' % cid
            sip, path1 = cid.split('@')
            #devuelve
            # id de llamada
            # orden de llamada
            # sip SIP/numero
            #path completo para ordenar
            sip = check_sip(sip)
            id = check_id(id)
            print id, path, sip, orden
            return id, orden, sip, path

        print "Empezamos"
        new_file = "%s%s"%(path, file)
        move_path = "asteriskcdr_files/out/"




        """
        Importa la bbdd
        """

        file_id = self.search('asteriskcdr.file', [('name', '=', file)])
        file_id = file_id and file_id[0]
        if not file_id:
            val = {
                'name': file,
            }
            file_id = self.create('asteriskcdr.file', val)
        print "\n\nasteriskcdr.file : %s con id: %s\n\n" % (file, file_id)


        with open(new_file, 'rb') as call_line:
            prodreader = csv.reader(call_line, delimiter=',', quotechar='"')


            category = []
            # defiuno el priemr inventario
            inventory_id = 1

            #cre los tags para los productos
            a=0
            for row in prodreader:

                print "Fila:%s"%a


                call_from = row[1]
                call_to = row[2]
                call_type_ = row[3]# ext-local, ext-queues, from-internal
                name = row[4]
                incoming_cid=row[5]
                outgoing_cid= row[6]
                call_to_sip = row[7]
                call_type_2 = row[8]
                aux1=row[8] #"SIP/502,,trM(auto-blkvm)"
                call_date = row[9]
                call_wait = row[10]
                call_to_date = row[11]
                call_duration_queue = row[12]
                call_duration = row[13]
                call_result = row[14] # ANSWERED NO ANSWER
                if call_type_=="ext-local":
                    call_type = 'INC'
                elif call_type_ == "ext-queues":
                    call_type ="QUE"
                elif call_type_=="from-internal":
                    call_type="OUT"

                else:
                    call_type="INT"
                call_text = "%s\n%s\n%s\n%s"%(name, call_date, incoming_cid, outgoing_cid)
                call_id= orden= call_from_sip= call_to_sip= path= from_number= to_number= sip_id= call_queue= False

                a +=1

                if call_result=='ANSWERED' or True:

                    from_number= check_phone(call_from)
                    to_number= check_phone(call_to)
                    if call_type =="QUE":
                        call_id, orden, call_from_sip, path = saca_sip(incoming_cid)
                        call_to_id, a2, call_to_sip, path = saca_sip(outgoing_cid)

                    elif call_type =="INC":
                        call_id, orden, call_from_sip, path = saca_sip(incoming_cid)
                        call_to_id, a2, call_to_sip, new_path = saca_sip(outgoing_cid)
                    else:
                        call_id, orden, call_from_sip, path = saca_sip(incoming_cid)
                        call_to_id, a2, call_to_sip, new_path = saca_sip(outgoing_cid)

                    name = '%s / %s'%(name, call_id)







                    call_result = 'A' if call_result=="ANSWERED" else "N"
                    val_line = {
                        'file_id': file_id,
                        'call_name': name,
                        'call_from': from_number,
                        'call_to':to_number,
                        'call_date': call_date,
                        'call_from_sip': call_from_sip,
                        'call_to_sip': call_to_sip,
                        'call_duration': call_duration,
                        'call_type': call_type,
                        'call_queue': call_queue,
                        'call_text': call_text,
                        'call_path': path,
                        'call_result': call_result,
                        'call_to_id': call_to_id
                    }
                    print val_line
                    sip_id = self.write('asteriskcdr.line', [call_id], val_line)




                #
                #     row = row[0]
                #     data_ids = self.search('ir.model.data', [('name', '=', row)])
                #     if not data_ids:
                #         print(row)
                #         lines[2] += 1
                #         continue
                #     product_id = self.read('ir.model.data', data_ids, ['res_id'])[0]['res_id']
                #     bom_id = self.read('product.product', product_id, ['bom_ids'])['bom_ids']
                #     if not bom_id:
                #         print(row)
                #         lines[3] += 1
                #         continue
                #     bom_id = bom_id[0]
                #     for line_id in self.read('mrp.bom', bom_id, ['bom_line_ids'])['bom_line_ids']:
                #         line = self.read('mrp.bom.line', line_id, ['product_id', 'product_qty'])
                #         self.create('product.pack.line', {'parent_product_id': product_id, 'product_id': line['product_id'][0], 'quantity': line['product_qty']})
                #         self.unlink('mrp.bom.line', line_id)
                #     self.unlink('mrp.bom', [bom_id])
                #     lines[1] += 1
                #     self.write('product.product', product_id, {'type': 'service', 'stock_depends': True})
                # print('lineas totales leidos: %s, productos encontrados: %s, productos no encontrados: %s, productos sin materiales: %s' % (lines[0], lines[1], lines[2], lines[3]))

            return True


if __name__ == "__main__":

   ENGINE = BuImport()

   now_ = datetime.datetime.now()
   woy = now_.isocalendar()[1]
   year = now_.isocalendar()[0]
   extension = ".csv"
   file_name = "Master01"
   local_path = "asteriskcdr_files/in/"

   new_file_name = "%s_%s_%s%s" % (file_name, year, woy, extension)

   ENGINE.process_data(local_path, new_file_name)
