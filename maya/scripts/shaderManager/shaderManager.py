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

# sys libs
import os, json

# pyside
from PySide2 import QtWidgets, QtGui, QtCore

# local imports
from gpucache import gpucache, treeitem, treeDelegate, treeitemWildcard, treeitemTag
reload(treeitem)
reload(treeitemWildcard)
reload(treeitemTag)
reload(treeDelegate)
reload(gpucache)

from propertywidgets import property_editorByType
reload(property_editorByType)

from propertywidgets.property_editorByType import PropertyEditor

from shaderwidget import shader_widget
reload(shader_widget)

from ui import UI_ABCHierarchy
reload(UI_ABCHierarchy)

from shaderManagerUtils import CopyLayers, import_xforms, get_previously_imported_transforms

# arnold / maya
from arnold import *
import maya.cmds as cmds
import maya.mel as mel
from maya.OpenMaya import MObjectHandle, MDGMessage, MMessage, MNodeMessage, MFnDependencyNode, MObject, MSceneMessage
import maya.app.renderSetup.model.renderSetup as renderSetup
import cask

d = os.path.dirname(__file__)

def debugger(text, wait=0):
    """debugger"""
    if 'time' not in globals().keys():
        import time
    
    if os.environ.has_key('ABCTOA_DEBUG'):
        if os.environ['ABCTOA_DEBUG']:
            print "[Debug] %s" % text
            time.sleep(wait)

class ShaderManager(QtWidgets.QMainWindow, UI_ABCHierarchy.Ui_NAM):
    def __init__(self, parent=None):
        """Shader Manager class"""
        super(ShaderManager, self).__init__(parent)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)        

        # initialise the inherited ui class
        self.setupUi(self)

        # set up some vars
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

        # properties widget
        self.propertyEditorWindow = QtWidgets.QDockWidget(self)
        self.propertyEditorWindow.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.propertyEditorWindow.setWindowTitle("Properties")
        self.propertyEditorWindow.setMinimumWidth(300)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.propertyEditorWindow)
        self.propertyType = "polymesh"
        self.propertyEditor = PropertyEditor(self, self.propertyType, self.propertyEditorWindow)
        self.propertyEditorWindow.setWidget(self.propertyEditor)
        self.propertyEditor.propertyChanged.connect(self.propertyChanged)        

        # shaders scroll widget
        self.shaderWindow = QtWidgets.QDockWidget(self)
        self.shaderWindow.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.shaderWindow.setWindowTitle("Shaders")
        self.shaderWindow.setMinimumWidth(300)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.shaderWindow)
        self.shaderEditor = shader_widget.ShadersDockWidget(self)
        self.shaderWindow.setWidget(self.shaderEditor)

        # hierarchy widget
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

        self.layers_pixmap = QtGui.QPixmap(os.path.join(d, "../../icons/layerEditor.png"))
        self.layers_btn.setIconSize(QtCore.QSize(18, 18))
        self.layers_btn.setIcon(self.layers_pixmap)

        # signals, slots and callbacks
        self.hierarchyWidget.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.hierarchyWidget.itemExpanded.connect(self.requireItemExpanded)
        self.hierarchyWidget.itemCollapsed.connect(self.requireItemCollapse)
        self.hierarchyWidget.itemClicked.connect(self.itemCLicked)
        self.hierarchyWidget.itemSelectionChanged.connect(self.itemSelectionChanged)
        self.hierarchyWidget.itemPressed.connect(self.itemPressed)
        self.hierarchyWidget.setExpandsOnDoubleClick(False)

        self.getLayers()
        self.setCurrentLayer()
        
        self.addCBs()

        self.afterNewSceneCBId = MSceneMessage.addCallback(MSceneMessage.kAfterNew, self.reset)
        self.afterOpenSceneCBId = MSceneMessage.addCallback(MSceneMessage.kAfterOpen, self.reset)

        self.disableLayerOverrides()

        self.overrideShaders.stateChanged.connect(self.overrideShadersChanged)
        self.overrideDisps.stateChanged.connect(self.overrideDispsChanged)        
        self.overrideProps.stateChanged.connect(self.overridePropsChanged)
        self.soloSelected.stateChanged.connect(self.soloSelectedChanged)        
        self.wildCardButton.pressed.connect(self.addWildCard)
        self.updateXformsButton.pressed.connect(self.updateXforms)        
        self.layers_btn.clicked.connect(self.layers_clicked)

    def updateXforms(self):
        """"""
        print 'Updating Previously imported xforms'

        # ensure that the abcfile is the current one
        self.reset()

        for parent in self.ABCViewerNode.keys():

            abcfile = str(self.ABCViewerNode[parent].ABCcache)
            parent_under = '|'.join(self.ABCViewerNode[parent].shape.split('|')[:-1])

            cmd = 'AbcImport "%s" -d -rpr "%s" -ct "%s" -eft "Shape"' % (abcfile, parent_under, parent_under)
            try:
                print '\n%s\n' % cmd
                mel.eval(cmd)
            except Exception as e:
                print "Error running update transforms : %s" % e

    def layers_clicked(self):
        """"""
        layers_copy = CopyLayers(self)
        layers_copy.show()

    def geoFilterChanged(self):
        """Geo filter callback, selects matching items"""

        # get the filter string
        filter_string = self.geoFilter.text()
        types = []
        if self.transform_check.isChecked():
            types.append('Transform')
        if self.shape_check.isChecked():
            types.append('Shape')

        # expand the hierarchy so it is iterable
        self.hierarchyWidget.expandAll()
        _iter = QtWidgets.QTreeWidgetItemIterator(self.hierarchyWidget)

        index = 0
        while(_iter.value()):
            item = _iter.value()

            if filter_string != "" and len(filter_string) > 1:

                if filter_string in str(item.text(0)):
                    if item.itemType in types:
                        item.setSelected(True)
                    else:
                        item.setSelected(False)
                else:
                    item.setSelected(False)
            else:
                item.setSelected(False)

            index += 1
            _iter += 1

    def showEvent(self, event):
        """Show the main window"""

        windowname = "hyperShadePanel1Window"
        if cmds.window(windowname, exists=True):
            pass
        else:
            print 'Opening Hypershade'
            mel.eval("HypershadeWindow;")

        current_selection = cmds.ls(sl=True)
        if self.ABCViewerNode != {}:
            self.reset(self.ABCViewerNode.values()[0].shape)
        else:
            self.reset()
        cmds.select(current_selection)

        return QtWidgets.QMainWindow.showEvent(self, event)

    def hideEvent(self, event):
        """Hide the main window"""

        current_selection = cmds.ls(sl=True)
        if self.ABCViewerNode != {}:
            self.reset(self.ABCViewerNode.values()[0].shape)
        else:
            self.reset()
        cmds.select(current_selection)            

        return QtWidgets.QMainWindow.hideEvent(self, event)

    def reset(self, shape=None, *args, **kwargs):
        """Reset the main window to initial state"""
        if shape:
            if cmds.objExists(shape):
                cmds.select(shape)

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

    def overrideShadersChanged(self, state):
        """Override shaders toggle"""

        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedShader(self.getLayer(), result)

        self.updateTree()

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

    def overridePropsChanged(self, state):
        """Override properties toggle"""

        result = True
        if state == 0:
            result = False

        if self.getLayer() == None:
            return

        for shape in self.ABCViewerNode:
            assignations = self.ABCViewerNode[shape].getAssignations()
            assignations.setRemovedProperties(self.getLayer(), result)

        self.updateTree()

    def soloSelectedChanged(self, state):
        """Solo selected toggle"""

        if state == 0:
            for cache in self.ABCViewerNode.values():
                cache.setSelection([])
        else:
            for cache in self.ABCViewerNode.values():

                allSelected = []
                for item in self.hierarchyWidget.selectedItems():
                    if item.isTag == False and item.isWildCard == False:
                        allSelected.append(item.getPath())

                if "/" in allSelected:
                    allSelected = []
                cache.setSelection(allSelected)

    def createSG(self, node):
        """Create a shading group if node doesn't have one"""

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
        """Callback when a node is renamed"""

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

            # we need to ensure that we are updating all the caches, not just the one selected
            current_selection = cmds.ls(sl=True)
            cmds.select(cmds.ls(type= 'alembicHolder'))
            self.getNode()

            if self.ABCViewerNode != {}:

                if cmds.getClassification(cmds.nodeType(nodeName), satisfies="shader"):

                    if cmds.nodeType(nodeName) == "displacementShader":
                        # renaming displacements in caches
                        for cache in self.ABCViewerNode.values():
                            cache.renameDisplacement(prevName, nodeName)
                            self.reset(shape=cache.shape)
                        self.shaderEditor.renameShader(prevName, nodeName)

                    else:
                        # renaming shaders in caches
                        for cache in self.ABCViewerNode.values():
                            cache.renameShader(prevName, nodeName)
                            self.reset(shape=cache.shape)
                        self.shaderEditor.renameShader(prevName, nodeName)

                elif cmds.nodeType(nodeName) == "shadingEngine":
                    # renaming shaders in caches
                    for cache in self.ABCViewerNode.values():
                        cache.renameShader(prevName, nodeName)
                        self.reset(shape=cache.shape)

                    self.shaderEditor.renameShader(prevName, nodeName)
                    self.checkShaders()

                elif cmds.nodeType(nodeName) == "renderLayer":

                    for cache in self.ABCViewerNode.values():
                        cache.assignations.layers.renameLayer(prevName, nodeName)
                        cache.assignations.writeLayer()
                        self.reset(shape=cache.shape)

                    # update the layers combo
                    self.getLayers()
                    self.setLayer(nodeName)

            cmds.select(current_selection)

    def newNodeCB(self, newNode, data ):
        """Callback when creating a new node"""

        mobject = MObjectHandle( newNode ).object()
        nodeFn = MFnDependencyNode ( mobject )
        if nodeFn.hasUniqueName():
            nodeName = nodeFn.name()
            if cmds.getClassification(cmds.nodeType(nodeName), satisfies="shader"):
                # add shader to scroller
                self.shaderEditor.addShader(nodeName)
            elif nodeFn.typeName() == 'renderLayer':
                self.renderLayer.addItems([nodeName])                

    def delNodeCB(self, node, data ):
        """Callback when a node has been deleted"""

        mobject = MObjectHandle( node ).object()
        nodeFn = MFnDependencyNode ( mobject )
        if nodeFn.hasUniqueName():
            nodeName = nodeFn.name()

            didSomething = False
            for cache in self.ABCViewerNode.values():
                didSomething = True
                cache.removeShader(nodeName)

            self.shaderEditor.removeShader(nodeName)  
            
            if didSomething:
                self.checkShaders()                           

    def newhierarchyWidgetdragEnterEvent(self, event):
        """Enter event"""

        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetdragMoveEvent(self, event):
        """Move event"""

        if event.mimeData().hasFormat("application/x-shader") or event.mimeData().hasFormat("application/x-displacement"):
            event.accept()
        else:
            event.ignore()

    def newhierarchyWidgetDropEvent(self, event):
        """Drop event"""

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
        """Add the callbacks"""

        try:
            self.renderLayer.currentIndexChanged.connect(self.layerChanged)
            self.NodeNameMsgId  = MNodeMessage.addNameChangedCallback( MObject(), self.nameChangedCB )
            self.newNodeCBMsgId = MDGMessage.addNodeAddedCallback( self.newNodeCB )
            self.delNodeCBMsgId = MDGMessage.addNodeRemovedCallback( self.delNodeCB )

            self.layerChangedJob = cmds.scriptJob( e= ["renderLayerManagerChange",self.setCurrentLayer])
        except:
            pass

    def clearCBs(self, event=None):
        """Clear the callbacks"""

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
        """Main window close event"""

        event.ignore()
        self.hide()
        return

    def clearing(self):
        """Clearing method called from maya menu"""

        self.clearCBs()
        try:
            MMessage.removeCallback( self.afterNewSceneCBId )
            MMessage.removeCallback( self.afterOpenSceneCBId )
        except:
            pass

    def setLayer(self, layername):
        """"""
        idx = self.renderLayer.findText(layername)
        if idx != -1:
            self.renderLayer.setCurrentIndex(idx)
        self.curLayer = layername       

    def setCurrentLayer(self):
        """Set current layer"""

        try:
            curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
        except:
            return
        curLayeridx = self.renderLayer.findText(curLayer)
        if curLayeridx != -1:
            self.renderLayer.setCurrentIndex(curLayeridx)
        self.curLayer = curLayer

    def layerChanged(self, index):
        """Layer changed slot"""

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
        try:
            curLayer = cmds.editRenderLayerGlobals(query=1, currentRenderLayer=1)
            if self.curLayer:
                if curLayer != self.curLayer:

                    rs = renderSetup.instance()
                    if self.curLayer != 'defaultRenderLayer':

                        # there is a bug whereby, if you have a collection filter set to 'All' and you change the name of the layer
                        # when you toggle active layer to that layer, it crashes, as a work around, you can set the filter type to transform
                        # and then back 'All'.

                        # so, get the layer in question
                        layer = rs.getRenderLayer(self.curLayer.split('rs_')[-1])

                        # and the collections
                        collections = layer.getCollections()
                        col_types = {}

                        # iterate over the collections and get the filter type and store them
                        for col in collections:
                            selector = col.getSelector()
                            current_filter_type = selector.getFilterType()
                            col_types[col] = current_filter_type

                            # if the filter type is 'All', set it to something else, in this case (1) transform
                            if current_filter_type == 0:
                                selector.setFilterType(1)
                        
                        # now we can set the active layer
                        cmds.editRenderLayerGlobals( currentRenderLayer=self.curLayer)

                        # now we can revert the collections filter type back to their original types
                        for col in col_types:
                            selector = col.getSelector()
                            selector.setFilterType(col_types[col])
                    else:
                        cmds.editRenderLayerGlobals( currentRenderLayer=self.curLayer)
        except:
            pass

    def updateTree(self):
        """Update alembic tree"""

        items = []
        for i in range(self.hierarchyWidget.topLevelItemCount()):
            self.visitTree(items, self.hierarchyWidget.topLevelItem(i))

        for item in items:
            item.removeAssigns()
            item.checkShaders(self.getLayer())
            item.checkProperties(self.getLayer())

    def visitTree(self, items, treeitem):
        """Visit alembic tree"""

        items.append(treeitem)
        for i in range(treeitem.childCount()):
            self.visitTree(items, treeitem.child(i))

    def enableLayerOverrides(self):
        """Enable layer override"""

        self.overrideShaders.setEnabled(1)
        self.overrideDisps.setEnabled(1)        
        self.overrideProps.setEnabled(1)

        self.overrideShaders.setChecked(0)
        self.overrideDisps.setChecked(0)        
        self.overrideProps.setChecked(0)

    def disableLayerOverrides(self):
        """Disable layer override"""

        self.overrideShaders.setEnabled(0)
        self.overrideDisps.setEnabled(0)        
        self.overrideProps.setEnabled(0)

        self.overrideShaders.setChecked(0)
        self.overrideDisps.setChecked(0)        
        self.overrideProps.setChecked(0)

    def getLayers(self):
        """Get layers"""

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
        """Properry change slot"""

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

            items = []
            
            selectedItems = self.hierarchyWidget.selectedItems()

            item = self.hierarchyWidget.currentItem()
            if item:
                items.append(item)

            if len(selectedItems) > 1:
                items = items + selectedItems

            for item in items:
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
        """Update the color of a property"""

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
        """Get current layer"""

        if self.curLayer != "defaultRenderLayer":
            return self.curLayer
        return None

    def itemCLicked(self, item, col, force=False):
        """Hierarchy item click"""

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

        if self.soloSelected.isChecked():
            cache.setSelection(allSelected)
        else:
            cache.setSelection([])

        self.propertyEditor.resetToDefault()
        self.updateAttributeEditor()
        self.propertyEditing = False

    def updateAttributeEditor(self):
        """Update what is inside the attribute editor (red text,....)"""

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

    def itemPressed(self, item, col):
        """Item clicked event"""

        self.lastClick = 1
        if QtWidgets.QApplication.mouseButtons()  == QtCore.Qt.RightButton:
            item.pressed()

    def itemSelectionChanged(self):
        """Item selection"""

        if len(self.hierarchyWidget.selectedItems()) == 0:
            for cache in self.ABCViewerNode.values():
                cache.setSelection("")

    def requireItemCollapse(self, item):
        pass

    def requireItemExpanded(self, item):
        """"""

        self.expandItem(item)

    def itemDoubleClicked(self, item, column) :
        """Hierarchy item double click slot"""

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

    def expandItem(self, item):
        """Expand hierarchy tree"""

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
        """Create a branch inside the cache hierarchy"""

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

    def populate(self):
        """Populate the hierarchy tree"""

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
        """Get selected shader"""

        x = cmds.ls(mat=1, sl=1)
        if len(x) == 0:
            return None

        if cmds.nodeType(x[0]) == "displacementShader":
            return x[0]

        else:
            return self.createSG(x[0])

    def checkShaders(self, layer=None, item=None):
        """Check shaders"""

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
        """Check properties"""

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
        """Clear any assignation that no longer exists in the cache"""

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
        """Load selected alembicHolder node into cache manager"""

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
        """Update and clean cache"""

        for shape in self.ABCViewerNode:
            self.ABCViewerNode[shape].updateCache()

        self.cleanAssignations()

    def createWildCard(self, parentItem, wildcard="*", protected=False) :
        """Create a wilcard assignation item"""

        newItem = treeitemWildcard.wildCardItem(parentItem.cache, wildcard, self)
        parentItem.cache.itemsTree.append(newItem)
        newItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)
        parentItem.addChild(newItem)
        
        newItem.checkShaders(self.getLayer())
        newItem.checkProperties(self.getLayer())

        newItem.protected = protected

    def createTag(self, parentItem, tag, protected=False) :
        """Create a tag item"""

        newItem = treeitemTag.tagItem(parentItem.cache, tag, self)
        parentItem.cache.itemsTree.append(newItem)
        newItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)
        parentItem.addChild(newItem)
        
        newItem.checkShaders(self.getLayer())
        newItem.checkProperties(self.getLayer())

        newItem.protected = protected

    def updateTags(self):
        """Update tags"""

        for shape in self.ABCViewerNode:
            self.ABCViewerNode[shape].updateTags() 

    def addWildCard(self):
        """Add a widldcard expression to the current cache"""
        
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
