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

class PropertyWidgetString(PropertyWidget):
   def __init__(self, controller, param, parent = None):
      PropertyWidget.__init__(self, param, parent)
      self.controller = controller
      self.paramName = param["name"]

      self.widget = QLineEdit(self)
      self.default = param["value"]
      self.default = ""

      self.widget.textEdited.connect(self.TextChanged)
      self.layout().addWidget(self.widget)

   def changed(self, val):
      self.TextChanged()

   def TextChanged(self):
      self.controller.mainEditor.propertyChanged(dict(propname=self.paramName, default=self.widget.text() == self.default, value=self.widget.text()))

   def __ReadFromArnold(self):
      value = AiNodeGetStr(self.node, self.paramName)
      self.widget.setText(value if value else '')

   def __WriteToArnold(self):
      AiNodeSetStr(self.node, self.paramName, str(self.widget.text()))

   def resetValue(self):
      self.widget.setText(self.default)
      self.TextChanged()
