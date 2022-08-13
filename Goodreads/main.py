#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__   = 'GPL v3'
__copyright__ = '2021, Wiso'
__docformat__ = 'restructuredtext en'

try:  ## PyQT6
    from PyQt6.QtCore import *
    #from PyQt6.QtGui import *
    from PyQt6.QtWidgets import QProgressDialog
    print('Using QT6')
except ImportError:  ## PyQT5
    from PyQt5 import Qt
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import QProgressDialog
    print('Using QT5')

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

if False:
    # This is here to keep my python error checker from complaining about
    # the builtin functions that will be defined by the plugin loading system
    # You do not need this code in your plugins
    get_icons = get_resources = None

try:
    from PyQt6.QtCore import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
except ImportError:
    from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel

from calibre_plugins.Goodreads.config import prefs
import os


class DemoDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel(prefs['menu'])
        self.l.addWidget(self.label)

        self.setWindowTitle('Goodreads')
        self.setWindowIcon(icon)

        self.about_button = QPushButton(_('About:'), self)
        self.about_button.clicked.connect(self.about)
        self.l.addWidget(self.about_button)

        #self.marked_button = QPushButton(
        #    'Mostrar libros con un único formato en calibre GUI', self)
        #self.marked_button.clicked.connect(self.marked)
        #self.l.addWidget(self.marked_button)

        #self.view_button = QPushButton(
        #    'Mostrar el último libro añadido', self)
        #self.view_button.clicked.connect(self.view)
        #self.l.addWidget(self.view_button)

        #self.update_metadata_button = QPushButton(
        #    'Actualizar metadatos del libro', self)
        #self.update_metadata_button.clicked.connect(self.update_metadata)
        #self.l.addWidget(self.update_metadata_button)

        self.update_duration_button = QPushButton(
            _('Update the audiobook duration column'), self)
        self.update_duration_button.clicked.connect(self.update_duration)
        self.l.addWidget(self.update_duration_button)

        self.conf_button = QPushButton(
            _('Configure this plugin'), self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        self.resize(self.sizeHint())

    def about(self):
        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.
        #
        # Note that if you are loading more than one file, for performance, you
        # should pass a list of names to get_resources. In this case,
        # get_resources will return a dictionary mapping names to bytes. Names that
        # are not found in the zip file will not be in the returned dictionary.
        text = get_resources('about.txt')
        QMessageBox.about(self, _('About the AudioBook Duration'),
                text.decode('utf-8'))

    def marked(self):
        ''' Show books with only one format '''
        db = self.db.new_api
        matched_ids = {book_id for book_id in db.all_book_ids() if len(db.formats(book_id)) == 1}
        # Mark the records with the matching ids
        # new_api does not know anything about marked books, so we use the full
        # db object
        self.db.set_marked_ids(matched_ids)

        # Tell the GUI to search for all marked records
        self.gui.search.setEditText('marked:true')
        self.gui.search.do_search()

    def view(self):
        ''' View the most recently added book '''
        most_recent = most_recent_id = None
        db = self.db.new_api
        for book_id, timestamp in db.all_field_for('timestamp', db.all_book_ids()).items():
            if most_recent is None or timestamp > most_recent:
                most_recent = timestamp
                most_recent_id = book_id

        if most_recent_id is not None:
            # Get a reference to the View plugin
            view_plugin = self.gui.iactions['View']
            # Ask the view plugin to launch the viewer for row_number
            view_plugin._view_calibre_books([most_recent_id])

    def update_metadata(self):
        '''
        Set the metadata in the files in the selected book's record to
        match the current metadata in the database.
        '''
        from calibre.ebooks.metadata.meta import set_metadata
        from calibre.gui2 import error_dialog, info_dialog

        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('Cannot update metadata'),
                             _('No books selected'), show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        db = self.db.new_api
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            if not fmts:
                continue
            for fmt in fmts:
                fmt = fmt.lower()
                # Get a python file object for the format. This will be either
                # an in memory file or a temporary on disk file
                ffile = db.format(book_id, fmt, as_file=True)
                ffile.seek(0)
                # Set metadata in the format
                set_metadata(ffile, mi, fmt)
                ffile.seek(0)
                # Now replace the file in the calibre library with the updated
                # file. We dont use add_format_with_hooks as the hooks were
                # already run when the file was first added to calibre.
                db.add_format(book_id, fmt, ffile, run_hooks=False)

        info_dialog(self, 'Updated files',
                'Updated the metadata in the files of %d book(s)'%len(ids),
                show=False)

    def create_progress_bar(self, title):
        progress = QProgressDialog(self)
        progress.setAutoClose(False)
        progress.setWindowTitle(title)
        progress.setCancelButton(None)
        #progress.setWindowModality(Qt.WindowModal)
        return progress


    def update_duration(self):
        '''
        Set the metadata in the files in the selected book's record to
        match the current metadata in the database.
        '''
        #
        from calibre.ebooks.metadata.meta import set_metadata
        from calibre.gui2 import error_dialog, info_dialog
        from calibre.gui2.dialogs.progress import ProgressDialog

        #
        progress = QProgressDialog('Work in progress', '', 0, 100, self)
        progress.setWindowTitle(_('Calculating AudioBook Files Duration'))
        #progress.setWindowModality(Qt.WindowModal)
        progress.show()
        progress.setValue(0)
        #

        #print('Walter estoy dentro de la función que se ejecuta al pulsar el botón del menú')
        col_duration = prefs['custom_colum_duration']
        duration = ''
        selected = 0
        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('Cannot update metadata'),
                             _('No books selected'), show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        selected = len(ids)
        print('Tengo seleccionados ' + str(selected) + ' libros.')
        db = self.db.new_api
        path = ''
        cont = 1
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            if not fmts:
                continue
            for fmt in fmts:
                fmt = fmt.lower()
                # Get a python file object for the format. This will be either
                # an in memory file or a temporary on disk file
                #path = db.format(book_id, fmt, as_file=True)
                path = db.format_abspath(book_id, fmt)
                trash = '.' + path.split(os.sep)[-1]
                book_name = path.split(os.sep)[-1]
                final_path = path[:-len(trash)]
                #print('Antes de entrar en la función CHECK')
                #print('PATH: ' + final_path)
                # Llamo a mi función para calcular la duración
                progress.setLabelText(book_name)
                loop = QEventLoop()
                QTimer.singleShot(5, loop.quit)
                loop.exec_()
                duration = "" #check_duration(final_path, progress)
                #print('variable duration = ' + duration)
                mi.set(col_duration, duration)
                #print(col_duration)
                self.db.set_metadata(book_id, mi)
                #print('Después de hacer un set_metadata')
                self.gui.library_view.model().refresh_ids([book_id])
                #
            print('El % es: ' + str(int((100/selected)*cont)) )
            progress.setValue(int((100/selected)*cont))
            cont = cont + 1
        self.gui.library_view.model().refresh_ids([book_id])
        info_dialog(self, _('Update files'),
                _('Updated duration column in %d book (s) files')%len(ids),
                show=True)


    def config(self):
        self.do_user_config(parent=self)
        # Apply the changes
        self.label.setText(prefs['menu'])
