# sys libs
import os

# pyside imports
from PySide2 import QtWidgets, QtGui, QtCore
import shiboken2

# maya / arnold
import maya.cmds as cmds
import maya.mel as mel
from maya.OpenMayaUI import MQtUtil

d = os.path.dirname(__file__)

class Shader(QtWidgets.QGroupBox):
    def __init__(self, shader_name, shader_widget):
        """
        Shader widget, group contains wrapped maya shader swatch widget and text label.
        """
        QtWidgets.QGroupBox.__init__(self)

        self.shader = shader_name

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(3, 0, 3, 0)

        self.label = QtWidgets.QLabel("%s" % shader_name)
        self.layout.addWidget(shader_widget)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.setMinimumHeight(38)
        self.setMinimumWidth(100)
        self.setMaximumHeight(38)
        self.setMaximumWidth(300)

    def renameShader(self, name):
        """Update the shader name label"""
        self.label.setText(name)
        self.shader = name

    def mouseMoveEvent(self, item):
        """Drag event"""

        shader = self.shader

        itemData = QtCore.QByteArray()
        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
        dataStream << QtCore.QByteArray(str(shader))

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-shader", itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        icon = QtGui.QIcon()
        icon.addFile(os.path.join(d, "../../../icons/sg.xpm"), QtCore.QSize(25,25))

        drag.setPixmap(icon.pixmap(50,50))
        drag.setHotSpot(QtCore.QPoint(0,0))
        drag.start(QtCore.Qt.MoveAction)

    def mousePressEvent(self, item):
        """Click event"""

        shader = self.shader
        if shader:
            if cmds.objExists(shader):
                try:
                    conn = cmds.connectionInfo(shader +".surfaceShader", sourceFromDestination=True)
                    if conn:
                        cmds.select(conn, r=1, ne=1)
                    else:
                        cmds.select(shader, r=1, ne=1)
                except:
                    cmds.select(shader, r=1, ne=1)

class ShadersDockWidget(QtWidgets.QWidget):
    def __init__(self, parent= None):
        """
        Shaders dock widget, with scroll area for shaders, buttons for render and refresh, plus filter box
        """
        super(ShadersDockWidget, self).__init__()
        self.parent = parent
         
        #Container Widget        
        widget = QtWidgets.QWidget()
        
        #Layout of Container Widget
        self.layout = QtWidgets.QVBoxLayout(self)
        self.shadersList = []

        self.btn_layout = QtWidgets.QHBoxLayout()
        self.render_btn = QtWidgets.QPushButton('')
        self.ipr_btn = QtWidgets.QPushButton('')
        self.filter = QtWidgets.QLineEdit()
        self.refresh_btn= QtWidgets.QPushButton('Refresh Manager')

        self.btn_layout.addWidget(self.filter)
        self.btn_layout.addWidget(self.render_btn)
        self.btn_layout.addWidget(self.ipr_btn)

        render_pixmap = QtGui.QPixmap(os.path.join(d, "../../../icons/rvRender.png"))
        ipr_pixmap = QtGui.QPixmap(os.path.join(d, "../../../icons/rvIprRender.png"))

        self.render_btn.setIcon(render_pixmap)
        self.render_btn.setIconSize(QtCore.QSize(32, 32))
        self.render_btn.setStyleSheet('QPushButton{border: 0px solid;}')
        self.ipr_btn.setIcon(ipr_pixmap)
        self.ipr_btn.setIconSize(QtCore.QSize(32, 32))
        self.ipr_btn.setStyleSheet('QPushButton{border: 0px solid;}')

        self.filter.textChanged.connect(self.filterShader)
        self.render_btn.clicked.connect(self.doRender)
        self.ipr_btn.clicked.connect(self.doIpr)
        self.refresh_btn.pressed.connect(self.parent.reset)

        self.update()
        widget.setLayout(self.layout)
 
        #Scroll Area Properties
        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
         
        #Scroll Area Layer add 
        self.vLayout = QtWidgets.QVBoxLayout(self)
        self.vLayout.addLayout(self.btn_layout)         
        self.vLayout.addWidget(scroll)
        self.vLayout.addWidget(self.refresh_btn)
        self.setLayout(self.vLayout)

    def doRender(self):
        """Execute render"""

        mel.eval("renderIntoNewWindow render;")

    def doIpr(self):
        """Execute ipr render"""

        mel.eval("IPRRenderIntoNewWindow;")

    def filterShader(self):
        """Filter event"""

        text = self.filter.text()
        for item in self.shadersList:

            item.setHidden(0)
            if text != "" and not text.lower() in item.label.text().lower():
                item.setHidden(1)

    def clearLayout(self, layout):
        """Clear a given layout"""

        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_shader(self, shader):
        """Wrap and return a maya material swatch as a QWidget"""

        port = cmds.swatchDisplayPort(sn=shader, widthHeight=[32, 32], width=32, height=32, renderSize=32, backgroundColor=[0,0,0])
        ptr = MQtUtil.findControl(port)
        qport = shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)
        qport.setFixedSize(32, 32)
        return qport

    def update(self, selected=None):
        """Update the layout with current shaders"""

        # this temp window and rowLayout are vital, failure to use them cause the hypershade to freeze when this widget had been created
        # the cmds.swatchDisplayPort command requires a maya layout to be established, not just a pyside layout
        temp = cmds.window()
        cmds.rowLayout()

        self.clearLayout(self.layout)
        self.shadersList = []

        shaders = cmds.ls(materials=True)
        if selected:
            shaders.append(selected)
        for shader in shaders:

            widget = self.get_shader(shader)

            grp_widget = Shader(shader, widget)
            self.shadersList.append(grp_widget)
            self.layout.addWidget(grp_widget)

        self.layout.addStretch()

    def addShader(self, shader):
        """From callback, add shader"""

        cmds.select(shader)
        sel = cmds.ls(sl=True)[0]
        self.update(selected=sel)

    def removeShader(self, shader):
        """From callback, remove shader"""

        self.update()

    def renameShader(self, oldName, newName):
        """Rename shader"""

        for shader in self.shadersList:
            if shader.label.text() == oldName:
                shader.renameShader(newName)
