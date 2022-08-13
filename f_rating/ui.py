#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.Qt import QMenu, QToolButton, QPixmap, Qt, QDialog, QProgressDialog
                        
__license__   = 'GPL v3'
__copyright__ = '2019, Mod'
__docformat__ = 'restructuredtext en'

try:
  load_translations()
except NameError:
  pass # load_translations() added in calibre 1.9

import sys

if False:
    # This is here to keep my python error checker from complaining about
    # the builtin functions that will be defined by the plugin loading system
    # You do not need this code in your plugins
    get_icons = get_resources = None

# The class that all interface action plugins must inherit from
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog

class InterfacePlugin(InterfaceAction):
    name = 'F_rating'
    # Declare the main action associated with this plugin
    # The keyboard shortcut can be None if you dont want to use a keyboard
    # shortcut. Remember that currently calibre has no central management for
    # keyboard shortcuts, so try to use an unusual/unused shortcut.
    action_spec = ('F_rating', None,
            _('Run F_rating to set decimal rating'), 'Ctrl+Shift+F1')
    action_type = 'current'
    popup_type = QToolButton.MenuButtonPopup
    
    def start_change(self):
        check=False
        check=self.check_column() # check if column gr1 exists
        #print ('check3:',check)
        if check==False: # first make column
            return
        else: # there is an column gr1
            self.change()
    
    def start_column(self):
        check=self.check_column()
        if check:
            info_dialog(self.gui, _('Column checked'),
                _('Column exists already'),
                show=True)

    def check_column(self):
        check=False
        check=self.check_gr() # check if column gr1 exists
        #print ('check1:',check)
        if check==False: # make column
            self.make_gr()
            #self.close()   
        return(check)

    def make_gr(self):
        num = self.db.create_custom_column('gr1', 'gr_Rating','float',False,'{}')
        num = self.db.create_custom_column('gr2', 'gr_Reviews','float',False,'{}')
        #print ('Custom column created with id: %d'%num)
        info_dialog(self.gui, _('Column created'),
                _('A custom column is created. restart Calibre to continue\n If the column is not created you have to do it manual'),
                show=True)
        
    def check_gr(self):
        self.db = self.gui.current_db
        check= False
        cols = self.db.custom_column_label_map
        for col in cols.items():
                print('col:',col[0])
                if col[0]=='gr1':
                    check= True
        return(check)
          
    def change(self):   
        puber = self.db.FIELD_MAP['publisher']
        print (_('searching ..'))
        tel=0
        for record in self.db.data:
            if sys.version_info.major==2:
                #print("versie 2.x")
                pub_org=str(record[puber]).encode('utf8')
                #pub_org=record[puber]
                pub_org = pub_org.decode('utf8','ignore')
            else:
                pub_org=str(record[puber])
            pos=pub_org.find('| Rating') # PrB.rating

            if pos>0:
                print ('pos:',pos)
                pub=pub_org[0:pos-1] # part of publisher
                #print ('len:',len(pub_org),'-', pos+11)
                if len(pub_org)>pos+8:
                    rat=pub_org[pos+8:] # part of floatrating
                else:
                    rat=None
                #print ('pub:',pub)
                #print ('rat:',rat)
                if rat:
                    pos2=rat.find(':')
                    pos3=rat.find('| Reviews')
                    #print ('pos2:',pos2)
                    if pos2>-1:
                        rating=rat[pos2+1:]
                        rating=rat[pos2+1:pos3].replace("|","").strip()
                        pos4=rat[pos2+1:].find(':')
                        rev=rat[pos4+2:].strip()
                        pub=pub_org[0:pos] # part of publisher
                        #print ('rat2:',rat) 
                        #print ('pub2:',pub)
                        
                id=record[0]
                print('id1:', id)
                mi = self.db.get_metadata(id, index_is_id=True)
                print ('mi:', mi)
                mi.publisher=pub

                print( mi.publisher)

                mi.set('#gr1',rating)
                mi.set('#gr2', rev)
                self.db.set_metadata(id, mi, force_changes=True)
                tel+=1
        info_dialog(self.gui, _('Database Update'),
                _('Finished extracting rating from publisherfield \n- for a total of %d books')%tel,
                show=True)
    
    def genesis(self):
        # This method is called once per plugin, do initial setup here

        # Set the icon for this interface action
        # The get_icons function is a builtin function defined for all your
        # plugin code. It loads icons from the plugin zip file. It returns
        # QIcon objects, if you want the actual data, use the analogous
        # get_resources builtin function.
        #
        # Note that if you are loading more than one icon, for performance, you
        # should pass a list of names to get_icons. In this case, get_icons
        # will return a dictionary mapping names to QIcons. Names that
        # are not found in the zip file will result in null QIcons.
        icon = get_icons('images/icon.png')

        # The qaction is automatically created from the action_spec defined
        # above
        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.start_change)
        # build menu
        m = self.menu = QMenu(self.gui)
        # XXF create more icons?
        from functools import partial
        for (short, tooltip, action) in self.menudata:
            self.create_menu_action(m, short, short, None, None, tooltip, partial(action,self), None)
        self.qaction.setMenu(m) 
                
    menudata = (
        (_("Set decimal rating"), _("Search end set database for decimal_ratings"),start_change),
        (_("Check and create custom column"),_(" Create custom column"),start_column)
       
        )
    def apply_settings(self):
        from calibre_plugins.F_rating.config import prefs
        # In an actual non trivial plugin, you would probably need to
        # do something based on the settings in prefs
        prefs

    
