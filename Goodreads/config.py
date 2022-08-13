#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__   = 'GPL v3'
__copyright__ = '2021, Wiso'
__docformat__ = 'restructuredtext en'

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from qt.core import QWidget, QHBoxLayout, QLabel, QLineEdit

from calibre.utils.config import JSONConfig

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/interface_demo) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/Goodreads')

# Set defaults
prefs.defaults['menu'] = _('Configuration menu (Goodreads))')
prefs.defaults['custom_colum_duration'] = _('Custom column like #colum_name')

class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QHBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel(_('&Duration:'))
        self.l.addWidget(self.label)

        self.msg = QLineEdit(self)
        self.msg.setText(prefs['custom_colum_duration'])
        self.l.addWidget(self.msg)
        self.label.setBuddy(self.msg)

    def save_settings(self):
        prefs['custom_colum_duration'] = self.msg.text()
