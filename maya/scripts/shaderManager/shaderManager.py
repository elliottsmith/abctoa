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


import os

d = os.path.dirname(__file__)

import json
from arnold import *

from PySide2 import QtWidgets, QtGui, QtCore
import shiboken2

from gpucache import gpucache, treeitem, treeDelegate, treeitemWildcard, treeitemTag
reload(treeitem)
reload(treeitemWildcard)
reload(treeitemTag)
reload(treeDelegate)
reload(gpucache)

from propertywidgets import property_editorByType
reload(property_editorByType)
from propertywidgets.property_editorByType import PropertyEditor

from ui import UI_ABCHierarchy
reload(UI_ABCHierarchy)

import maya.cmds as cmds
import maya.mel as mel
from maya.OpenMaya import MObjectHandle, MDGMessage, MMessage, MNodeMessage, MFnDependencyNode, MObject, MSceneMessage
from maya.OpenMayaUI import MQtUtil 

class Shader(QtWidgets.QGroupBox):
    def __init__(self, shader_name, shader_widget):
        """Shader Widget"""
        QtWidgets.QGroupBox.__init__(self)

        self.shader = shader_name

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(3, 0, 3, 0)

        self.label = QtWidgets.QLabel("%s" % shader_name)
        self.layout.addWidget(shader_widget)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.setMinimumHeight(38)
        self.setMinimumWidth(240)
        self.setMaximumHeight(38)

    def renameShader(self, name):
        """Update the shader name label"""
        self.label.setText(name)

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
        icon.addFile(os.path.join(d, "../../icons/sg.xpm"), QtCore.QSize(25,25))

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

class ShadersScrollWidget(QtWidgets.QWidget):
     
    def __init__(self, parent= None):
        super(ShadersScrollWidget, self).__init__()
        self.setMinimumWidth(300)
         
        #Container Widget        
        widget = QtWidgets.QWidget()
        paneLayoutName = cmds.rowLayout() #required even though we never use it
        
        #Layout of Container Widget
        self.layout = QtWidgets.QVBoxLayout(self)
        self.update()
        widget.setLayout(self.layout)
 
        #Scroll Area Properties
        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setWidget(widget)
         
        #Scroll Area Layer add 
        self.vLayout = QtWidgets.QVBoxLayout(self)
        self.vLayout.addWidget(scroll)
        self.setLayout(self.vLayout)

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
        return qport

    def update(self):
        """Update the layout with current shaders"""
        # print 'Updating Shaders'
        paneLayoutName = cmds.rowLayout() #required even though we never use it
        self.clearLayout(self.layout)

        shaders = cmds.ls(materials=True)
        for shader in shaders:

            widget = self.get_shader(shader)
            widget.setFixedSize(32, 32)

            grp_widget = Shader(shader, widget)
            self.layout.addWidget(grp_widget)

        self.layout.addStretch() 

class ShaderManager(QtWidgets.QMainWindow, UI_ABCHierarchy.Ui_NAM):
    def __init__(self, parent=None):
        super(ShaderManager, self).__init__(parent)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)        

        self.setupUi(self)

        self.shadersFromFile = []
        self.displaceFromFile = []

        self.curLayer = None
        self.shaderToAssign = None
        self.ABCViewerNode = {}

        self.getNode()
        self.getCache()

        self.thisTagItem = None
        self.thisTreeItem = None

        self.lastClick = -1

        self.propertyEditing = False

        self.propertyEditorWindow = QtWidgets.QDockWidget(self)
        self.propertyEditorWindow.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.propertyEditorWindow.setWindowTitle("Properties")
        self.propertyEditorWindow.setMinimumWidth(300)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.propertyEditorWindow)
        self.propertyType = "polymesh"
        self.propertyEditor = PropertyEditor(self, self.propertyType, self.propertyEditorWindow)
        self.propertyEditorWindow.setWidget(self.propertyEditor)


        self.propertyEditor.propertyChanged.connect(self.propertyChanged)

        self.hierarchyWidget.setColumnWidth(0,600)
        self.hierarchyWidget.setIconSize(QtCore.QSize(22,22))

        self.hierarchyWidget.dragEnterEvent = self.newhierarchyWidgetdragEnterEvent
        self.hierarchyWidget.dragMoveEvent = self.newhierarchyWidgetdragMoveEvent
        self.hierarchyWidget.dropEvent = self.newhierarchyWidgetDropEvent

        self.hierarchyWidget.setColumnWidth(0,200)
        self.hierarchyWidget.setColumnWidth(1,300)
        self.hierarchyWidget.setColumnWidth(2,300)

        self.hierarchyWidget.setItemDelegate(treeDelegate.treeDelegate(self))

        self.updateTags()
        self.populate()
        

        self.curPath = ""
        self.ABCcurPath = ""

        self.shaders = ShadersScrollWidget()
        self.verticalLayout.addWidget(self.shaders)

        self.hierarchyWidget.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.hierarchyWidget.itemExpanded.connect(self.requireItemExpanded)
        self.hierarchyWidget.itemCollapsed.connect(self.requireItemCollapse)
        self.hierarchyWidget.itemClicked.connect(self.itemCLicked)
        self.hierarchyWidget.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.hierarchyWidget.itemPressed.connect(self.itemPressed)
        self.hierarchyWidget.setExpandsOnDoubleClick(False)

        self.render.clicked.connect(self.doRender)
        self.refreshManagerBtn.pressed.connect(self.reset)

        self.getLayers()
        self.setCurrentLayer()
        
        self.addCBs()

        self.afterNewSceneCBId = MSceneMessage.addCallback(MSceneMessage.kAfterNew, self.reset)
        self.afterOpenSceneCBId = MSceneMessage.addCallback(MSceneMessage.kAfterOpen, self.reset)

        self.disableLayerOverrides()

        self.overrideDisps.stateChanged.connect(self.overrideDispsChanged)
        self.overrideShaders.stateChanged.connect(self.overrideShadersChanged)
        self.overrideProps.stateChanged.connect(self.overridePropsChanged)

        self.isolateCheckbox.stateChanged.connect(self.isolateCheckboxChanged)

        #Widcard management
        self.wildCardButton.pressed.connect(self.addWildCard)

        # render buttons
        render_pixmap = QtGui.QPixmap(os.path.join(d, "../../icons/rvRender.png"))
        self.render.setIcon(render_pixmap)
        self.render.setIconSize(QtCore.QSize(32, 32))
        self.render.setStyleSheet('QPushButton{border: 0px solid;}')

    def doRender(self):
        """"""
        mel.eval("renderIntoNewWindow render;")

    def showEvent(self, event):
        self.reset()
        self.isolateCheckbox.setChecked(0)
        self.shaders.update()

        return QtWidgets.QMainWindow.showEvent(self, event)
   
    def hideEvent(self, event):
        self.reset()
        self.isolateCheckbox.setChecked(0)
        return QtWidgets.QMainWindow.hideEvent(self, event)

    def reset(self, *args, **kwargs):
        try:
            self.renderLayer.currentIndexChanged.disconnect()
        except:
            pass

        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        self.hierarchyWidget.clear()
        self.propertyEditor.resetToDefault()

        self.curPath = ""
        self.ABCcurPath = ""        
        
        self.shadersFromFile = []
        self.displaceFromFile = []
        self.ABCViewerNode = {}
        self.curLayer = None

        self.getLayers()
        self.setCurrentLayer()

        self.shaderToAssign = None

        self.tags = {}
        self.getNode()
        self.getCache()   
        self.updateTags()
        self.populate()
        self.thisTagItem = None
        self.thisTreeItem = None

        self.lastClick = -1

        self.propertyEditing = False    

        self.renderLayer.currentIndexChanged.connect(self.layerChanged)
        self.propertyEditor.propertyChanged.connect(self.propertyChanged)

    def isolateCheckboxChanged(self, state):
        ''' activate/desactive isolation'''
        if state == 0:
            for cache in self.ABCViewerNode.values():
                cache.setToPath("")

        else:
            for cache in self.ABCViewerNode.values():
                cache.setToPath(cache.getSelection())            

    def overrideDispsChanged(self, state):
        result = True
        if state == 0:
            result = False


        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedDisplace(self.getLayer(), result)

        self.updateTree()

    def overrideShadersChanged(self, state):

        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedShader(self.getLayer(), result)

        self.updateTree()


    def overridePropsChanged(self, state):
        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedProperties(self.getLayer(), result)

        self.updateTree()

    def createSG(self, node):
        sg = None

        SGs = cmds.listConnections( node, d=True, s=False, type="shadingEngine")        
        if not SGs:
            try:
                sg = cmds.shadingNode("shadingEngine", n="%sSG" % node, asRendering=True)
                cmds.connectAttr("%s.outColor" % node, "%s.surfaceShader" % sg, force=True)
                return sg
            except:
                print "Error creating shading group for node", node
        else:
            return SGs[0]
        
    def nameChangedCB(self, node, prevName, client):
        ''' Callback when a node is renamed '''

        if prevName == "" or not prevName or prevName.startswith("_"):
            return
        handle = MObjectHandle( node )
        if not handle.isValid():
            return
        mobject = handle.object()

        nodeFn = MFnDependencyNode ( mobject )
        if nodeFn.hasUniqueName():
            nodeName = nodeFn.name()
            if not cmds.objExists(nodeName):
                return

            # shader manager is open
            if self.ABCViewerNode != {}:

                if cmds.nodeType(nodeName) == "shadingEngine" or cmds.nodeType(nodeName).startswith("ai"):
                    # renaming shaders in caches
                    for cache in self.ABCViewerNode.values():
                        cache.renameShader(prevName, nodeName)
                    self.checkShaders()
                    self.shaders.update()

            # shader manager isnt open, update the attributes directly
            else:
                alembicHolders = cmds.ls(dag=True, leaf=True, visible=True, type='alembicHolder', l=True)

                if cmds.nodeType(nodeName) == "shadingEngine" or cmds.nodeType(nodeName).startswith("ai"):

                    for holder in alembicHolders:
                        shader_assignments = cmds.getAttr('%s.shadersAssignation' % holder)

                        if shader_assignments:
                            j = json.loads(shader_assignments)
                            for shader in j.keys():
                                
                                if shader == prevName:
                                    j[nodeName] = j[shader]
                                    del j[shader]

                            cmds.setAttr('%s.shadersAssignation' % holder, json.dumps(j), type='string')

    def newNodeCB(self, newNode, data ):
        ''' Callback when creating a new node '''
        self.shaders.update()

    def delNodeCB(self, node, data ):
        ''' Callback when a node has been deleted '''

        mobject = MObjectHandle( node ).object()
        nodeFn = MFnDependencyNode ( mobject )
        if nodeFn.hasUniqueName():
            nodeName = nodeFn.name()
            didSomething = False

            # remove shaders from caches
            for cache in self.ABCViewerNode.values():
                didSomething = True
                cache.removeShader(nodeName)                
            
            if didSomething:
                self.shaders.update()
                self.checkShaders()

    def newshadersListmouseMoveEvent(self, event):
        self.newshadersListStartDrag(event)

    def newdisplaceListmouseMoveEvent(self, event):
        self.newdisplaceListStartDrag(event)

    def newshadersListStartDrag(self, event):
        index = self.shadersList.indexAt(event.pos())
        if not index.isValid():
            return
        selected = self.shadersList.itemFromIndex(index)

        self.shaderCLicked(selected)

        itemData = QtCore.QByteArray()
        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.WriteOnly)
        dataStream << QtCore.QByteArray(str(selected.text()))

        mimeData = QtCore.QMimeData()
        mimeData.setData("application/x-shader", itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        drag.setPixmap(self.shadersList.itemAt(event.pos()).icon().pixmap(50,50))
        drag.setHotSpot(QtCore.QPoint(0,0))
        drag.start(QtCore.Qt.MoveAction)

    def newhierarchyWidgetdragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetdragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetDropEvent(self, event):
        mime = event.mimeData()
        itemData = None
        mode = 0
        
        if mime.hasFormat("application/x-shader"):
            mode = 0
            itemData = mime.data("application/x-shader")
        elif mime.hasFormat("application/x-displacement"):
            mode = 1
            itemData = mime.data("application/x-displacement")

        dataStream = QtCore.QDataStream(itemData, QtCore.QIODevice.ReadOnly)

        shader = QtCore.QByteArray()
        dataStream >> shader

        shader = str(shader)
        items = []
        
        selectedItems = self.hierarchyWidget.selectedItems()

        item = self.hierarchyWidget.itemFromIndex(self.hierarchyWidget.indexAt(event.pos()))
        if item:
            items.append(item)

        if len(selectedItems) > 1:
            items = items + selectedItems

        for item in items:
            item.shaderToAssign = shader
            if mode == 0:
                item.assignShader()
            elif mode == 1:
                item.assignDisplacement()
               
        event.accept()

    def addCBs(self, event=None):
        try:
            self.renderLayer.currentIndexChanged.connect(self.layerChanged)
            self.NodeNameMsgId  = MNodeMessage.addNameChangedCallback( MObject(), self.nameChangedCB )
            self.newNodeCBMsgId = MDGMessage.addNodeAddedCallback( self.newNodeCB )
            self.delNodeCBMsgId = MDGMessage.addNodeRemovedCallback( self.delNodeCB )
            self.layerChangedJob = cmds.scriptJob( e= ["renderLayerManagerChange",self.setCurrentLayer])
        except:
            pass

    def clearCBs(self, event=None):
        try:
            cmds.scriptJob( kill=self.layerChangedJob, force=True)
            for cache in self.ABCViewerNode.values():
                cache.setSelection("")
            MMessage.removeCallback( self.newNodeCBMsgId )
            MMessage.removeCallback( self.delNodeCBMsgId )
            MNodeMessage.removeCallback( self.NodeNameMsgId )
        except:
            pass


    def closeEvent(self, event):
        event.ignore()
        self.hide()
        return

    def clearing(self):
        self.clearCBs()
        try:
            MMessage.removeCallback( self.afterNewSceneCBId )
            MMessage.removeCallback( self.afterOpenSceneCBId )
        except:
            pass


    def setCurrentLayer(self):
        try:
            curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
        except:
            return
        curLayeridx = self.renderLayer.findText(curLayer)
        if curLayeridx != -1:
            self.renderLayer.setCurrentIndex(curLayeridx)
        self.curLayer = curLayer


    def layerChanged(self, index):


        self.curLayer = self.renderLayer.itemText(index)
        if self.curLayer == "defaultRenderLayer":
            self.disableLayerOverrides()
        else:
            self.enableLayerOverrides()
            for cache in self.ABCViewerNode:
                c = self.ABCViewerNode[cache]
                over = c.getLayerOverrides(self.getLayer())

                if over:
                    self.overrideProps.setChecked(over["removeProperties"])
                    self.overrideShaders.setChecked(over["removeShaders"])
                    self.overrideDisps.setChecked(over["removeDisplacements"])


        self.updateTree()
        if self.hierarchyWidget.currentItem():
            self.itemCLicked(self.hierarchyWidget.currentItem(), 0, force=True)

        # change it in maya too
        curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
        if curLayer != self.curLayer:
            cmds.editRenderLayerGlobals( currentRenderLayer=self.curLayer)



    def updateTree(self):
        items = []
        for i in range(self.hierarchyWidget.topLevelItemCount()):
            self.visitTree(items, self.hierarchyWidget.topLevelItem(i))

        for item in items:
            item.removeAssigns()
            item.checkShaders(self.getLayer())
            item.checkProperties(self.getLayer())


    def visitTree(self, items, treeitem):
        items.append(treeitem)
        for i in range(treeitem.childCount()):
            self.visitTree(items, treeitem.child(i))


    def enableLayerOverrides(self):
        self.overrideDisps.setEnabled(1)
        self.overrideShaders.setEnabled(1)
        self.overrideProps.setEnabled(1)


        self.overrideDisps.setChecked(0)
        self.overrideShaders.setChecked(0)
        self.overrideProps.setChecked(0)


    def disableLayerOverrides(self):
        self.overrideDisps.setEnabled(0)
        self.overrideShaders.setEnabled(0)
        self.overrideProps.setEnabled(0)

        self.overrideDisps.setChecked(0)
        self.overrideShaders.setChecked(0)
        self.overrideProps.setChecked(0)


    def getLayers(self):
        self.renderLayer.clear()
        renderLayers = []
        for layer in cmds.ls(type="renderLayer"):
            con = cmds.connectionInfo(layer + ".identification", sourceFromDestination=True)
            if con:
                if con.split(".")[0] == "renderLayerManager":
                    renderLayers.append(layer)

        self.renderLayer.addItems(renderLayers)
        idx = self.renderLayer.findText("defaultRenderLayer")
        if idx == -1:
            self.curLayer = self.renderLayer.itemText(0)
        else:
            self.curLayer = self.renderLayer.itemText(idx)
            self.renderLayer.setCurrentIndex(idx)

    def propertyChanged(self, prop):
        if self.propertyEditing:
            return
        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        propName = prop["propname"]
        default = prop["default"]
        value = prop["value"]

        if self.lastClick == 1:

            item = self.hierarchyWidget.currentItem()
            if item:
                curPath = item.getPath()
                if curPath is None:
                    return
            else:
                return

            cache = item.cache
            layer = self.getLayer()
            cache.updateOverride(propName, default, value, curPath, layer)
            self.updatePropertyColor(cache, layer, propName, curPath)

            self.checkProperties(self.getLayer(), item=item)

        elif self.lastClick == 2:
            item = self.listTagsWidget.currentItem()
            item.assignProperty(propName, default, value)


        self.propertyEditor.propertyChanged.connect(self.propertyChanged)


    def updatePropertyColor(self, cache, layer, propName, curPath):
        cacheState = cache.getPropertyState(layer, propName, curPath)
        if cacheState == 3:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='darkRed'>%s</font>" % propName)
        if cacheState == 2:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='red'>%s</font>" % propName)
        if cacheState == 1:
            self.propertyEditor.propertyWidgets[propName].title.setText("<font color='white'><i>%s</i></font>" % propName)
        if cacheState == 0:
            self.propertyEditor.propertyWidgets[propName].title.setText("%s" % propName)

    def getLayer(self):
        if self.curLayer != "defaultRenderLayer":
            return self.curLayer
        return None

    def itemCLicked(self, item, col, force=False) :
        self.propertyEditing = True
        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        if item.icon == 7 and self.propertyType != "points":
            self.propertyType = "points"
            self.propertyEditor.resetTo(item.itemType.lower())

        if item.icon == 9 and self.propertyType != "curves":
            self.propertyType = "curves"
            self.propertyEditor.resetTo(item.itemType.lower())

        elif item.icon == 8 and self.propertyType != item.itemType:
            self.propertyType = item.itemType
            if item.itemType == "PointLight":
                self.propertyEditor.resetTo("point_light")

            elif item.itemType == "DistantLight":
                self.propertyEditor.resetTo("distant_light")

            elif item.itemType == "SpotLight":
                self.propertyEditor.resetTo("spot_light")

            elif item.itemType == "QuadLight":
                self.propertyEditor.resetTo("quad_light")                
            
            elif item.itemType == "PhotometricLight":
                self.propertyEditor.resetTo("photometric_light")                                

            elif item.itemType == "DiskLight":
                self.propertyEditor.resetTo("disk_light")

            elif item.itemType == "CylinderLight":
                self.propertyEditor.resetTo("cylinder_light")

        elif (item.icon == 1 or item.icon == 2) and self.propertyType != "polymesh":
            self.propertyType = "polymesh"
            self.propertyEditor.resetTo("polymesh")


        self.lastClick = 1

        if self.thisTreeItem is item and force==False:
            self.propertyEditing = False
            return
        self.thisTreeItem = item

        curPath = item.getPath()
        cache = item.cache

        allSelected = []
        for item in self.hierarchyWidget.selectedItems():
            if item.isTag == False and item.isWildCard == False:
                allSelected.append(item.getPath())

        if "/" in allSelected:
            allSelected = []

        cache.setSelection(allSelected)

        if self.isolateCheckbox.checkState() == QtCore.Qt.Checked:
            cache.setToPath(curPath)

        self.propertyEditor.resetToDefault()

        self.updateAttributeEditor()

        self.propertyEditing = False

        

    def updateAttributeEditor(self):
        ''' this will update what is inside the attribute editor (red text,....)'''

        try:
            self.propertyEditor.propertyChanged.disconnect()
        except:
            pass

        for item in self.hierarchyWidget.selectedItems():
            curPath = item.getPath()
            cache = item.cache
            layer = self.getLayer()
            attributes = {}

            if layer:
                layerOverrides = cache.getAssignations().getLayerOverrides(layer)
                if not layerOverrides:
                    layerOverrides = dict(removeDisplacements=False, removeProperties=False, removeShaders=False)

                if layerOverrides["removeProperties"] == False:
                    attributes = cache.getAssignations().getOverrides(curPath, layer)
                else:
                    attributes = cache.getAssignations().getOverrides(curPath, None)

            else:
                attributes = cache.getAssignations().getOverrides(curPath, None)


            if len(attributes) > 0 :
                for propname in attributes:
                    value = attributes[propname].get("override") 
                    self.propertyEditor.propertyValue(dict(paramname=propname, value=value))

                    if propname in self.propertyEditor.propertyWidgets :
                        self.updatePropertyColor(cache, layer, propname, curPath)

        try:            
            self.propertyEditor.propertyChanged.connect(self.propertyChanged)
        except:
            pass

    def itemPressed(self, item, col) :
        self.lastClick = 1
        if QtWidgets.QApplication.mouseButtons()  == QtCore.Qt.RightButton:
            item.pressed()


    def itemSelectionChanged(self):
        if len(self.hierarchyWidget.selectedItems()) == 0:
            for cache in self.ABCViewerNode.values():
                cache.setSelection("")


    def requireItemCollapse(self, item):
        pass

    def requireItemExpanded(self, item) :
        self.expandItem(item)

    def itemDoubleClicked(self, item, column) :
        '''  An item on the hierarchy is double clicked'''
        if column == 0:
            if item.isWildCard:
                if not item.protected:
                    text, ok = QtWidgets.QInputDialog.getText(self, 'WildCard expression',  'Enter the expression:', QtWidgets.QLineEdit.Normal, item.getPath())
                    if ok:
                        #first change the path
                        item.setExpression(text)

            else:
                self.expandItem(item)
                item.setExpanded(True)

        elif column == 1:
            shader = item.getShader(self.getLayer())
            if shader:
                if shader["fromfile"] == False:
                    cmds.select(shader["shader"], r=1, ne=1)

        elif column == 2:
            shader = item.getDisplacement(self.getLayer())
            if shader:
                if shader["fromfile"] == False:
                    cmds.select(shader["shader"], r=1, ne=1)


    def expandItem(self, item) :
        expandAll = False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            expandAll = True

        if item.hasChidren():
            items = item.cache.getHierarchy(item.getPath())
            if len(items) != 0 :
                createdItems = self.createBranch(item, items)
                if expandAll:
                    for i in createdItems:
                        self.hierarchyWidget.expandItem(i)
                        self.expandItem(i)
            
            return


        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)

    def createBranch(self, parentItem, abcchild, hierarchy = False, p = "/") :
        ''' 
        createBranch
        This function will create a branch inside the cache hierarchy
        '''
        createdItems = []
        for item in abcchild :
            itemType = item["type"]
            itemName = item["name"]

            itemExists = False
            for i in xrange(0, parentItem.childCount()) :
                text = parentItem.child(i).getDisplayPath()
                if str(text) == str(itemName) :
                    itemExists = True

            if itemExists == False :
                newItem = treeitem.abcTreeItem(parentItem.cache, parentItem.path + [itemName], itemType, self)
                parentItem.cache.itemsTree.append(newItem)

                newItem.checkShaders(self.getLayer())
                newItem.checkProperties(self.getLayer())
               
                # check if the item has chidren, but go no further...
                childsItems = newItem.cache.getHierarchy(newItem.getPath())
                if childsItems:
                    newItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.ShowIndicator)
                    newItem.setHasChildren(True)
                else:
                    newItem.setHasChildren(False)


                parentItem.addChild(newItem)

                if hierarchy == True :
                    parentItem = newItem

                self.hierarchyWidget.resizeColumnToContents(0)
                createdItems.append(newItem)

        return createdItems

    def populate(self) :
        for cache in self.ABCViewerNode.values():
            if cache.cache != "":
                firstLevel = cache.getHierarchy(cache.ABCcurPath or "/")

                pathList = [elem for elem in cache.ABCcurPath.split("/") if elem]
                root = treeitem.abcTreeItem(cache, pathList, "Transform", self)

                root.checkShaders(self.getLayer())
                root.checkProperties(self.getLayer())
                root.setHasChildren(True)
                cache.itemsTree.append(root)

                self.hierarchyWidget.addTopLevelItem(root)
                self.createBranch(root,firstLevel)
                root.setExpanded(1)

            ### CHECK WILDCARD ASSIGNATIONS
            tags = cache.assignations.getAllTags()
            wildsAdded = []
            tagsAdded = []
            for wild in cache.assignations.getAllWidcards():
                name = wild["name"]
                fromTag = False
                if tags:
                    if name in tags:
                        if not name in tagsAdded :
                            tagsAdded.append(name)
                            self.createTag(root, name, wild["fromfile"])
                            fromTag = True

                if not fromTag:
                    if not name in wildsAdded :
                        wildsAdded.append(name)
                        self.createWildCard(root, name, wild["fromfile"])
                        

            if tags:
                for tag in tags:
                    if not tag in tagsAdded:
                            tagsAdded.append(tag)
                            self.createTag(root, tag, False)

    def getShader(self):
        x = cmds.ls(mat=1, sl=1)
        if len(x) == 0:
            return None

        if cmds.nodeType(x[0]) == "displacementShader":
            return x[0]

        else:
            return self.createSG(x[0])


    def checkShaders(self, layer=None, item=None):

        if item is None or item.isWildCard == True:
            # we check every single item.
            for cache in self.ABCViewerNode.values():
                if cache.cache != "":
                    for item in cache.itemsTree:
                        item.checkShaders(layer)
        else:
            # we only check this item and his childrens
            item.checkShaders(layer)

            numChildren = item.childCount()
            for i in range(numChildren):
                self.checkShaders(layer, item.child(i))

    def checkProperties(self, layer=None, item=None):

        if item is None or item.isWildCard == True:
            # we check every single item.
            for cache in self.ABCViewerNode.values():
                if cache.cache != "":
                    for item in cache.itemsTree:
                        item.checkProperties(layer)
        else:
            # we only check this item and his childrens
            item.checkProperties(layer)
            numChildren = item.childCount()
            for i in range(numChildren):
                self.checkProperties(layer, item.child(i))
                    

    def cleanAssignations(self):
        ''' This function will remove any assignation that no longer exists in the cache'''
        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            shaders = assignations.getAllShaderPaths()

            toRemove = []
            for shader in shaders:
                for path in shader:
                    if path.startswith("/"):
                        if self.ABCViewerNode[shape].getHierarchy(path) == None:
                            toRemove.append(path)
            
            for remove in toRemove:

                print "Cleaning non existing path", remove
                assignations.assignShader(None, remove, None)


    def getNode(self):
        tr = cmds.ls( type= 'transform', sl=1, l=1) + cmds.ls(type= 'alembicHolder', sl=1, l=1)
        if len(tr) == 0:
            return
        for x in tr:
            if cmds.nodeType(x) == "alembicHolder":
                shape = x
            else:
                shapes = cmds.listRelatives(x, shapes=True, f=1)
                if not shapes:
                    continue
                shape = shapes[0]
            if cmds.nodeType(shape) == "gpuCache" or cmds.nodeType(shape) == "alembicHolder":

                self.ABCViewerNode[shape] = gpucache.gpucache(shape, self)
                cacheAssignations = self.ABCViewerNode[shape].getAssignations()

                if cmds.objExists(str(shape) + ".jsonFile"):
                    cur = cmds.getAttr("%s.jsonFile" % shape)
                    if cur is not None:
                        for p in os.path.expandvars(cur).split(";"):
                            try:
                                f = open(p, "r")
                                allLines = json.load(f)
                                if "shaders" in allLines:
                                    cacheAssignations.addShaders(allLines["shaders"], fromFile=True)
                                if "attributes" in allLines:
                                    cacheAssignations.addOverrides(allLines["attributes"], fromFile=True)
                                if "displacement" in allLines:
                                    cacheAssignations.addDisplacements(allLines["displacement"], fromFile=True)
                                if "layers" in allLines:
                                    cacheAssignations.addLayers(allLines["layers"], fromFile=True)
                                f.close()
                            except:
                                pass


                if not cmds.objExists(str(shape) + ".shadersAssignation"):
                    cmds.addAttr(shape, ln='shadersAssignation', dt='string')
                else:
                    cur = cmds.getAttr("%s.shadersAssignation"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addShaders(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str( shape )+ ".attributes"):
                    cmds.addAttr(shape, ln='attributes', dt='string')

                else:
                    cur = cmds.getAttr("%s.attributes"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addOverrides(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str(shape) + ".displacementsAssignation"):
                    cmds.addAttr(shape, ln='displacementsAssignation', dt='string')
                else:
                    cur = cmds.getAttr("%s.displacementsAssignation" % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addDisplacements(json.loads(cur))
                        except:
                            pass


                if not cmds.objExists(str(shape) + ".layersOverride"):
                    cmds.addAttr(shape, ln='layersOverride', dt='string')
                else:
                    cur = cmds.getAttr("%s.layersOverride"  % shape)
                    if cur != None and cur != "":
                        try:
                            cacheAssignations.addLayers(json.loads(cur))
                        except:
                            pass

                attrs=["Json","Shaders","Attributes","Displacements"]
                for attr in attrs:
                    if not cmds.objExists(str(shape) + ".skip%s" % attr):
                        cmds.addAttr(shape, ln='skip%s' % attr, at='bool')

        

    def getCache(self):
        for shape in self.ABCViewerNode:
            self.ABCViewerNode[shape].updateCache()

        self.cleanAssignations()


    def createWildCard(self, parentItem, wildcard="*", protected=False) :
        ''' Create a wilcard assignation item '''

        newItem = treeitemWildcard.wildCardItem(parentItem.cache, wildcard, self)
        parentItem.cache.itemsTree.append(newItem)
        newItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)
        parentItem.addChild(newItem)
        
        newItem.checkShaders(self.getLayer())
        newItem.checkProperties(self.getLayer())

        newItem.protected = protected

    def createTag(self, parentItem, tag, protected=False) :
        ''' Create a wilcard assignation item '''

        newItem = treeitemTag.tagItem(parentItem.cache, tag, self)
        parentItem.cache.itemsTree.append(newItem)
        newItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)
        parentItem.addChild(newItem)
        
        newItem.checkShaders(self.getLayer())
        newItem.checkProperties(self.getLayer())

        newItem.protected = protected



    def updateTags(self):
        for shape in self.ABCViewerNode:
            self.ABCViewerNode[shape].updateTags() 

    def addWildCard(self):
        ''' Add a widldcard expression to the current cache'''
        
        # first get the current cache
        item = self.hierarchyWidget.currentItem()
        if item is None:
            return

        # and the top level ancestor..
        if item is not None:
            while 1:
                pitem = item.parent()
                if pitem is None:
                    break
                item = pitem

        self.createWildCard(item)

    # def autoAssign(self):
    #     ''' Assign shaders to selected tags, using their name.'''
    #     for item in self.hierarchyWidget.selectedItems():
    #         if item.isTag:
    #             item.autoAssignShader()
