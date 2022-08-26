#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2020, lgonzalezp'
__docformat__ = 'restructuredtext en'


from calibre.utils.config import JSONConfig

try:
    import PyQt5
    from PyQt5.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout
    from PyQt5.QtWidgets import QLabel, QWidget, QLineEdit, QToolTip, QFileDialog
    from PyQt5.QtGui import QPixmap, QFont
    from PyQt5.QtCore import pyqtSignal
except:
    import PyQt6
    from PyQt6.QtWidgets import QCheckBox, QGroupBox, QVBoxLayout, QHBoxLayout
    from PyQt6.QtWidgets import QLabel, QWidget, QLineEdit, QToolTip, QFileDialog
    from PyQt6.QtGui import QPixmap, QFont
    from PyQt6.QtCore import pyqtSignal

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/interface_demo) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/biblioteca_EPL')

# Ajustes por defecto
prefs.defaults['Aleman'] = True
prefs.defaults['Catalan'] = True
prefs.defaults['Espanol'] = True
prefs.defaults['Esperanto'] = True
prefs.defaults['Euskera'] = True
prefs.defaults['Frances'] = True
prefs.defaults['Gallego'] = True
prefs.defaults['Ingles'] = True
prefs.defaults['Italiano'] = True
prefs.defaults['Mandarin'] = True
prefs.defaults['Portugues'] = True
prefs.defaults['Sueco'] = True
prefs.defaults['Limite_descargar'] = 50
prefs.defaults['Limite_anadir'] = 30
prefs.defaults['dir_epub'] = ''

class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.setMaximumWidth(500)
        self.setMaximumHeight(350)

        layout = QHBoxLayout()
        self.setLayout(layout)

        cuadro_izq = QGroupBox()
        layout.addWidget(cuadro_izq)

        fuente = QFont()
        fuente.setPointSize(10)
        fuente.setBold(True)

        cuadro_der = QGroupBox('Carpeta de descarga')
        cuadro_der.setFont(fuente)
        layout.addWidget(cuadro_der)
        cuadro_der.setMaximumWidth(250)
        cuadro_der.setMaximumHeight(350)

        vertical = QVBoxLayout()
        cuadro_izq.setLayout(vertical)

        idioma_libros = QGroupBox('Idiomas de los libros:', self)
        idioma_libros.setFont(fuente)
        vertical.addWidget(idioma_libros)
        idioma_libros.setMaximumWidth(250)
        idioma_libros.setMaximumHeight(250)

        vbox = QVBoxLayout()
        idioma_libros.setLayout(vbox)

        idioma1 = QHBoxLayout()
        vbox.addLayout(idioma1)
        self.check_aleman = QCheckBox('Aleman')
        self.check_ingles = QCheckBox('Inglés')
        self.check_aleman.setChecked(prefs['Aleman'])
        self.check_ingles.setChecked(prefs['Ingles'])
        idioma1.addWidget(self.check_aleman)
        idioma1.addWidget(self.check_ingles)

        idioma2 = QHBoxLayout()
        vbox.addLayout(idioma2)
        self.check_catalan = QCheckBox('Catalán')
        self.check_italiano = QCheckBox('Italiano')
        self.check_catalan.setChecked(prefs['Catalan'])
        self.check_italiano.setChecked(prefs['Italiano'])
        idioma2.addWidget(self.check_catalan)
        idioma2.addWidget(self.check_italiano)

        idioma3 = QHBoxLayout()
        vbox.addLayout(idioma3)
        self.check_espanol = QCheckBox('Español')
        self.check_mandarin = QCheckBox('Mandarín')
        self.check_espanol.setChecked(prefs['Espanol'])
        self.check_mandarin.setChecked(prefs['Mandarin'])
        idioma3.addWidget(self.check_espanol)
        idioma3.addWidget(self.check_mandarin)

        idioma4 = QHBoxLayout()
        vbox.addLayout(idioma4)
        self.check_esperanto = QCheckBox('Esperanto')
        self.check_portugues = QCheckBox('Portugués')
        self.check_esperanto.setChecked(prefs['Esperanto'])
        self.check_portugues.setChecked(prefs['Portugues'])
        idioma4.addWidget(self.check_esperanto)
        idioma4.addWidget(self.check_portugues)

        idioma5 = QHBoxLayout()
        vbox.addLayout(idioma5)
        self.check_euskera = QCheckBox('Euskera')
        self.check_sueco = QCheckBox('Sueco')
        self.check_euskera.setChecked(prefs['Euskera'])
        self.check_sueco.setChecked(prefs['Sueco'])
        idioma5.addWidget(self.check_euskera)
        idioma5.addWidget(self.check_sueco)

        idioma6 = QHBoxLayout()
        vbox.addLayout(idioma6)
        self.check_frances = QCheckBox('Francés')
        self.check_gallego = QCheckBox('Gallego')
        self.check_frances.setChecked(prefs['Frances'])
        self.check_gallego.setChecked(prefs['Gallego'])
        idioma6.addWidget(self.check_frances)
        idioma6.addWidget(self.check_gallego)

        limites = QGroupBox('Límites para añadir epub', self)
        limites.setFont(fuente)
        vertical.addWidget(limites)
        limites.setMaximumWidth(250)
        limites.setMaximumHeight(100)

        vbox = QVBoxLayout()
        limites.setLayout(vbox)

        descargar = QHBoxLayout()
        vbox.addLayout(descargar)
        limite_descargar = QLabel('Límite de descargas')
        self.escribir_limite_descargar = QLineEdit()
        self.escribir_limite_descargar.setText(str(prefs['Limite_descargar']))
        descargar.addWidget(limite_descargar)
        descargar.addWidget(self.escribir_limite_descargar)

        anadir = QHBoxLayout()
        vbox.addLayout(anadir)
        limite_anadir = QLabel('Nº de epub a añadir')
        self.escribir_limite_anadir = QLineEdit()
        self.escribir_limite_anadir.setText(str(prefs['Limite_anadir']))
        anadir.addWidget(limite_anadir)
        anadir.addWidget(self.escribir_limite_anadir)

        dir_descarga = QVBoxLayout()
        cuadro_der.setLayout(dir_descarga)

        self.linea_dir_epub = QLineEdit()
        self.linea_dir_epub.setStyleSheet("background-color:white; color:black;")
        self.linea_dir_epub.setReadOnly(True)
        self.linea_dir_epub.setText(prefs['dir_epub'])

        etiqueta_carpeta = QLabelClickable()
        imagen = QPixmap()
        imagen.loadFromData(get_resources('img/carpeta.png'))
        etiqueta_carpeta.setPixmap(imagen)
        etiqueta_carpeta.setScaledContents(True)
        etiqueta_carpeta.setToolTip('Modificar la ruta de la carpeta de descarga de los magnets.')
        etiqueta_carpeta.clicked.connect(self.carpetaEpub)

        dir_descarga.addWidget(self.linea_dir_epub)
        dir_descarga.addWidget(etiqueta_carpeta)

        self.resize(self.sizeHint())

    def save_settings(self):
        prefs['Aleman'] = self.check_aleman.isChecked()
        prefs['Catalan'] = self.check_catalan.isChecked()
        prefs['Espanol'] = self.check_espanol.isChecked()
        prefs['Esperanto'] = self.check_esperanto.isChecked()
        prefs['Euskera'] = self.check_euskera.isChecked()
        prefs['Frances'] = self.check_frances.isChecked()
        prefs['Gallego'] = self.check_gallego.isChecked()
        prefs['Ingles'] = self.check_ingles.isChecked()
        prefs['Italiano'] = self.check_italiano.isChecked()
        prefs['Mandarin'] = self.check_mandarin.isChecked()
        prefs['Portugues'] = self.check_portugues.isChecked()
        prefs['Sueco'] = self.check_sueco.isChecked()
        prefs['Limite_descargar'] = int(self.escribir_limite_descargar.text())
        prefs['Limite_anadir'] = int(self.escribir_limite_anadir.text())
        prefs['dir_epub'] = self.linea_dir_epub.text()

    def validate(self):
        if int(self.escribir_limite_descargar.text()) >= int(self.escribir_limite_anadir.text()):
            return True
        else:
            return False

    def carpetaEpub(self):
        carpeta = fileChooser(self, 'Escoja una carpeta.', prefs['dir_epub'])
        self.linea_dir_epub.setText(carpeta)
        self.dir_epub = carpeta


def fileChooser(parent, titulo, directory):
    dlg = QFileDialog(parent, titulo, directory)
    try:
        dlg.setFileMode(QFileDialog.DirectoryOnly)
    except:
        dlg.setFileMode(QFileDialog.FileMode.Directory)
    if dlg.exec_():
        inpath = dlg.selectedFiles()

    try:
        if type(inpath) is tuple or list:
            recpath = inpath[0]
        elif inpath == '':
            recpath = ''
        else:
            recpath = inpath

        return recpath
    except:
        pass

class QLabelClickable(QLabel):

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLabel.__init__(self)

    def mousePressEvent(self, ev):
        self.clicked.emit()
