#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2020, lgonzalezp'
__docformat__ = 'restructuredtext en'

import sys
import os
import subprocess
import re
import time
from calibre_plugins.biblioteca_EPL.config import prefs
from calibre.ebooks.metadata.meta import get_metadata

try:
    import PyQt5
    from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QWidget
    from PyQt5.QtWidgets import QLabel, QMessageBox, QLineEdit, QToolTip, QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView
    from PyQt5.QtGui import QPixmap, QIcon, QFont
    from PyQt5.QtCore import Qt
except:
    import PyQt6
    from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout, QWidget
    from PyQt6.QtWidgets import QLabel, QMessageBox, QLineEdit, QToolTip, QTableWidget, QAbstractItemView, QTableWidgetItem, QHeaderView
    from PyQt6.QtWidgets import QTableView
    from PyQt6.QtGui import QPixmap, QIcon, QFont

iswindows = sys.platform.startswith('win')
isosx = sys.platform.startswith('darwin')
iscygwin = sys.platform.startswith('cygwin')
islinux = not (iswindows or isosx or iscygwin)

EPLID_raros = {
    'Fuentes, Juan F. & Parra Lopez, Emilio La - Historia universal del siglo XX (r1.4).epub': '383',
    'Hugo, Victor - El Hombre que rie [Tomo I] (r1.3).epub': '2306',
    'Vian, Boris - El lobo hombre y otros relatos (r1.1 Hechadelluvia).epub': '5903',
    'Munoz Seca, Pedro y Garcia Alvarez, Enrique - La conferencia de Algeciras (r1.0 jandepora).epub': '7725',
    'Sigurdardottir, Yrsa - [Zora y Matthew 3] Ceniza (r1.0).epub': '4481',
    'Starhawk - La danza espiral (r1.0).epub': '4150',
    'Zweig, Stefan - Tres poetas de sus vidas (r1.0).epub': '1859',
    'Prineas, Sarah - [El ladron mago 02] Perdido (r1.0 moower).epub': '6569',
    'Baecque, Antoine de - Teoria y critica del cine (r1.0 EPL).epub': '4522',
    'Barcelo, Miquel i Romero, Pedro Jorge - Testimoni de Narom (r1.0).epub': '6280',
    'Dostoievski, Fiodor - El eterno marido (r1.0).epub': '4914',
    'Hoces Garcia-Galan, Alfredo de - Fuckowski, Memorias de un ingeniero (r1.1).epub': '4577',
    'Nario, Hugo - Bepo. Vida secreta de un linyera (r1.1 helike).epub': '5870',
    'Ratzinger, Joseph - La infancia de Jesus (r1.1).epub': '665',
    'Anonimo - La saga de Kormak (r1.1 EPL).epub': '5062',
    'Borges, J. L. & Bioy Casares, A. - [HBD 4] Nuevos cuentos de Bustos Domecq (r1.0 jugaor).epub': '3197',
    'Ende, Michael - [Jim Boton y Lucas el maquinista 2] Jim Boton y los trece salvajes (r1.0 Ishamael).epub': '3385',
    'Palahniuk, Chuck - Rant. La vida de un asesino (r1.0).epub': '1806',
    'Shinya, Hiromi - La enzima prodigiosa (r1.1 Sheena).epub': '3237',
    'VVAA - Premio UPC 2000 - Novela corta de Ciencia Ficción (r1.2).epub': '2444',
    'Scarrow, Simon - [Serie Aguila - 9] - Gladiador (r1.1 Escipion).epub': '3580',
    'VVAA - Premio UPC 1996 - Novela corta de Ciencia Ficción (r1.1).epub': '2443',
    'Pizarnik, Alejandra - Extraccion de la piedra de locura (r1.0 Moro).epub': '3962',
    'Gallego, Eduardo i Sánchez, Guillem - Naufrags en la nit (r1.0).epub': '2631',
    'Bermudez Ortiz, Alberto - Zoombi (r1.2 capitancebolleta).epub': '1743',
    'Perry, Anne - [Monk 12] Funeral in Blue (r1.0 Insaciable).epub': '5471',
    '[Reinos Olvidados] [Avatar 05] Denning, Troy - El Crisol, el juicio de Cyric el Loco (r1.0 moower).epub': '6583',
    'Feijoo, Benito Jeronimo - [Teatro critico universal 02] Teatro critico universal. Tomo II (r1.0).epub': '4265',
    'Feijoo, Benito Jeronimo - [Teatro critico universal 6] Teatro critico universal (r1.0).epub': '6724',
    'Feijoo, Benito Jeronimo - [Teatro critico universal 8] Teatro critico universal (r1.0).epub': '6202',
    'Feijoo, Benito Jeronimo - [Teatro critico universal] Teatro critico universal. Tomo I (r1.0).epub': '4264',
    '[Multiverso] [El Baston Runico 4] Moorcock, Michael - El Baston Runico (r1.1).epub': '4247',
    'AA., VV. - El libro de los cuentos de hoy (r1.2).epub': '5196'}


class Principal(QDialog):
    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui, Qt.WindowTitleHint)
        self.gui = gui
        self.do_user_config = do_user_config
        self.db = self.gui.current_db.new_api
        self.vista = self.gui.library_view.model()
        Intercambio.icono = icon
        Intercambio.principal = self

        self.setWindowTitle('Biblioteca EPL v2.8.0')
        self.setWindowIcon(icon)
        self.setFixedSize(902, 440)

        fuente = QFont()
        fuente.setPointSize(10)

        layout = QHBoxLayout()
        self.setLayout(layout)

        cuadro_izq = QGroupBox()
        cuadro_izq.setMaximumWidth(250)
        layout.addWidget(cuadro_izq)

        cuadro_der = QGroupBox()
        layout.addWidget(cuadro_der)

        vbox = QVBoxLayout()
        cuadro_izq.setLayout(vbox)

        boton_salir = QPushButton('Salir del plugin')
        boton_salir.setFont(fuente)
        boton_salir.setStyleSheet("background-color:#FFFF7F; color:black;")
        boton_salir.setToolTip('Pulsa para cerrar la aplicación.')
        boton_salir.clicked.connect(self.clicked_terminar)

        self.boton_config = QPushButton('Configurar el plugin')
        self.boton_config.setFont(fuente)
        self.boton_config.setStyleSheet("background-color:#82ff9e; color:black;")
        self.boton_config.setToolTip('Configurar el funcionamiento del plugin.')
        self.boton_config.clicked.connect(self.config)

        self.boton_mantener = QPushButton('Mantener biblioteca ePL')
        self.boton_mantener.setFont(fuente)
        self.boton_mantener.setStyleSheet("background-color:#FFAE1C; color:black;")
        self.boton_mantener.setToolTip('Añadir libros nuevos y actualizar los antiguos en la biblioteca de ePL.')
        self.boton_mantener.clicked.connect(self.iniciar)

        self.boton_forzar = QPushButton('Forzar finalización')
        self.boton_forzar.setFont(fuente)
        self.boton_forzar.setStyleSheet("background-color:#FFA5B7; color:black;")
        self.boton_forzar.setToolTip('Forzar el añadir los libros preparados a la biblioteca de ePL.')
        self.boton_forzar.clicked.connect(self.clicked_forzar)

        self.boton_comprobar = QPushButton('Comprobar biblioteca')
        self.boton_comprobar.setFont(fuente)
        self.boton_comprobar.setStyleSheet("background-color:#6073FF; color:black;")
        self.boton_comprobar.setToolTip('Comprobar la integridad de la biblioteca de Calibre.')
        self.boton_comprobar.clicked.connect(self.clicked_comprobar)

        self.boton_manual = QPushButton('Cargar epub manualmente')
        self.boton_manual.setFont(fuente)
        self.boton_manual.setStyleSheet("background-color:#00FF00; color:black;")
        self.boton_manual.setToolTip('Cargar uno o varios epub manualmente.')
        self.boton_manual.clicked.connect(self.cargar_manualmente)

        self.linea_dir_epub = QLineEdit()
        self.linea_dir_epub.setStyleSheet("background-color:white; color:black;")
        self.linea_dir_epub.setReadOnly(True)
        self.linea_dir_epub.setText(prefs['dir_epub'])

        etiqueta_imagen = QLabel()
        imagen = QPixmap()
        imagen.loadFromData(get_resources('img/Titivillus.png'))
        etiqueta_imagen.setPixmap(imagen)
        etiqueta_imagen.setScaledContents(True)

        vbox.addWidget(self.linea_dir_epub)
        vbox.addWidget(etiqueta_imagen)
        vbox.addWidget(self.boton_mantener)
        vbox.addWidget(self.boton_forzar)
        vbox.addWidget(self.boton_manual)
        vbox.addWidget(self.boton_comprobar)
        vbox.addWidget(self.boton_config)
        vbox.addWidget(boton_salir)

        hbox = QHBoxLayout()
        cuadro_der.setLayout(hbox)

        self.etiqueta_log = QLabel()
        self.etiqueta_log.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.etiqueta_log.setStyleSheet("background-color:white; color:black;")
        Intercambio.log = self.etiqueta_log
        hbox.addWidget(self.etiqueta_log)

        self.dir_epub = prefs['dir_epub']
        Intercambio.aportes = []

        self.resize(self.sizeHint())
        log('INFORMACIÓN IMPORTANTE\n\nPara mantener la integridad en el funcionamiento\nde este plugin, advertimos que cuando se termine\nsu ejecución, simultáneamente se cerrará la ventana\nde Calibre. Por lo tanto, para volver a ejecutarlo\nserá necesario volver a abrir Calibre.\n\nRecomendamos ejecute el módulo "Comprobar biblioteca"\nantes de actualizar la biblioteca de Calibre. ', False)

    def clicked_comprobar(self):
        if '#epg_id' not in self.vista.custom_columns:
            mensajeBox('Mantener biblioteca ePL', 'La biblioteca que se intenta actualizar\nno es la biblioteca de EPL', 'informacion', 'ok')
            self.termina()

        log('Estamos comprobando la integridad de la biblioteca de Calibre.\nEspere un momento.', False)
        all_ids = self.db.all_book_ids()
        epg_id = self.db.all_field_for('#epg_id', all_ids)
        version = self.db.all_field_for('#version', all_ids)

        lista_epg_vacios = []
        lista_version_vacios = []
        dict_epg_correctos = dict()
        lista_epg_repetidos = []
        lista_claves = list(epg_id.keys())
        for key in lista_claves:
            if epg_id[key] is not None:
                if epg_id[key] > 10000000 or epg_id[key] < 20000000:
                    dict_epg_correctos[key] = epg_id[key]
                    if len(version[key]) == 0:
                        lista_version_vacios.append(key)
            else:
                lista_epg_vacios.append(key)

        #Encontrar los epg_id repetidos
        from collections import defaultdict

        d = defaultdict(list)
        lista_claves = list(dict_epg_correctos.keys())
        for item in lista_claves:
            d[dict_epg_correctos[item]].append(item)

        lista_claves = list(d.keys())
        for key in lista_claves:
            if len(d[key]) > 1:
                for item in d[key]:
                    lista_epg_repetidos.append(item)

        texto_01 = ''
        texto_02 = ''
        texto_03 = ''
        texto_04 = '\nSi quiere que el plugin lo corrija automáticamente pulse "Si"\nsi quiere corergirlo usted pulse "No".\nPara que el plugin funcione correctamente debe eliminar este error.\n'
        texto_05 = 'La biblioteca está correctamente formada.'
        if len(lista_epg_vacios) > 0:
            texto_01 = 'Existen ' + str(len(lista_epg_vacios)) + ' epub sin número de EPLID.\nDebe eliminarlo si está en el rango de los epub de ePL,\nsi no lo hace el plugin puede fallar.\n'
        if len(lista_version_vacios) > 0:
            texto_02 = 'Existen ' + str(len(lista_version_vacios)) + ' epub sin número de versión.\n'
        if len(lista_epg_repetidos) > 0:
            texto_03 = 'Hay ' + str(len(lista_epg_repetidos)) + ' valores de EPLID repetidos.\n'

        if texto_01 == '' and texto_02 == '' and texto_03 == '':
            mensajeBox('Mantener biblioteca ePL', texto_05, 'informacion', 'ok')
            log('', False)
        else:
            if texto_01 != '':
                mensajeBox('Mantener biblioteca ePL', texto_01, 'informacion', 'ok')
                log('', False)
                if texto_02 != '' or texto_03 != '':
                    if mensajeBox('Mantener biblioteca ePL', texto_02 + texto_03 + texto_04, 'informacion', 'sino'):
                        if texto_02 != '' and texto_03 != '':
                            log('Estamos eliminando los libros con número de versión vacío y EPLID repetido.')
                        if texto_02 != '':
                            log('Estamos eliminando los libros con número de versión vacío.')
                        if texto_03 != '':
                            log('Estamos eliminando los libros con EPLID repetido.')
                        self.corregir_biblioteca(lista_version_vacios, lista_epg_repetidos)
                        log('La biblioteca está corregida.', False)
                    else:
                        log('', False)
            else:
                if texto_02 != '' or texto_03 != '':
                    if mensajeBox('Mantener biblioteca ePL', texto_02 + texto_03 + texto_04, 'informacion', 'sino'):
                        if texto_02 != '' and texto_03 != '':
                            log('Estamos eliminando los libros con número de versión vacío y EPLID repetido.')
                        if texto_02 != '':
                            log('Estamos eliminando los libros con número de versión vacío.')
                        if texto_03 != '':
                            log('Estamos eliminando los libros con EPLID repetido.')
                        self.corregir_biblioteca(lista_version_vacios, lista_epg_repetidos)
                        log('La biblioteca está corregida.', False)
                    else:
                        log('', False)

    def corregir_biblioteca(self, lista_version_vacios, lista_epg_repetidos):
        if len(lista_version_vacios) > 0:
            self.vista.delete_books_by_id(lista_version_vacios)

        if len(lista_epg_repetidos) > 0:
            self.vista.delete_books_by_id(lista_epg_repetidos)

        self.vista.books_deleted()
        self.vista.refresh(reset=False)
        self.gui.tags_view.recount()
        self.gui.library_view.set_current_row(0)
        self.gui.library_view.refresh_book_details(force=True)

    def clicked_forzar(self):
        if Intercambio.actualizarEPL or Intercambio.anadirEPL:
            self.anadir_epub()
            if Intercambio.actualizarEPL:
                self.epub_actualizados = self.anadidos
                if self.epub_actualizados == self.libros_actualizar:
                    self.anadir_EPL()
                else:
                    self.termina()
            else:
                self.epub_anadidos = self.anadidos
                self.epub_fallidos = self.fallidos
                self.termina()
        else:
            pass

    def clicked_terminar(self):
        if not Intercambio.actualizarEPL and not Intercambio.anadirEPL:
            self.termina()
        else:
            Intercambio.terminar = True

    def termina(self):
        #Limpiar la carpeta de trabajo
        #self.limpiezaCarpeta(self.dir_epub)

        try:
            if Intercambio.actualizarEPL or Intercambio.anadirEPL:
                if Intercambio.actualizarEPL:
                    self.epub_actualizados = self.anadidos
                else:
                    self.epub_anadidos = self.anadidos
                    self.epub_fallidos = self.fallidos
                log('', False)
                mensajeBox('Mantener biblioteca ePL', 'El plugin ha finalizado correctamente.\nSe han actualizado ' + str(self.epub_actualizados) + ' epub,\nse han añadido '+ str(self.epub_anadidos) + ' epub nuevos\n y hay ' + str(self.epub_fallidos) + ' epub que no se han podido cargar.\nPulse en "Aceptar" para salir del plugin.', 'informacion', 'ok')
                self.close()
                sys.exit()
            else:
                Intercambio.inicializado = True
                self.close()
        except:
            self.close()
            sys.exit()

    def config(self):
        self.do_user_config(parent=self)

        #Aplicar los cambios
        self.dir_epub = prefs['dir_epub']
        self.linea_dir_epub.setText(prefs['dir_epub'])
        self.repaint()
        QApplication.processEvents()

    def cargarCSV(self):
        log('Comprobando si el CSV está actualizado.\nEspere un momento.', False)
        Intercambio.aportes = cargarLibros(self.dir_epub)

    def limpiezaCarpeta(self, carpeta):
        if os.path.isdir(carpeta):
            files = os.listdir(carpeta)
            if len(files) > 0:
                for file in files:
                    #Cambiar los derechos en windows
                    if iswindows:
                        os.chmod(os.path.join(carpeta, file), 0o777)
                    try:
                        os.remove(os.path.join(carpeta, file))
                    except:
                        pass
        else:
            #Crear la carpeta
            os.mkdir(carpeta)

    def limpiar_EPLID(self, item):
         return (item.lstrip('"')).lstrip('0')

    def iniciar(self):
        if '#epg_id' not in self.vista.custom_columns:
            mensajeBox('Mantener biblioteca ePL', 'La biblioteca que se intenta actualizar\nno es la biblioteca de EPL', 'informacion', 'ok')
            self.termina()

        self.dir_epub = prefs['dir_epub']
        if os.path.isdir(self.dir_epub):
            pass
        else:
            mensajeBox('Mantener biblioteca ePL', 'No está definida la carpeta\nde descarga de los epub.\nVaya a "Configuración" para definirla.', 'informacion', 'ok')
            return

        self.boton_mantener.hide()
        self.boton_config.hide()
        self.boton_forzar.hide()
        self.boton_comprobar.hide()
        self.boton_manual.hide()

        if len(Intercambio.aportes) == 0:
            self.cargarCSV()
            del(Intercambio.aportes[0])

        #Limpiar la carpeta de trabajo
        self.limpiezaCarpeta(self.dir_epub)

        while len(os.listdir(self.dir_epub)) > 0: 
            mensajeBox('Mantener biblioteca ePL', 'La carpeta de descarga no está vacía, debe eliminar\nlos archivos existentes antes de continuar.\nCompruebe también que el cliente P2P en uso, está vacío.', 'informacion', 'ok')

        #Encontrar los epub a actualizar
        log('Preparando los epub a actualizar y a añadir.\nEspere por favor.', False)
        all_ids = self.db.all_book_ids()

        epg_id = self.db.all_field_for('#epg_id', all_ids)
        version = self.db.all_field_for('#version', all_ids)

        epg_id = {k: int(epg_id[k] - 10000000) for k in epg_id.keys() if epg_id[k] >= 10000000 and epg_id[k] < 20000000}
        version = [float(version[k][0]) for k in epg_id.keys()]
        lista_biblioteca = list(zip(epg_id.values(), version))

        lista_aportes = [tuple([int(self.limpiar_EPLID(item[0])), float(item[9])]) for item in Intercambio.aportes]
        lista_prov = list(set(lista_biblioteca) - set(lista_aportes))
        #Para corregir errores del CSV
        lista_faltan = []
        self.libros_noactualizados = []
        self.dict_faltan = dict()
        for item in lista_prov:
            item1 = [e for e in lista_aportes if e[0] == item[0] and e[1] > item[1]]
            if item1 != []:
                lista_faltan.append(item)
                self.libros_noactualizados.append(item[0])
                self.dict_faltan[str(item1[0][0])] = str(item1[0][1])
        self.libros_actualizar = len(lista_faltan)

        self.lista_actualizar = []
        if self.libros_actualizar > 0:
            self.lista_actualizar = [lista for lista in Intercambio.aportes if int(self.limpiar_EPLID(lista[0])) in self.libros_noactualizados]

        #Encontrar los epub a añadir
        ponerFiltro()
        self.lista_EPLID = set(epg_id.values())
        if Intercambio.filtro == []:
            self.lista_anadir = list(filter(self.funcion_filter1, Intercambio.aportes))
        else:
            self.lista_anadir = list(filter(self.funcion_filter2, Intercambio.aportes))
        self.libros_anadir = len(self.lista_anadir)

        #Inicializar los valores
        self.epub_actualizados = 0
        self.epub_anadidos = 0
        self.epub_fallidos = 0

        self.lista_agregados = []
        self.lista_insertados = []
        self.lista_fallidos = []
        if mensajeBox('Mantener biblioteca ePL', 'Hay ' + str(self.libros_actualizar) + ' epub para actualizar.\n y ' + str(self.libros_anadir) + ' epub nuevos para añadir.\nPulse en "Si" para continuar o en "No" para terminar.', 'informacion', 'sino'):
            if self.libros_actualizar > 0:
                self.cadena_trackers = obtener_trackers()
                self.actualizar_EPL()
            elif self.libros_anadir > 0:
                self.cadena_trackers = obtener_trackers()
                self.anadir_EPL()
            else:
                self.termina()
        else:
            self.termina()

    def funcion_filter1(self, lista):
        if int((lista[0].lstrip('"')).lstrip('0')) not in self.lista_EPLID:
            return True

    def funcion_filter2(self, lista):
        if lista[10] in Intercambio.filtro:
            if int((lista[0].lstrip('"')).lstrip('0')) not in self.lista_EPLID:
                return True

    def continuacion_EPL(self):
        self.boton_forzar.hide()
        if not Intercambio.terminar:
            self.anadir_epub()
        if Intercambio.actualizarEPL:
            self.epub_actualizados = self.anadidos
        elif Intercambio.anadirEPL:
            self.epub_anadidos = self.anadidos
            self.epub_fallidos = self.fallidos

        if Intercambio.terminar:
            self.termina()

        #Descargar los magnet de los libros a incorporar eliminando los libros que ya se han descargado
        self.lista_agregar = [e for e in self.lista_agregar if self.limpiar_EPLID(e[0]) not in self.lista_agregados]

        if len(self.lista_agregar) > 0:
            self.descargarNuevos()
        else:
            control = 0
            limite = 0
            if Intercambio.actualizarEPL:
                while self.libros_actualizar - self.anadidos > 0:
                    control = 0
                    limite = self.libros_actualizar - self.anadidos
                    if limite > prefs['Limite_anadir']:
                        limite = prefs['Limite_anadir']

                    while control < limite:
                        files = os.listdir(self.dir_epub)
                        self.files = [e for e in files if (e not in self.lista_insertados) and (e not in self.lista_fallidos) and os.path.isfile(os.path.join(self.dir_epub, e)) and (e.endswith('.epub') or e.endswith('.EPUB'))]
                        control = len(self.files)
                        log(self.texto_0 + '\n\nHay ' + str(control) + ' epub preparados para añadir a la biblioteca ePL.', False)
                        if control < limite and control != 0:
                            self.boton_forzar.show()
                        else:
                            self.boton_forzar.hide()
                        if Intercambio.terminar:
                            self.termina()
                    if control > 0:
                        self.anadir_epub()

                self.epub_actualizados = self.anadidos
                if mensajeBox('Mantener biblioteca ePL', 'El plugin ha actualizado correctamente ' + str(self.anadidos) + ' epub.\nPulse en "Si" para que añada epub nuevos\no en "No" para salir del plugin.', 'informacion', 'sino'):
                    self.anadir_EPL()
                else:
                    self.termina()

            else:
                while self.libros_anadir - self.anadidos - self.fallidos > 0:
                    control = 0
                    limite = self.libros_anadir - self.anadidos - self.fallidos
                    if limite > prefs['Limite_anadir']:
                        limite = prefs['Limite_anadir']

                    while control < limite:
                        files = os.listdir(self.dir_epub)
                        self.files = [e for e in files if (e not in self.lista_insertados) and (e not in self.lista_fallidos) and os.path.isfile(os.path.join(self.dir_epub, e)) and (e.endswith('.epub') or e.endswith('.EPUB'))]
                        control = len(self.files)
                        log(self.texto_0 + '\n\nHay ' + str(control) + ' epub preparados para añadir a la biblioteca ePL.', False)
                        if control < limite and control != 0:
                            self.boton_forzar.show()
                        else:
                            self.boton_forzar.hide()
                        if Intercambio.terminar:
                            self.termina()
                    if control > 0:
                        self.anadir_epub()
                        print('Libros que quedan por añadir: ' + str(self.libros_anadir - self.anadidos - self.fallidos))
                self.epub_anadidos = self.anadidos
                self.epub_fallidos = self.fallidos
                self.termina()

    def actualizar_EPL(self):
        Intercambio.actualizarEPL = True
        self.texto_0 = 'ACTUALIZANDO LOS LIBROS EXISTENTES EN LA BIBLIOTECA'
        self.lista_agregar = self.lista_actualizar
        self.libros_agregar = self.libros_actualizar

        #Descargar los magnet de los libros actualizados
        log(self.texto_0 + '\n\nEs necesario actualizar ' + str(self.libros_actualizar) + ' epub.', False)

        #Mostrar la lista de libros a actualizar
        contenedorTabla(self.lista_agregar).exec_()
        if Intercambio.tabla == 'Seguir':
            Intercambio.tabla = ''
            self.anadidos = 0
            self.fallidos = 0
            self.descargarNuevos()
        elif Intercambio.tabla == 'noSeguir':
            Intercambio.tabla = ''
            self.anadir_EPL()
        else:
            log(self.texto_0 + '\n\nNo es necesario actualizar ningún epub.', False)
            if mensajeBox('Mantener biblioteca ePL', 'Pulse en "Si" para que añada epub nuevos\no en "No" para salir del plugin.', 'informacion', 'sino'):
                self.anadir_EPL()
            else:
                self.termina()

    def anadir_EPL(self):
        Intercambio.actualizarEPL = False
        Intercambio.anadirEPL = True
        self.texto_0 = 'AÑADIENDO LIBROS NUEVOS A LA BIBLIOTECA'
        self.lista_agregar = self.lista_anadir
        self.libros_agregar = self.libros_anadir

        #Mostrar la lista de epub pendientes de añadir
        if len(self.lista_agregar) > 0:
            contenedorTabla(self.lista_agregar).exec_()
            if Intercambio.tabla == 'Seguir':
                Intercambio.tabla = ''
                self.anadidos = 0
                self.fallidos = 0
                self.descargarNuevos()
            elif Intercambio.tabla == 'noSeguir':
                self.termina()
        else:
            self.anadidos = 0
            self.termina()

    def descargarNuevos(self):
        self.boton_forzar.hide()
        if Intercambio.actualizarEPL:
            log(self.texto_0 + '\n\nSe están descargando los magnet de los epub\na actualizar en la biblioteca ePL.', False)
        elif Intercambio.anadirEPL:
            log(self.texto_0 + '\n\nSe están descargando los magnet de los epub\na añadir a la biblioteca ePL.', False)
        anadidos = 0
        for lista in self.lista_agregar:
            titulo = lista[1]
            try:
                torrent = lista[15]

                lista_torrents = []
                if not torrent.find(',') == -1:
                    lista_torrents = torrent.split(',')
                    torrent = lista_torrents[0]

                torrent = torrent.lstrip(' ')
                if type(titulo) != 'str':
                    titulo = str(titulo)
                titulo = '_'.join(titulo.split(' '))
                if self.cadena_trackers == '':
                    magnet = 'magnet:?xt=urn:btih:' + torrent + '&dn=EPL_[' + self.limpiar_EPLID(lista[0]) + ']_' + titulo + '&tr=udp://9.rarbg.me:2710/announce&tr=udp://tracker.leechers-paradise.org:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://tracker.cyberia.is:6969/announce&tr=udp://exodus.desync.com:6969/announce&tr=udp://explodie.org:6969/announce&tr=http://p4p.arenabg.com:1337/announce&tr=udp://p4p.arenabg.ch:1337/announce&tr=udp://tracker3.itzmx.com:6961/announce&tr=http://tracker1.itzmx.com:8080/announce&tr=udp://tracker.torrent.eu.org:451/announce&tr=udp://open.stealth.si:80/announce&tr=udp://tracker.tiny-vps.com:6969/announce&tr=udp://tracker.ds.is:6969/announce&tr=http://open.acgnxtracker.com:80/announce&tr=udp://tracker.zerobytes.xyz:1337/announce&tr=udp://retracker.lanta-net.ru:2710/announce&tr=udp://open.demonii.si:1337/announce'
                else:
                    magnet = 'magnet:?xt=urn:btih:' + torrent + '&dn=EPL_[' + self.limpiar_EPLID(lista[0]) + ']_' + titulo + self.cadena_trackers 

                if islinux:
                    subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif iswindows or iscygwin:
                    os.startfile(magnet)
                elif isosx:
                    subprocess.Popen(['open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    subprocess.Popen(['xdg-open', magnet], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                anadidos += 1
                self.lista_agregados.append(self.limpiar_EPLID(lista[0]))
                if anadidos == prefs['Limite_descargar']:
                    break
            except:
                pass

        control = 0

        limite = self.libros_agregar - self.anadidos - self.fallidos
        if limite > prefs['Limite_anadir']:
            limite = prefs['Limite_anadir']

        while control < limite:
            files = os.listdir(self.dir_epub)
            self.files = [e for e in files if (e not in self.lista_insertados) and (e not in self.lista_fallidos) and os.path.isfile(os.path.join(self.dir_epub, e)) and (e.endswith('.epub') or e.endswith('.EPUB'))]
            control = len(self.files)
            if control < limite and control != 0:
                self.boton_forzar.show()
            else:
                self.boton_forzar.hide()
            if Intercambio.terminar:
                self.termina()
            log(self.texto_0 + '\n\nHay ' + str(control) + ' epub preparados para añadir a la biblioteca ePL.', False)

        self.continuacion_EPL()

    def anadir_epub(self):
        regex_1 = r"\[\d+\]"
        regex_2 = r"\(r\d\.\d"
        regex_3 = r"\(r.\d\.\d"
        anadidos = len(self.files)
        for file_epub in self.files:
            try:
                matches = re.search(regex_1, str(file_epub))
                stream = open(os.path.join(self.dir_epub, file_epub), 'rb')
                mi = get_metadata(stream, 'epub')
                lengua = idioma(mi.languages[0])
                try:
                    EPLID = EPLID_raros[file_epub]
                except:
                    try:
                        EPLID_titulo = ((matches.group().rstrip(']')).lstrip('[')).lstrip('0')
                        lista = [e for e in Intercambio.aportes if self.limpiar_EPLID(e[0]) == EPLID_titulo]
                        if lista != []:
                            EPLID = EPLID_titulo
                        else:
                            EPLID_csv = buscarEPLID(mi.title, mi.authors[0], lengua)
                            if len(EPLID_csv) == 1:
                                EPLID = self.limpiar_EPLID(EPLID_csv[0])
                            else:
                                self.lista_fallidos.append(file_epub)
                                anadidos -= 1
                                self.fallidos += 1
                                continue
                    except:
                        eplid = buscarEPLID(mi.title, mi.authors[0], lengua)
                        if len(eplid) == 1:
                            EPLID =self.limpiar_EPLID(eplid[0])
                        else:
                            eplid = buscarEPLID(mi.title, mi.authors[0], lengua, True)
                            if len(eplid) == 1:
                                EPLID = self.limpiar_EPLID(eplid[0])
                            else:
                                eplid = buscarEPLID(mi.title, mi.authors[0], lengua, False, True)
                                if len(eplid) == 1:
                                    EPLID = self.limpiar_EPLID(eplid[0])
                                else:
                                    eplid = buscarEPLID(mi.title, mi.authors[0], lengua, True, True)
                                    if len(eplid) == 1:
                                        EPLID = self.limpiar_EPLID(eplid[0])
                                    else:
                                        self.lista_fallidos.append(file_epub)
                                        anadidos -= 1
                                        self.fallidos += 1
                                        continue

                if Intercambio.manualEPL:
                    all_ids = self.db.all_book_ids()
                    epg_id = self.db.all_field_for('#epg_id', all_ids)
                    lista_EPLID = epg_id.values()
                    EPLID_new = str(int(EPLID) + 10000000) + '.0'
                    if float(EPLID_new) in lista_EPLID:
                        if mensajeBox('Mantener biblioteca ePL', 'El EPL_id del archivo\n' + file_epub + '\nya está en la biblioteca\nPulse en "Si" para añadir este epub a pesar de ello\no en "No" para pasar a cargar el siguiente epub.', 'informacion', 'sino'):
                            pass
                        else:
                            continue

                if (EPLID not in self.libros_noactualizados and Intercambio.anadirEPL) or Intercambio.actualizarEPL or Intercambio.manualEPL:
                    matches1 = re.search(regex_2, str(file_epub))
                    matches2 = re.search(regex_3, str(file_epub))
                    if Intercambio.actualizarEPL:
                        version = self.dict_faltan[EPLID]
                    else:
                        try:
                            version = matches1.group().lstrip('(r')
                        except:
                            version = matches2.group().lstrip('(r.')
                        #Para corregir errores del fichero o del csv
                        version1 = [e[9] for e in Intercambio.aportes if self.limpiar_EPLID(e[0]) == EPLID]
                        if version1 != []:
                            if version1[0] > version:
                                version = version1[0]

                    paginas_estado = [[str(e[8]), e[12]] for e in Intercambio.aportes if self.limpiar_EPLID(e[0]) == EPLID]

                    if Intercambio.actualizarEPL:
                        epub_old = self.db.search('#epg_id:' + str(int(EPLID) + 10000000))
                        self.vista.delete_books_by_id(epub_old)
                        self.vista.books_deleted()
                        self.gui.tags_view.recount()
                        self.vista.refresh(reset=False)

                    if self.anadidos == 0:
                        time.sleep(30)

                    stream = open(os.path.join(self.dir_epub, file_epub), 'rb')
                    mi = get_metadata(stream, 'epub')
                    epub_id = self.vista.add_books([os.path.join(self.dir_epub, file_epub)], ['epub'], [mi], add_duplicates=True, return_ids=True)[1][0]

                    self.db.set_field('#pages', {epub_id: paginas_estado[0][0]})
                    self.db.set_field('#version', {epub_id: version})
                    self.db.set_field('#epg_id', {epub_id: int(EPLID) + 10000000})
                    self.db.set_field('#estado', {epub_id: paginas_estado[0][1]})

                    self.vista.books_added(1)
                    self.gui.tags_view.recount()
                    self.gui.library_view.set_current_row(0)
                    self.gui.library_view.refresh_book_details(force=True)

                    anadidos -= 1
                    self.anadidos += 1
                    self.lista_insertados.append(file_epub)
                    if Intercambio.actualizarEPL:
                        self.libros_noactualizados.remove(int(EPLID))

                    if Intercambio.actualizarEPL:
                        texto_1 = 'Hay ' + str(self.libros_agregar - self.anadidos) + ' libros sin actualizar en la biblioteca'
                    elif Intercambio.anadirEPL or Intercambio.manualEPL:
                        texto_1 = 'Hay ' + str(self.libros_agregar - self.anadidos) + ' libros en el CSV sin agregar a la biblioteca'

                    texto_2 = 'Se han añadido ' + str(self.anadidos) + ' epub.\nHay ' + str(self.fallidos) + ' epub que no se han podido cargar.'
                    texto_3 = 'Hay preparados ' + str(anadidos) + ' epub pendientes de añadir.'
                    log(self.texto_0 + '\n\n' + texto_1 + '\n\n' + texto_2 + '\n' + texto_3 + '\n\nAñadido el epub:\n' + str(file_epub), False)

            except:
                pass

            if Intercambio.terminar:
                break

    def cargar_manualmente(self):
        self.boton_mantener.hide()
        self.boton_config.hide()
        self.boton_forzar.hide()
        self.boton_comprobar.hide()
        self.boton_manual.hide()

        self.lista_insertados = []
        self.lista_fallidos = []
        self.libros_noactualizados = []
        self.anadidos = 0
        self.fallidos = 0
        Intercambio.manualEPL = True
        if os.path.isdir(self.dir_epub):
            files = os.listdir(self.dir_epub)
            self.files = [e for e in files if os.path.isfile(os.path.join(self.dir_epub, e)) and (e.endswith('.epub') or e.endswith('.EPUB'))]
            if len(self.files) < 1:
                mensajeBox('Mantener biblioteca ePL', 'La carpeta de descarga no contiene ningún epub.', 'informacion', 'ok')
                return
        else:
            mensajeBox('Mantener biblioteca ePL', 'No está definida la carpeta\nde descarga de los epub.\nVaya a "Configuración" para definirla.', 'informacion', 'ok')
            return

        self.libros_agregar = len(self.files)
        self.cargarCSV()
        del(Intercambio.aportes[0])
        log('Estamos cargando los ' + str(len(self.files)) + ' epub existentes en la carpeta.', False)
        self.texto_0 = 'AÑADIENDO LIBROS NUEVOS A LA BIBLIOTECA'
        self.anadir_epub()
        mensajeBox('Mantener biblioteca ePL', 'Se han añadido ' + str(self.anadidos) + ' epub,\ny hay ' + str(self.fallidos) + ' epub que no se han podido cargar.', 'informacion', 'ok')

        self.boton_mantener.show()
        self.boton_config.show()
        self.boton_forzar.show()
        self.boton_comprobar.show()
        self.boton_manual.show()
        log('', False)
        Intercambio.manualEPL = False


def idioma(lengua):
    if lengua == 'eng':
        return 'Inglés'
    elif lengua == 'cat':
        return 'Catalán'
    elif lengua == 'spa':
        return 'Español'
    elif lengua == 'eus':
        return 'Euskera'
    elif lengua == 'swe':
        return 'Sueco'
    elif lengua == 'epo':
        return 'Esperanto'
    elif lengua == 'glg':
        return 'Gallego'
    elif lengua == 'fra':
        return 'Francés'
    elif lengua == 'por':
        return 'Portugués'
    elif lengua == 'ita':
        return 'Italiano'
    elif lengua == 'deu':
        return 'Alemán'
    else:
        return ''


def coincide_titulo(cad_meta, cad_csv):
    if cad_csv == cad_meta:
        return True
    else:
        cadena_1 = normalizar(cad_csv)
        cadena_2 = normalizar(cad_meta)
        if cadena_1 == cadena_2:
            return True
        else:
            return False


def coincide_autor(cad_meta, cad_csv):
    if coincide_titulo(cad_meta, cad_csv):
        return True
    elif cad_csv.count('&') > 2:
        if cad_meta == 'AA. VV.':
            return True
        else:
            return False
    else:
        return False


def contenido(cad_meta, cad_csv):
    if contiene(cad_meta, cad_csv):
        return True
    elif contiene(cad_csv, cad_meta):
        return True
    else:
        return False


def contiene(cad_1, cad_2):
    if cad_1 in cad_2:
        return True
    else:
        return False


def quitarAcentos(cadena):
    import unicodedata

    nfkd_form = unicodedata.normalize('NFKD', cadena)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalizar(cadena):
    cadena_prov = quitarAcentos(cadena)
    return cadena_prov.replace(" ", "").replace(".", "").replace(",", "").replace("-", "").replace("’", "").replace("'", "").lower()


def buscarEPLID(titulo_meta, autor_meta, idioma_meta, titulo=False, autor=False):
    if titulo:
        return [e[0] for e in Intercambio.aportes if coincide_titulo(titulo_meta, e[1]) and (coincide_autor(autor_meta, e[2]) or contenido(autor_meta, e[2])) and idioma_meta == e[10]]
    elif autor:
        return [e[0] for e in Intercambio.aportes if (coincide_titulo(titulo_meta, e[1]) or contenido(titulo_meta, e[1])) and coincide_autor(autor_meta, e[2]) and idioma_meta == e[10]]
    elif titulo and autor:
        return [e[0] for e in Intercambio.aportes if (coincide_titulo(titulo_meta, e[1]) or contenido(titulo_meta, e[1])) and (coincide_autor(autor_meta, e[2]) or contenido(autor_meta, e[2])) and idioma_meta == e[10]]
    else:
        return [e[0] for e in Intercambio.aportes if coincide_titulo(titulo_meta, e[1]) and coincide_autor(autor_meta, e[2])  and idioma_meta == e[10]]


def ponerFiltro():
    Intercambio.filtro = []
    control = 0
    if prefs['Aleman']:
        Intercambio.filtro.append('Alemán')
        control += 1
    if prefs['Catalan']:
        Intercambio.filtro.append('Catalán')
        control += 1
    if prefs['Espanol']:
        Intercambio.filtro.append('Español')
        control += 1
    if prefs['Esperanto']:
        Intercambio.filtro.append('Esperanto')
        control += 1
    if prefs['Euskera']:
        Intercambio.filtro.append('Euskera')
        control += 1
    if prefs['Frances']:
        Intercambio.filtro.append('Francés')
        control += 1
    if prefs['Gallego']:
        Intercambio.filtro.append('Gallego')
        control += 1
    if prefs['Ingles']:
        Intercambio.filtro.append('Inglés')
        control += 1
    if prefs['Italiano']:
        Intercambio.filtro.append('Italiano')
        control += 1
    if prefs['Mandarin']:
        Intercambio.filtro.append('Mandarín')
        control += 1
    if prefs['Portugues']:
        Intercambio.filtro.append('Portugués')
        control += 1
    if prefs['Sueco']:
        Intercambio.filtro.append('Sueco')
        control += 1
    if control == 12:
        Intercambio.filtro = []


def cargarLibros(dir_epub):
    import zipfile
    from io import BytesIO
    try:
        from urllib.request import urlopen
    except:
        from urllib import urlopen

    url = 'https://www.dropbox.com/s/a9r4p7oyaftaz1b/csv_full_imgs.zip?dl=1'

    lista_ruta_csv = dir_epub.split('/')
    del(lista_ruta_csv[-1])
    ruta_csv = '/'.join(lista_ruta_csv)

    aportes = []
    try:
        resp = urlopen(url)
    except:
        resp = None

    if resp:
        data = resp.read()
        myzipfile = zipfile.ZipFile(BytesIO(data))
        if os.path.isfile(os.path.join(ruta_csv, 'datos_csv.txt')):
            bytes_csv = open(os.path.join(ruta_csv, 'datos_csv.txt'), 'r')
        else:
            with open(os.path.join(ruta_csv, 'datos_csv.txt'), 'w') as Datos_csv:
                Datos_csv.write('0')
                Datos_csv.close()
                bytes_csv = open(os.path.join(ruta_csv, 'datos_csv.txt'), 'r')

        len_csv = bytes_csv.readline()
        if int(len_csv) != len(data):
            log('Guardando el CSV en el disco del ordenador.', False)
            with open(os.path.join(ruta_csv, 'datos_csv.txt'), 'w') as Datos_csv:
                Datos_csv.write(str(len(data)))
                Datos_csv.close()
            myzipfile.extractall(ruta_csv)

    if os.path.isfile(os.path.join(ruta_csv, 'csv_full_imgs.csv')):
        log('Leyendo el CSV en el disco del ordenador.', False)
        f = open(os.path.join(ruta_csv, 'csv_full_imgs.csv'), 'rb')
    else:
        log('No hay fuente de datos.\nEl programa no puede continuar.', False)
        return aportes

    aportes = f.readlines()
    aportes = [(lista.decode('utf-8')).split('","') for lista in aportes]

    return aportes


def obtener_trackers():
    cadena_trackers = ''
    try:
        from urllib.request import urlopen
    except:
        from urllib import urlopen

    try:
        resp = urlopen('https://ngosang.github.io/trackerslist/trackers_best_ip.txt')
    except:
        resp = None

    if resp:
        trackers = resp.readlines()
    else:
        return cadena_trackers

    for e in trackers:
        if e.decode('utf-8') == '\n':
            trackers.remove(e)

    for e in trackers:
        a = trackers.index(e)
        trackers[a] = e.decode('utf-8').rstrip('\n')

    for e in trackers:
        cadena_trackers = cadena_trackers + '&tr=' + e

    return cadena_trackers


class TablaPrevisualizacion(QTableWidget):

    def __init__(self, parent):
        QTableWidget.__init__(self, parent)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().minimumSectionSize())
        self.resize(parent.width(), parent.height())

    def populate_table(self, csv_rows):
        self.clear()
        self.setRowCount(len(csv_rows))
        header_labels = ['EPL_Id', 'Título', 'Autores', 'Serie', 'Ver.']
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        header = self.horizontalHeader()
        try:
            header.setSectionResizeMode(1, QHeaderView.Custom)
        except:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Custom)

        for row, csv_row in enumerate(csv_rows):
            self.populate_table_row(row, csv_row)

        # Reajustamos el tamaño de las columnas a un máximo de 200
        for num_columna in range(0, len(header_labels)):
            if num_columna == 0:
                self.setColumnWidth(num_columna, 50)
            elif num_columna == 1:
                self.setColumnWidth(num_columna, 250)
            elif num_columna == 2 or num_columna == 3:
                self.setColumnWidth(num_columna, 170)
            elif num_columna == 4:
                self.setColumnWidth(num_columna, 30)
            num_columna += 1

    def populate_table_row(self, row, csv_row):
        for col, col_data in enumerate(csv_row):
            if col == 0 or col == 4:
                item = ReadOnlyTableWidgetItem(col_data)
                item.setTextAlignment(Qt.AlignHCenter)
                self.setItem(row, col, item)
            else:
                self.setItem(row, col, ReadOnlyTableWidgetItem(col_data))


class ReadOnlyTableWidgetItem(QTableWidgetItem):

    def __init__(self, text):
        if text is None:
            text = ''
        try:
            QTableWidgetItem.__init__(self, text, QtGui.QTableWidgetItem.UserType)
        except:
            QTableWidgetItem.__init__(self, text, 0)

        self.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)


class contenedorTabla(QDialog):
    def __init__(self, lista):
        QDialog.__init__(self)
        if Intercambio.actualizarEPL:
            self.setWindowTitle('Epub para actualizar la biblioteca')
        else:
            self.setWindowTitle('Epub para añadir a la biblioteca')
        self.setWindowIcon(Intercambio.icono)
        self.setModal(True)

        fuente = QFont()
        fuente.setPointSize(10)

        layout = QVBoxLayout()
        self.setLayout(layout)

        cuadro_sup = QGroupBox()
        cuadro_sup.setMinimumWidth(745)
        cuadro_sup.setMinimumHeight(300)
        layout.addWidget(cuadro_sup)

        vbox = QHBoxLayout()
        cuadro_sup.setLayout(vbox)

        cuadro_inf = QGroupBox()
        layout.addWidget(cuadro_inf)

        hbox = QHBoxLayout()
        cuadro_inf.setLayout(hbox)

        if Intercambio.actualizarEPL:
            boton_noseguir = QPushButton('No actualizar')
        else:
            boton_noseguir = QPushButton('Terminar')
        boton_noseguir.setFont(fuente)
        boton_noseguir.setStyleSheet("background-color:#FF491C; color:black;")
        if Intercambio.actualizarEPL:
            boton_noseguir.setToolTip('Pulsa para seguir sin actualizar.')
        else:
            boton_noseguir.setToolTip('Pulsa para seguir sin añadir nuevos epub.')
        boton_noseguir.clicked.connect(self.tabla_noseguir)

        if Intercambio.actualizarEPL:
            boton_seguir = QPushButton('Actualizar')
        else:
            boton_seguir = QPushButton('Añadir')
        boton_seguir.setFont(fuente)
        boton_seguir.setStyleSheet("background-color:#82ff9e; color:black;")
        boton_seguir.setToolTip('Pulsa para seguir con la actualización.')
        boton_seguir.clicked.connect(self.tabla_seguir)

        etiqueta = QLabel()
        if Intercambio.actualizarEPL:
            etiqueta.setText('Hay ' + str((Intercambio.principal).libros_actualizar) + ' epub para actualizar.')
        else:
            etiqueta.setText('Hay ' + str((Intercambio.principal).libros_anadir) + ' epub para añadir.')
        etiqueta.setMinimumWidth(300)
        etiqueta.setAlignment(Qt.AlignCenter)

        hbox.addWidget(boton_noseguir)
        hbox.addWidget(etiqueta)
        hbox.addWidget(boton_seguir)

        #Mostrar los epub a actualizar o añadir
        filas = []
        for item in lista:
            fila = []
            fila.append((Intercambio.principal).limpiar_EPLID(item[0]))
            fila.append(item[1])
            fila.append(item[2])
            if item[4] == '' or item[5] == '':
                fila.append(item[4])
            else:
                fila.append(item[4] + ' [' + item[5] + ']')
            fila.append(item[9])
            filas.append(fila)

        tabla = TablaPrevisualizacion(self)
        tabla.populate_table(filas)
        vbox.addWidget(tabla)

    def tabla_noseguir(self):
        Intercambio.tabla = 'noSeguir'
        self.close()

    def tabla_seguir(self):
        Intercambio.tabla = 'Seguir'
        self.close()


def mensajeBox(titulo, texto, tipo, botones):
    ''' Crea un widget QMessageBox donde se puede escribir un mensaje.
    '''
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setWindowIcon(Intercambio.icono)
    msg.setText(texto)
    if tipo == 'informacion':
        tip = QMessageBox.Information
        msg.setIcon(tip)
    if botones == 'ok':
        bot = QMessageBox.Ok
        msg.setStandardButtons(bot)
        msg.exec_()
    elif botones == 'sino':
        msg.addButton('Si', QMessageBox.YesRole)
        msg.setStandardButtons(QMessageBox.No)
        retval = msg.exec_()

        if retval == QMessageBox.No:
            return False
        else:
            return True


def log(texto, imprime=True):

    if imprime:
        old_stdout = sys.stdout
        sys.stdout = sys.__stdout__
        print(texto)
        sys.stdout = old_stdout
    else:
        Intercambio.log.setText(texto)
        Intercambio.log.repaint()
        QApplication.processEvents()


def initialize_plugin():
    if Intercambio.inicializado:
        Intercambio.inicializado = False
        return True
    else:
        return False


class Intercambio(object):
    icono = None
    log = None
    aportes = []
    actualizarEPL = False
    anadirEPL = False
    manualEPL = False
    filtro = []
    tabla = ''
    principal = None
    terminar = False
    fd = None
    inicializado = True
