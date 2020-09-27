# -*- coding: utf-8 -*-

"""
   _____         _        _           _                   _                _           _
  / ____|       | |      | |         | |                 (_)              | |         (_)
 | |     ___  __| |   ___| | ___  ___| |_ _ __ ___  _ __  _  ___ ___    __| | ___  ___ _  __ _ _ __
 | |    / _ \/ _` |  / _ \ |/ _ \/ __| __| '__/ _ \| '_ \| |/ __/ __|  / _` |/ _ \/ __| |/ _` | '_ \
 | |___|  __/ (_| | |  __/ |  __/ (__| |_| | | (_) | | | | | (__\__ \ | (_| |  __/\__ \ | (_| | | | |
  \_____\___|\__,_|  \___|_|\___|\___|\__|_|  \___/|_| |_|_|\___|___/  \__,_|\___||___/_|\__, |_| |_|
                                                                                          __/ |
                                                                                         |___/
 Project     : The poorman's frequency counter. 
 File        : tools/helpdialogs.py
 Version     : 1.0
 Description : Dialog window that displays an help  text file.



 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt5.QtCore import Qt, pyqtSignal,QSize, QLocale, QSettings
from PyQt5.QtWidgets import (QWidget, QDialog, QDialogButtonBox, QVBoxLayout, QTextEdit,
                             QApplication)
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor
from tools.langtranslate import load_section
import os

class HelpDialog(QDialog):
    """ loads and displays an help file (any text file) """
    filename = ''
    appsettings = QSettings("C.E.D", "freqmeter")
     
    def __init__(self, parent=None, filename=None):
        super(HelpDialog,self).__init__()
        self.filename = filename
        self.langstr = load_section(self.appsettings.value('Lang','translations/freqmeter_en'), 'helpdialogs')
        
        #self.setWindowTitle('User manual')
        self.setWindowTitle(self.langstr[0])
        self.setupUI()
        self.load_data()
        self.setFixedSize(self.size()+QSize(150,50))
        
    def setupUI(self):
        # set window icon     
        self.setWindowIcon(QIcon('resources/images/icon.png'))
        
        # dialog layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)        
        
        # add ok button
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        # add a textbox
        self.textbox = QTextEdit()
        self.textbox.setReadOnly(True)
        # add all stuff to layout
        self.layout.addWidget(self.textbox)
        self.layout.addWidget(self.buttonBox)        
    
    def load_data(self):
        """ load and display a text file """
        try:
            with open(self.filename, 'r') as reader:        
                self.textbox.clear()
                self.textbox.append(reader.read())
                self.textbox.moveCursor(QTextCursor.Start)
        except FileNotFoundError:
            self.textbox.clear()
            #self.textbox.append('File {} not found !'.format(self.filename))
            self.textbox.append(self.langstr[1].format(self.filename))
            
