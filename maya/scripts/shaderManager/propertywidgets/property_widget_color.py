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

      self.widget = QPushButton(self)
      self.widget.setFlat(True)
      self.widget.setAutoFillBackground(True)

      self.widget.clicked.connect(self.mayaColorPicker)
      self.layout().addWidget(self.widget)

      self.default = params["value"]
      self.default_color = QColor(self.default[0] * 255, self.default[1] * 255, self.default[2]* 255)
      self.ColorChanged(self.default_color)

   def ColorChanged(self, color):
      palette = QPalette()
      palette.setColor(QPalette.Button, color)
      self.widget.setPalette(palette)

   def mayaColorPicker(self):
      """"""
      cmds.colorEditor()
      if cmds.colorEditor(query=True, result=True):
         value = []
         values = cmds.colorEditor(query=True, rgb=True)

         value.append( values[0])
         value.append( values[1])
         value.append( values[2])

         if  self.colorType == PropertyWidget.RGBA:
            value.append( color.alphaF())
         self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=value == self.default, value=value))

         color = QColor(value[0]*255, value[1]*255, value[2]*255)
         self.ColorChanged(color)        

   def changed(self, message):
      value = message["value"]
      color = QColor(value[0]*255, value[1]*255, value[2]*255)
      self.ColorChanged(color)

   def resetValue(self):
      self.ColorChanged(self.default_color)


