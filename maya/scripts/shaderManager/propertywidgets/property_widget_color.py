# Alembic Holder
# Copyright (c) 2014, Gael Honorez, All rights reserved.
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from arnold import *
from property_widget import *
import maya.cmds as cmds

class PropertyWidgetColor(PropertyWidget):
   def __init__(self, controller,  params, colorType, parent = None):
      PropertyWidget.__init__(self, params, parent)

      self.paramName = params["name"]
      self.colorType = colorType
      self.controller = controller

      self.fileNodesCombo = QComboBox()
      self.colorBtn = QPushButton("")
      self.colorBtn.setAutoFillBackground(True)

      self.colorBtn.clicked.connect(self.mayaColorPicker)
      self.fileNodesCombo.currentIndexChanged.connect(self.fileComboChanged)

      self.layout().addWidget(self.fileNodesCombo)
      self.layout().addWidget(self.colorBtn)

      # if the color param of light node isnt set, it's black, which isnt the default
      # value of the an actual color param, it's just that there isnt that param there at all
      self.default = [0.0, 0.0, 0.0]
      self.default_color = QColor(self.default[0] * 255, self.default[1] * 255, self.default[2]* 255)
      self.updatePalette(self.default_color)

      # the color palete we store in memory if the user choose a file node
      self.suspended_color = None
      self.fillFileNodesCombo()

   def fileComboChanged(self, index):
      """The combo box has been changed"""
      if self.fileNodesCombo.currentText() == 'RGB':
         # restore the color button and the suspended_color
         self.colorBtn.setEnabled(True)
         if self.suspended_color:
            self.colorBtn.setPalette(self.suspended_color)
      else:
         # reset the color button
         self.updatePalette(self.default_color)
         self.colorBtn.setEnabled(False)
         self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=False, value=self.fileNodesCombo.currentText()))

         fileNode = cmds.ls("%s" % self.fileNodesCombo.currentText(), textures=True)[0]

         for k in self.controller.mainEditor.ABCViewerNode.keys():
            ports_in_use = 0
            for c in cmds.listConnections("%s" % k):
               if cmds.getClassification(cmds.nodeType(c), satisfies="shader") or cmds.nodeType(c) == 'file':
                  ports_in_use += 1

            found = False
            for each in range(0, ports_in_use):
               if cmds.isConnected("%s.message" % fileNode, "%s.shaders[%i]" % (k, each)):
                  found = True
            if not found:
               cmds.connectAttr( "%s.message" % fileNode, "%s.shaders[%i]" % (k, ports_in_use + 1))

   def fillFileNodesCombo(self):
      """Populate the combo box with maya texture nodes"""
      nodes = ['RGB'] + cmds.ls( textures=True )
      self.fileNodesCombo.addItems(nodes)

   def updatePalette(self, color):
      """Update button palette with given QColor"""
      palette = QPalette()
      palette.setColor(QPalette.Button, color)
      self.colorBtn.setPalette(palette)

   def mayaColorPicker(self):
      """Open maya color picker"""
      cmds.colorEditor()
      if cmds.colorEditor(query=True, result=True):
         value = []
         values = cmds.colorEditor(query=True, rgb=True)
         value.append( values[0])
         value.append( values[1])
         value.append( values[2])
         
         if self.colorType == PropertyWidget.RGBA:
            value.append( color.alphaF())

         self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=False, value=value))
         color = QColor(value[0]*255, value[1]*255, value[2]*255)
         self.updatePalette(color)
         self.suspended_color = self.colorBtn.palette()

   def changed(self, message):
      """Change color"""
      value = message["value"]
      if isinstance(value, list):
         color = QColor(value[0]*255, value[1]*255, value[2]*255)
         self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=False, value=value))
         self.updatePalette(color)

      if isinstance(value, str):
         self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=False, value=value))
         index = self.fileNodesCombo.findText(value, Qt.MatchFixedString)
         print index
         if index > 0:
            self.fileNodesCombo.setCurrentIndex(index)

   def resetValue(self):
      """Reset color"""
      self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=False, value=self.default))
      self.updatePalette(self.default_color)
      index = self.fileNodesCombo.findText('RGB', Qt.MatchFixedString)
      self.fileNodesCombo.setCurrentIndex(0)
