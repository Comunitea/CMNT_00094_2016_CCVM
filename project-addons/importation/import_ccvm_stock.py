
# -*- coding: utf-8 -*-
import sys
import xmlrpclib
import socket
import traceback
import re
import base64
import time
import csv

class BuImport:
    """
    Se pasan las listas de materiales a packs
    """

    def __init__(self, dbname, user, passwd):
        """
        Inicializar las opciones por defecto y conectar con OpenERP
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = "localhost"
        self.port = 8069
        self.dbname = dbname
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

    def process_data(self):
        """
        Importa la bbdd
        """
        try:
            with open('CCVM_PRODUCT.csv', 'rb') as prodlist:
                prodreader = csv.reader(prodlist, delimiter=',', quotechar='"')


                category = []
                # defiuno el priemr inventario
                inventory_id = 1

                #cre los tags para los productos
                a=0

                for row in prodreader:
                    a +=1
                    print row[0], row[2]
                    if not row[0]=='code':




                        code = row[9].replace(" ","")
                        print code
                        almacen =  row[4]
                        location_name = row[3]
                        location_name = location_name.replace("  ", " ")
                        location_name = location_name.replace("  ", " ")
                        location_name = location_name.replace("  ", " ")




                        categ_name = row[5].replace("/", "-")

                        try:
                            stock_inicial = int(row[2].replace(" ",""))
                        except:
                            stock_inicial = 0.00

                        try:
                            price = row[16].replace(" ", "")
                            price = price.replace(",",".")
                            price = float(price)
                        except:
                            price = 0.00

                        categ_id = self.search('product.category', [('name', '=', categ_name)])
                        if not categ_id:
                            val_categ = {
                                'name':categ_name,
                                'parent_id': 1
                            }
                            categ_id = self.create('product.category', val_categ)
                            print "creo categoria: %s con id: %s"%(categ_name, categ_id)

                        try:
                            categ_id = categ_id[0]
                        except:
                            pass

                        print "Ok categoria %s"%categ_name

                        #Almacen padre

                        stock_location = {
                            'usage' : 'internal',
                            'name': almacen,
                            'location_id': 15
                        }
                        #existe stock_ location
                        parent_location_id = self.search('stock.location', [('name','=', almacen)])
                        if not parent_location_id:
                            parent_location_id = self.create('stock.location', stock_location)
                            print "Creo el almacen padre: %s con id: %s"%(almacen, parent_location_id)
                        try:
                            parent_location_id = parent_location_id[0]
                        except:
                            pass

                        #Creo la ubicacion dentro de la anterior
                        val_stock_location = {
                            'usage': 'internal',
                            'name': location_name,
                            'location_id': parent_location_id
                        }
                        # existe stock_ location
                        product_location_id = self.search('stock.location', [('name', '=', location_name)])
                        if not product_location_id:

                            product_location_id = self.create('stock.location', val_stock_location)
                            print "Creo el almacen: %s con id: %s" % (location_name, product_location_id)
                        print "OK Location"
                        try:
                            product_location_id = product_location_id[0]
                        except:
                            pass


                        product_name = row[1]
                        val = {
                            'default_code': code,
                            'name': product_name,
                            'categ_id': categ_id,
                            'type': 'product',
                            'standard_price': price,
                            'description_purchase': "%s\n%s"%(row[6], row[8])
                        }
                        #creo el producto
                        product_id = self.search('product.product', [('default_code', '=', code)])
                        if not product_id:
                            product_id = self.create('product.product', val)

                        print "OK product"
                        try:
                            product_id = product_id[0]
                        except:
                            pass


                        print "Sotock Inicial %s" %stock_inicial
                        #creo un inventario nuevo
                        #supongo inventario inciial 1

                        #def write(self, model, ids, field_values, context={})
                        #creo una stock_inventory_line
                        if stock_inicial>0:
                            #import ipdb; ipdb.set_trace()
                            val_line ={'inventory_id': 1,
                                'product_id': product_id,
                                'partner_id':1,
                                'product_qty': stock_inicial,
                                'company_id': 1,
                                'location_id': product_location_id}
                            print "line a de inven %s" %val_line
                            stock_inv_line =self.search('stock.inventory.line', [('location_id', '=', product_location_id), ('inventory_id','=',1), ('product_id', '=', product_id)])
                            if not stock_inv_line:
                                new_stock_inventory_line = self.create('stock.inventory.line', val_line)
                            #ahora escribo
                                ids = [(4, [new_stock_inventory_line])]
                                print ids
                                res = self.write('stock.inventory',1, {'line_ids': ids})


                        print "ok Stock Inv Line"










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

        except Exception, ex:
            print "Error al conectarse a las bbdd: ", (ex)
            sys.exit()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password>" % sys.argv[0]
    else:
        ENGINE = BuImport(sys.argv[1], sys.argv[2], sys.argv[3])

        ENGINE.process_data()
