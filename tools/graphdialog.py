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
 File        : tools/graphdialog.py
 Version     : 1.0
 Description : Dialog window displaying data as a graph.



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

from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import (QWidget, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QApplication,
                             QFrame, QCheckBox)
from PyQt5.QtCore import QTimer
import numpy as np
import pyqtgraph as pg
from PyQt5.QtGui import QIcon, QPixmap
import os

class GraphDialog(QDialog):
    """ This class displays a dialog box with a graph """
    
    # array to store incoming data (120 samples = 120s in slow mode or 12s in fast mode)
    data = np.zeros((120,))
     
    def __init__(self, parent=None):
        super(GraphDialog,self).__init__()
        self.setWindowTitle('Plot')
        self.setupUI()
        self.setFixedSize(self.size())
        self.create_graphs()
        
    def setupUI(self):
        """ init all widgets """
        
        ## set window icon
        self.setWindowIcon(QIcon('resources/images/icon.png'))
        
        ## layout for dialog
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.btnlayout = QHBoxLayout()
        
        ## add buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.buttonBox.rejected.connect(self.reject)
        self.xaxisgrid = QCheckBox('X Grid')
        self.xaxisgrid.setChecked(True)
        self.yaxisgrid = QCheckBox('Y Grid')
        self.yaxisgrid.setChecked(True)
        self.yaxislog = QCheckBox('Y Log')
        self.yaxisgrid.toggled.connect(self.set_axis_grid)
        self.xaxisgrid.toggled.connect(self.set_axis_grid)
        self.yaxislog.toggled.connect(self.set_axis_log)
        ## pack them horizontally
        self.btnlayout.addWidget(self.xaxisgrid)
        self.btnlayout.addWidget(self.yaxisgrid)
        self.btnlayout.addWidget(self.yaxislog)
        self.btnlayout.addWidget(self.buttonBox)
        
        ## create a PlotWidget from pyqtgraph
        self.pw = pg.PlotWidget()
        self.pw.setLabel('left','Frequency', 'Hz')
        self.pw.setLabel('bottom','Samples')
        self.pw.showGrid(True, True)
        
        ## using a frame as an horizontal line separator
        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        
        # add all the stuff to layout
        self.layout.addWidget(self.pw)
        self.layout.addWidget(self.line)
        self.layout.addLayout(self.btnlayout)
        
    def create_graphs(self):
        """ create a new plot inside the PlotWidget """
        self.p1 = self.pw.plot()        # create a new plot and set color to green
        self.p1.setPen((100,200,100))
        
    def update_data(self,value):
        """ setter called by parent window to update the display"""  
        self.data[:-1] = self.data[1:]  # shift data in the array one sample left
        self.data[-1] = value           # add new value
        self.p1.setData(self.data)      # update display
        
    def set_axis_log(self):
        """ set log display mode on vertical axis """
        if self.yaxislog.checkState():
            self.pw.setLogMode(False, True)
        else:
            self.pw.setLogMode(False, False)
    
    def set_axis_grid(self):
        """ display horizontal an vertical grids """
        xaxis = False
        yaxis = False
        
        if self.xaxisgrid.checkState():
            xaxis = True      
        if self.yaxisgrid.checkState():
            yaxis = True   
        self.pw.showGrid(xaxis, yaxis)