# -*- coding: utf-8 -*-

"""

 Project     : The poorman's data logger.
 File        : tools/settingsdialogs.py
 Version     : 1.0
 Description : Dialogs to set serial communication settings
                and application settings.


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

import glob
import sys
import re
from PyQt5.QtCore import (Qt, pyqtSignal, QLocale, pyqtSlot, QSettings,
                          QRegularExpression)
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QGridLayout, QLabel,
                             QHBoxLayout, QCheckBox, QSpinBox, QPushButton,
                             QRadioButton, QLineEdit, QComboBox, QGroupBox,
                             QVBoxLayout, QAbstractButton, QMessageBox,
                             QDoubleSpinBox, QColorDialog, QVBoxLayout, QFrame)
from PyQt5.QtGui import (QIcon, QColor, QRegularExpressionValidator,
                         QIntValidator)
import serial
from tools.langtranslate import loadLanguage, load_section


class SerialSettingsDialog(QDialog):
    """ Dialog to configure a serial connection """

    baudvalues = ['9600', '19200', '38400', '57600', '115200', '230400']
    dataReady = pyqtSignal(list)
    appsettings = QSettings("C.E.D", "freqmeter")

    def __init__(self, parent=None):
        super(SerialSettingsDialog, self).__init__()

        # load translation
        self.langstr = load_section(self.appsettings.value('Lang', 'translations/freqmeter_en'), 'serial')
        self.setWindowTitle(self.langstr[0])
        self.setupUI()

    def setupUI(self):
        """ init widgets """
        # set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ports list
        self.combobox = QComboBox()
        self.combobox.clear()
        self.combobox.addItems(self.serial_ports())

        # rescan ports button
        self.scanBtn = QPushButton(self.langstr[1])
        self.scanBtn.clicked.connect(self.rescan)

        # baud rate
        self.baudbox = QComboBox()
        for bauds in self.baudvalues:
            self.baudbox.addItem(bauds)
        self.baudbox.setCurrentIndex(3)

        # ok and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        # some labels
        self.portlabel = QLabel("Port:")
        self.baudlabel = QLabel(self.langstr[2])
        self.bitslabel = QLabel(self.langstr[3])
        self.startlabel = QLabel(self.langstr[4])
        self.stoplabel = QLabel(self.langstr[5])

        # data bits
        self.dataspin = QSpinBox()
        self.dataspin.setValue(8)

        # parity combo
        self.parity = QComboBox()
        self.parity.addItems([self.langstr[6], self.langstr[7],
                             self.langstr[8]])

        # stop bits
        self.stopspin = QSpinBox()
        self.stopspin.setValue(1)

        # other serial stuff
        self.cts = QCheckBox('CTS')
        self.dtr = QCheckBox('DTR')
        self.xon = QCheckBox('XON')

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.portlayout = QHBoxLayout()
        self.portlayout.addWidget(self.portlabel)
        self.portlayout.addWidget(self.combobox)

        # put all the stuff together
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addWidget(self.baudlabel, 0, 1)
        self.grid.addWidget(self.bitslabel, 1, 1)
        self.grid.addWidget(self.startlabel, 2, 1)
        self.grid.addWidget(self.stoplabel, 3, 1)
        self.grid.addWidget(self.dataspin, 1, 2)
        self.grid.addWidget(self.parity, 2, 2)
        self.grid.addWidget(self.stopspin, 3, 2)
        self.grid.addWidget(self.cts, 4, 2)
        self.grid.addWidget(self.dtr, 5, 2)
        self.grid.addWidget(self.xon, 6, 2)
        self.grid.addWidget(self.baudbox, 0, 2)
        self.grid.addLayout(self.portlayout, 0, 0)
        self.grid.addWidget(self.scanBtn, 1, 0)
        self.grid.addWidget(self.line, 7, 0, 1, 3)
        self.grid.addWidget(self.buttonBox, 8, 2)

    def submit_data(self):
        """ Ok button pressed : let's send values back and exit"""
        vallist = [True, self.combobox.currentText(),
                   int(self.baudbox.currentText()), self.dataspin.value(),
                   self.parity.currentText(), self.stopspin.value(),
                   self.cts.isChecked(), self.dtr.isChecked(),
                   self.xon.isChecked()]
        self.dataReady.emit(vallist)
        self.accept()

    def reject_data(self):
        """ Cancel button pressed : let's send defaulf values and exit"""
        vallist = [False, self.combobox.currentText(),
                   int(self.baudbox.currentText()), self.dataspin.value(),
                   self.parity.currentText(), self.stopspin.value(),
                   self.cts.isChecked(), self.dtr.isChecked(),
                   self.xon.isChecked()]
        self.dataReady.emit(vallist)
        self.reject()

    def rescan(self):
        """ Test if new ports are available """
        # clear list then try to populate it
        self.combobox.clear()
        self.combobox.addItems(self.serial_ports())

    @staticmethod
    def serial_ports():
        """ Get a list of available serial ports """

        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith(
                    'cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result



class LangSelector(QDialog):
    """
    Select a language from the translations directory
    """
    lang_selected = pyqtSignal(list)
    lang_data = []

    def __init__(self, parent=None):
        super(LangSelector, self).__init__()

        self.setWindowTitle('Preferences')
        self.setupUI()
        self.populate_lang()

    def setupUI(self):
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        self.lang_label = QLabel("Select a language")

        self.lang_list = QComboBox()

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.lang_label)
        self.vlayout.addWidget(self.lang_list)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.grid = QGridLayout()
        self.setLayout(self.grid)
        self.grid.addLayout(self.vlayout, 0, 0)
        self.grid.addWidget(self.line, 1, 0, 1,2)
        self.grid.addWidget(self.buttonBox, 2, 1)

    def populate_lang(self):
        try:
            with open("translations/lang.idx", "r") as reader:
                for line in reader:
                    name = line.split(",")
                    self.lang_data.append(name)
                    self.lang_list.addItem(name[0])

        except FileNotFoundError:
            self.lang_label.setText("No language index file found !")
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def submit_data(self):
        self.lang_selected.emit(self.lang_data[self.lang_list.currentIndex()])
        self.accept()

    def reject_data(self):
        self.reject()


class TCPConfigDialog(QDialog):
    """
    Configure an ip address and port number with validation
    arguments:
        adr=xxx.yyy.ttt.ddd
        port=integer
    """
    # Qt signal used to tranfer data
    ip_config = pyqtSignal(list)

    def __init__(self, parent=None, adr="", port=0):
        super(TCPConfigDialog, self).__init__()

        self.ip_adr = adr
        self.portnb = port

        self.setWindowTitle('TCP configuration')
        self.setupUI()

    def setupUI(self):
        self.setWindowIcon(QIcon('resources/images/icon.png'))

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.submit_data)
        self.buttonBox.rejected.connect(self.reject_data)

        # Labels
        self.dialog_label = QLabel("Configure Ip settings")
        self.ip_label = QLabel("Ip address:")
        self.port_label = QLabel("Port :    ")

        # input for ip address
        self.ip_text = QLineEdit()
        # Part of the regular expression for validating ip address
        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        # Regular expression
        ipRegex = QRegularExpression("^" + ipRange + "\\." + ipRange + "\\."
                                     + ipRange + "\\." + ipRange + "$")
        # regex object to validate address
        self.pattern = re.compile("^" + ipRange + "\\." + ipRange + "\\."
                                      + ipRange + "\\." + ipRange + "$")
        ipValidator = QRegularExpressionValidator(ipRegex, self)   
        self.ip_text.setValidator(ipValidator)
        # an adress was passed as an argument
        if self.ip_adr != "":
            self.ip_text.setText(self.ip_adr)

        # input for port number
        self.port_text = QLineEdit()
        # only accepts integers !
        self.onlyints = QIntValidator()
        self.port_text.setValidator(self.onlyints)
        # a port number  was passed as an argument
        if self.portnb != 0:
            self.port_text.setText(str(self.portnb))
        # add stuff to layout
        self.grid = QGridLayout()
        self.grid.addWidget(self.dialog_label, 0, 0, 1, 2, Qt.AlignCenter)
        self.grid.addWidget(self.ip_label, 1, 0)
        self.grid.addWidget(self.port_label, 2, 0)
        self.grid.addWidget(self.ip_text, 1, 1)
        self.grid.addWidget(self.port_text,2, 1)
        self.grid.addWidget(self.buttonBox, 3, 1)
        self.setLayout(self.grid)

    def submit_data(self):
        """ Ok button pressed """

        # validate ip adress
        if not self.pattern.match(self.ip_text.text()):
            QMessageBox.information(self, "Info",
                                    "Not a valid ip address!")
            return
        # validate port number
        try:
            configuration = [1, self.ip_text.text(), int(self.port_text.text())]
        except ValueError:
            QMessageBox.information(self, "Info",
                                    "Please enter a valid port number!")
            return
        # emit signal if everything is ok
        self.ip_config.emit(configuration)
        self.accept()

    def reject_data(self):
        """ Cancel button pressed """
        configuration = [0]
        self.ip_config.emit(configuration)
        self.reject()
