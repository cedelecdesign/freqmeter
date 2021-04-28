#!/usr/bin/env python3
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
 File        : freqmeter.py
 Version     : 1.0
 Description : A simple Arduino based frequency meter.



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

from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QSize, QLocale, QTranslator,
                          QLibraryInfo, QResource, QCoreApplication, QSettings)
from PyQt5.QtWidgets import (QWidget, QMainWindow, QGridLayout, QHBoxLayout,
                             QVBoxLayout, QLabel,
                             QRadioButton, QPushButton, QMessageBox, QAction,
                             QGroupBox, QApplication, QLineEdit, QCheckBox,
                             QComboBox)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from tools.settingsdialogs import SerialSettingsDialog, LangSelector
from tools.helpdialogs import HelpDialog
from tools.graphdialog import GraphDialog
from tools.langtranslate import load_section
from tools.datafilters import filter
from tools.CustomWidgets import EditorDialog
import sys
import serial
import math


class MainWindow(QMainWindow):
    """ UI code
        Creates window and displays data
    """
    # a global list to store serial settings
    settingsList=[]
    # is connection whith arduino established?
    isConnected = False
    # Calculate units?
    autorange = True
    # freeze reading?
    holddata = False
    # raw value from serial (int)
    readvalue = 0
    # Settings saved by the system
    appsettings = QSettings("C.E.D", "freqmeter")
    # Multipliers for external frequency dividers
    scale = ["x1", "x2", "x4", "x8", "x16", "x32", "x64", "x128", "x256"]
    multiplier = 1
    use_internal_filter = False

    def __init__(self):
        super(MainWindow,self).__init__()
        self.setObjectName('MainWindow')

        # load language file
        self.langstr = load_section(self.appsettings.value("Lang",
                                    "translations/freqmeter_en"), 'freqmeter')

        self.initUI()
        self.setFixedSize(self.size() + QSize(0, 30))
        self.statusBar().showMessage(self.langstr[0])

        # configuration dialog
        self.configdlg = SerialSettingsDialog(self)
        self.configdlg.setModal(True)
        self.configdlg.dataReady.connect(self.configure_data)

        # help dialog
        if QLocale.system().name() == 'fr_FR':
            self.helpdlg = HelpDialog(parent=self,
                                      filename='resources/help_fr.txt')
            self.langstr = load_section('translations/freqmeter_fr_FR',
                                        'freqmeter')
        else:
            self.langstr = load_section('translations/freqmeter_en',
                                        'freqmeter')
            self.helpdlg = HelpDialog(parent=self,
                                      filename='resources/help.txt')

        # graph dialog
        self.graphdlg = GraphDialog()

        # language dialog
        self.langselectdlg = LangSelector()
        self.langselectdlg.lang_selected.connect(self.new_lang)

        # Create serial object
        self.serport = serial.Serial()

        # create thread for reading data from serial port
        self.Thread = DataThread(self)
        self.Thread.dataReady.connect(self.display_data)

    def initUI(self):
        """ Initialize widgets """
        # Create central widget for MainWindow
        self.widget = QWidget()
        self.grid = QGridLayout()
        self.widget.setLayout(self.grid)
        self.setCentralWidget(self.widget)

        # set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        self.myeditor = EditorDialog(self)

        # create menus
        self.exitAct = QAction(QIcon('resources/images/stop.png'),
                               self.langstr[1], self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip(self.langstr[2])
        self.exitAct.triggered.connect(self.close)

        self.configAct = QAction(QIcon('resources/images/properties.png'),
                                 self.langstr[3], self)
        self.configAct.setShortcut('Ctrl+S')
        self.configAct.setStatusTip(self.langstr[4])
        self.configAct.triggered.connect(self.configure)

        self.connectAct = QAction(QIcon('resources/images/start.png'),
                                  self.langstr[5], self)
        self.connectAct.setShortcut('Ctrl+C')
        self.connectAct.setStatusTip(self.langstr[6])
        self.connectAct.setEnabled(False)
        self.connectAct.triggered.connect(self.connect_serial)

        self.filterAct = QAction(self.langstr[34], self, checkable=True)
        self.filterAct.setChecked(self.appsettings.value("UseFilter", False,
                                                         type=bool))
        self.filterAct.triggered.connect(self.use_filter)

        self.editAct = QAction(
            QIcon.fromTheme('document-content'), self.langstr[35], self)
        self.editAct.triggered.connect(self.showedit)

        self.langAct = QAction(QIcon.fromTheme('document-language'),
                               self.langstr[32], self)
        self.langAct.triggered.connect(self.select_lang)

        self.aboutAct = QAction(QIcon('resources/images/help.png'),
                                self.langstr[7], self)
        self.aboutAct.setShortcut('Ctrl+A')
        self.aboutAct.setStatusTip(self.langstr[8])
        self.aboutAct.triggered.connect(self.about_app)

        self.helpAct = QAction(QIcon('resources/images/help.png'),
                               self.langstr[9], self)
        self.helpAct.setShortcut('Ctrl+H')
        self.helpAct.setStatusTip(self.langstr[10])
        self.helpAct.triggered.connect(self.help_app)

        # Create menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu(self.langstr[11])
        fileMenu.addAction(self.configAct)
        fileMenu.addAction(self.connectAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.filterAct)
        fileMenu.addAction(self.editAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.langAct)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAct)
        helpMenu = menubar.addMenu(self.langstr[9])
        helpMenu.addAction(self.helpAct)
        helpMenu.addAction(self.aboutAct)

        # Create radio buttons for speed and pack them
        self.fast = QRadioButton(self.langstr[12])
        self.fast.setEnabled(False)
        self.fast.toggled.connect(self.set_fast)

        self.slow = QRadioButton(self.langstr[13])
        self.slow.setEnabled(False)
        self.slow.setChecked(True)
        self.slow.toggled.connect(self.set_slow)

        self.hold = QCheckBox(self.langstr[14])
        self.hold.setEnabled(False)
        self.hold.toggled.connect(self.set_hold)

        self.vbox1 = QVBoxLayout()
        self.vbox1.addWidget(self.fast)
        self.vbox1.addWidget(self.slow)
        self.vbox1.addWidget(self.hold)

        self.unitbox = QGroupBox(self.langstr[15])
        self.unitbox.setAlignment(Qt.AlignCenter)
        self.unitbox.setLayout(self.vbox1)

        # Create graph and autorange buttons
        self.auto = QCheckBox(self.langstr[16])
        self.auto.setChecked(True)
        self.auto.setEnabled(False)
        self.auto.toggled.connect(self.auto_unit)

        self.graph = QPushButton(self.langstr[17])
        self.graph.clicked.connect(self.show_graph)
        self.graph.setEnabled(False)

        self.scale_combo = QComboBox()
        self.scale_combo.activated.connect(self.set_multiplier)
        for mult in self.scale:
            self.scale_combo.addItem(mult)

        self.scale_label = QLabel(self.langstr[33])

        self.scale_box = QHBoxLayout()
        self.scale_box.addWidget(self.scale_label)
        self.scale_box.addWidget(self.scale_combo)

        self.vbox2 = QVBoxLayout()
        self.vbox2.setAlignment(Qt.AlignTop)
        self.vbox2.addWidget(self.auto)
        self.vbox2.addWidget(self.graph)
        self.vbox2.addLayout(self.scale_box)

        self.probebox = QGroupBox(self.langstr[18])
        self.probebox.setAlignment(Qt.AlignCenter)
        self.probebox.setLayout(self.vbox2)

        # Create buttons for system tasks
        self.setBtn = QPushButton(self.langstr[19])
        self.setBtn.clicked.connect(self.configure)
        self.setBtn.setIcon(QIcon('resources/images/properties.png'))

        self.conBtn = QPushButton(self.langstr[30])
        self.conBtn.setIcon(QIcon('resources/images/start.png'))
        self.conBtn.setEnabled(False)
        self.conBtn.clicked.connect(self.connect_serial)

        self.exitBtn = QPushButton(self.langstr[20])
        self.exitBtn.setIcon(QIcon('resources/images/stop.png'))
        self.exitBtn.clicked.connect(self.close)

        self.vbox3 = QVBoxLayout()
        self.vbox3.addWidget(self.setBtn)
        self.vbox3.addWidget(self.conBtn)
        self.vbox3.addWidget(self.exitBtn)

        self.setbox = QGroupBox(self.langstr[21])
        self.setbox.setAlignment(Qt.AlignCenter)
        self.setbox.setLayout(self.vbox3)

        # labels to display data
        self.disp = QLabel('0')    
        self.disp.setAlignment(Qt.AlignRight)
        self.disp.setFont(QFont("Times", 20, QFont.Bold))
        self.disp.setStyleSheet("background-color:black;color:lightgreen")

        self.dispp = QLabel('0')    
        self.dispp.setAlignment(Qt.AlignRight)
        self.dispp.setFont(QFont("Times", 20, QFont.Bold))
        self.dispp.setStyleSheet("background-color:black;color:lightgreen")

        self.displayout = QHBoxLayout()
        self.displayout.addWidget(self.disp)
        self.dispplayout = QHBoxLayout()
        self.dispplayout.addWidget(self.dispp)        

        # label for units
        self.unitlabel = QLabel('Hz')
        self.unitlabel.setFont(QFont("Times", 16))
        self.unitlabel.setStyleSheet("background-color:black;color:lightgreen")
        self.displayout.addWidget(self.unitlabel)

        self.timelabel = QLabel('s')
        self.timelabel.setFont(QFont("Times", 16))
        self.timelabel.setStyleSheet("background-color:black;color:lightgreen")

        self.dispplayout.addWidget(self.timelabel)
        self.displayout.setAlignment(Qt.AlignRight)
        self.dispplayout.setAlignment(Qt.AlignRight)

        self.dispbox = QGroupBox(self.langstr[22])
        self.dispbox.setLayout(self.displayout)
        self.dispbox.setAlignment(Qt.AlignRight)
        self.dispbox.setStyleSheet("background-color:black;color:lightgreen")

        self.disppbox = QGroupBox(self.langstr[23])
        self.disppbox.setLayout(self.dispplayout)
        self.disppbox.setAlignment(Qt.AlignRight)
        self.disppbox.setStyleSheet("background-color:black;color:lightgreen")

        # Add all that stuff to MainWindow
        self.grid.addWidget(self.dispbox, 0, 0, 1, 3)
        self.grid.addWidget(self.disppbox, 1, 0, 1, 3)
        self.grid.addWidget(self.unitbox, 2, 0)
        self.grid.addWidget(self.probebox, 2, 1)
        self.grid.addWidget(self.setbox, 2, 2)
        # show window
        self.move(300, 150)
        self.setWindowTitle(self.langstr[24])
        self.show()

    def showedit(self):
        self.myeditor.show()
        self.myeditor.file_set('tools/datafilters.py')

    def use_filter(self):
        """ Menu->Edit->use filter callback """
        if self.filterAct.isChecked():
            self.use_internal_filter = True
        else:
            self.use_internal_filter = False
        self.appsettings.setValue("UseFilter", self.use_internal_filter)

    def set_multiplier(self, index):
        """ select frequency multiplier from combobox """
        self.multiplier = math.pow(2, index)

    def new_lang(self, langue):
        """ Save selected language """
        self.appsettings.setValue("Lang",
                                  f'translations/{langue[2].strip()}')
        QMessageBox.information(self, "Language", "Restart to change language")

    def select_lang(self):
        """ Show language dialog """
        self.langselectdlg.show()

    def closeEvent(self, event):
        """ Custom handler when user tries to close the window
            Closes ports if needed and exits properly
        """
        self.statusBar().showMessage(self.langstr[25])
        reply = QMessageBox.question(self, self.langstr[20], self.langstr[26],
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            if self.isConnected:
                self.serport.close()
                self.Thread.stop()
                self.Thread.terminate()
                self.graphdlg.close()
        else:
            event.ignore()
            self.statusBar().showMessage('')

    def show_graph(self):
        """ show graph window """
        self.graphdlg.setModal(False)
        self.graphdlg.show()

    def configure(self):
        """ Launch configuration dialog """
        self.configdlg.show()

    def configure_data(self,conflist):
        """ Get data from configuration dialog and parse it """
        # save a copy of settings list
        self.settingsList = conflist.copy()
        # conflist[0] is the exit status (ok = 1 or cancel = 0)
        if int(conflist[0]) and (conflist[1] != None and conflist[1] != ''):
            self.conBtn.setEnabled(True)
            self.connectAct.setEnabled(True)
        else:
            pass

    def set_fast(self):
        """ put arduino in fast reading mode """
        if self.isConnected:
            self.serport.write('f\n'.encode('ascii'))

    def set_slow(self):
        """ put arduino in slow reading mode """        
        if self.isConnected:
            self.serport.write('s\n'.encode('ascii'))

    def set_hold(self):
        """ hold the previous display """        
        if self.hold.checkState():
            self.holddata = True
        else:
            self.holddata = False

    def auto_unit(self):
        """ in auto mode we display hz, khz or Mhz,
            if false raw data (Hz) is displayed
        """
        if self.auto.checkState():
            self.autorange = True
        else:
            self.autorange = False

    def help_app(self):
        """ launch help dialog """
        self.helpdlg.show()

    def about_app(self):
        """ About dialog box """
        QMessageBox.about(self,'About',
                          "The poorman's frequency counter based on Arduino !!!\n\nCopyright 2020 Cedric Pereira\nReleased under GNU GPL license")

    def display_data(self, data):
        """ get data from thread (the data argument) and display it """

        if self.use_internal_filter:
            self.readvalue = filter(data)
        else:
            self.readvalue = data

        convertedval = data * self.multiplier

        if self.autorange:
            # MHz range
            if self.readvalue >= 1000000:
                convertedval = self.readvalue / 1000000
                self.unitlabel.setText('Mhz')
                self.timelabel.setText('µs')
            # KHz range
            elif self.readvalue >= 1000:
                convertedval = self.readvalue / 1000
                self.unitlabel.setText('Khz')
                self.timelabel.setText('ms')
            # Hz range
            else:
                convertedval = self.readvalue
                self.unitlabel.setText('Hz')
                self.timelabel.setText('s')
        # not in autorange mode
        else:
            convertedval = self.readvalue
            self.unitlabel.setText('Hz')
            self.timelabel.setText('s')
        # does thread  read real values ?
        if self.readvalue != -1:
            self.statusBar().showMessage(self.langstr[27])
            # not in hold mode
            if not self.holddata:
                if (convertedval != 0):
                    period = 1 / convertedval
                    self.dispp.setText(str('{:10.6f}').format(period))
                else:
                    self.dispp.setText('0')
                self.disp.setText(str('{:10.3f}').format(convertedval))
                self.graphdlg.update_data(self.readvalue)
        else:
            self.statusBar().showMessage(self.langstr[28])

    def connect_serial(self):
        """ Button conBtn clicked event handler
            Try to connect to selected serial port
        """
        # set serial configuration
        self.serport.port = self.settingsList[1]
        self.serport.baudrate = int(self.settingsList[2])
        self.serport.timeout = 1
        # not yet connected? -> try to connect
        if not self.isConnected:
            try:
                if not self.serport.isOpen():
                    self.serport.open()
                self.isConnected = True
                self.conBtn.setEnabled(False)
                self.setBtn.setEnabled(False)
                self.connectAct.setEnabled(False)
                self.configAct.setEnabled(False)
                self.fast.setEnabled(True)
                self.slow.setEnabled(True)
                self.hold.setEnabled(True)
                self.auto.setEnabled(True)
                self.graph.setEnabled(True)
                self.statusBar().showMessage(self.langstr[29].format(self.settingsList[1]), 1000)
                self.Thread.start()
            # something is wrong
            except serial.serialutil.SerialException:
                QMessageBox.about(self, 'Big mistake!',
                                  'Error opening port.\nPlease check your connections!!!')


class DataThread(QThread):
    """ Thread for reading serial data """

    # custom signal to return data
    dataReady = pyqtSignal(float)
    isOpen = True

    def __init__(self, parent=None):
        super(DataThread, self).__init__(parent)
        self.threadactive = True
        self.parent = parent

    def run(self):
        # self.threadactive = True
        while (self.threadactive):
            try:
                # read a string from serial and cast it to int
                self.values = float(self.parent.serport.readline().decode('ascii'))
                self.dataReady.emit(self.values) #envoi d'une valeur à afficher
            except (TypeError, ValueError) as e:
                self.dataReady.emit(-1)

    def stop(self):
        self.threadactive = False
        self.wait()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    locale = QLocale.system().name()
    appTranslator = QTranslator(app)
    if appTranslator.load('qt_' + locale,
                          QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(appTranslator)
    ex = MainWindow()
    sys.exit(app.exec_())
