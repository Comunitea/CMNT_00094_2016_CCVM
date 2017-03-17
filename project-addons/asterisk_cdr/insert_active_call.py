#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xmlrpclib
import socket
# import traceback
# import re
# import base64
# import time
# import csv
# import datetime as datetime
# import paramiko
import os


class BuImport:
    """
    Se pasan las listas de materiales a packs
    """

    def __init__(self):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """

        # -------------------------------------------------------------------------
        # --- WRAPPER XMLRPC OPENERP ----------------------------------------------
        # -------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = "192.168.0.112"
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

    def insert_call(self, op, call_number, channel, call_id, hangupcause, connectedline, dstring, cdr_channel,
                    dest_channel, src, dst, lastapp, lastdata, start, answer, end, duration, billsec, sequence):

        val = {'call_number': call_number,
               'call_id': call_id,
               'call_channel': channel,
               'call_hangupcause': hangupcause,
               'call_connectedline': connectedline,
               'call_dstring': dstring,
               'call_cdrchannel': channel,
               'call_cdrdest_channel': dest_channel,
               'call_cdrseconds': billsec,
               'call_src': src,
               'call_dst': dst,
               'call_lastapp': lastapp,
               'call_lastdata': lastdata,
               'call_start': start,
               'call_answer': answer,
               'call_end': end,
               'call_duration': duration,
               'call_bilsec': billsec,
               'sequence': sequence}

        if op == "1":
            os.system('echo """\n\nCreando ...\n """>> /log/log.txt')
            call_id = self.create('asterisk.activecall', val)

        elif op == "0" and call_number:
            os.system('echo """\n\nActualizando ...\n""" >> /log/log.txt')

        call_id = self.execute('asterisk.activecall', 'hangup_call', [], val)

        os.system('echo """\n\n echo Resultado : >>> %s ...\n""" >> /log/log.txt' % call_id)

        return call_id


if __name__ == "__main__":

    os.system('echo """\n\n VARIABLES RECIBIDAS (%s) \n %s""" >> /log/log.txt' % (len(sys.argv), sys.argv))
    if len(sys.argv) < 3:
        print u"Uso: %s <dbname> <user> <password>" % sys.argv[0]

    else:
        ENGINE = BuImport()
        os.system('echo """\n Base de Datos OK""" >> /log/log.txt')

        py, op, call_number, channel, call_id, hangupcause, connectedline, dstring, cdr_channel, dest_channel, src, dst, lastapp, lastdata, start, answer, end, duration, billsec, sequence = sys.argv
        os.system('echo """\n Variables Importadas OK""" >> /log/log.txt')
    # if (op=="1" and call_number!="") or op=="0" or True:
    sys.exit(ENGINE.insert_call(op, call_number, channel, call_id, hangupcause, connectedline, dstring, cdr_channel,
                                dest_channel, src, dst, lastapp, lastdata, start, answer, end, duration, billsec,
                                sequence))
    # print ENGINE.insert_call(sys.argv[1],sys.argv[2],sys.argv[3])


