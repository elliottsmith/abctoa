from PySide2 import QtWidgets, QtGui, QtCore
import maya.cmds as cmds

class CopyLayers(QtWidgets.QWidget):    
    def __init__(self, win):        
        super(CopyLayers, self).__init__(win)

        self.setParent(win)        
        self.setWindowFlags(QtCore.Qt.Window)   
        
        self.shaderManager = win

        self.setObjectName('CopyLayers')
        self.setWindowTitle('Copy Layers')        
        self.setGeometry(50, 50, 750, 80)
        
        self.main_layout = QtWidgets.QVBoxLayout()
           
        self.initUI()
        self.setLayout(self.main_layout)

    def showEvent(self, event):
        """Show event to re populate combo boxes"""
        self.source_combo.clear()
        self.target_combo.clear()

        self.get_layers()
        return QtWidgets.QMainWindow.showEvent(self, event)

    def initUI(self):
        """Initialise the interface"""

        # copy assignments
        self.copy_layer_assignmnets_layout = QtWidgets.QHBoxLayout()

        self.source_group = QtWidgets.QGroupBox("Source Layer")
        self.source_layout = QtWidgets.QHBoxLayout()
        self.source_combo = QtWidgets.QComboBox()
        self.source_layout.addWidget(self.source_combo)
        self.source_group.setLayout(self.source_layout)

        self.target_group = QtWidgets.QGroupBox("Target Layer")
        self.target_layout = QtWidgets.QHBoxLayout()
        self.target_combo = QtWidgets.QComboBox()
        self.target_layout.addWidget(self.target_combo)
        self.target_group.setLayout(self.target_layout)

        self.confirm_copy = QtWidgets.QPushButton("Copy Assignments")
        self.confirm_copy.setEnabled(False)

        self.copy_layer_assignmnets_layout.addWidget(self.source_group)
        self.copy_layer_assignmnets_layout.addWidget(self.target_group)
        self.copy_layer_assignmnets_layout.addWidget(self.confirm_copy)
        self.main_layout.addLayout(self.copy_layer_assignmnets_layout)

        self.confirm_copy.clicked.connect(self.copy_assignments)
        self.source_combo.currentIndexChanged.connect(self.combo_changed)
        self.target_combo.currentIndexChanged.connect(self.combo_changed)

    def combo_changed(self, index):
        """Combo changed slot"""

        if self.source_combo.currentText() != self.target_combo.currentText():
            self.confirm_copy.setEnabled(True)
        else:
            self.confirm_copy.setEnabled(False)

    def copy_assignments(self):
        """Copy Assignments function"""

        source = self.source_combo.currentText()
        target = self.target_combo.currentText()

        print 'Copy: %s > %s'% (source, target)

        for cache in self.shaderManager.ABCViewerNode.values():

            main = cache.assignations.mainAssignations
            layers = cache.assignations.layers

            source_dict = {'shaders' : {}, 'displacements' : {}, 'properties' : {}}

            if source == 'defaultRenderLayer':
                source_dict['shaders'] = main.getShaders()
                source_dict['displacements'] = main.getDisplacements()
                source_dict['properties'] = main.getOverrides()

            else:
                if source in layers.layers:
                    source_dict['shaders'] = layers.layers[source].getShaders()
                    source_dict['displacements'] = layers.layers[source].getDisplacements()
                    source_dict['properties'] = layers.layers[source].getOverrides()

            if source_dict == {'shaders' : {}, 'displacements' : {}, 'properties' : {}}:
                # nothing in source to copy
                self.close()
                return

            if target == 'defaultRenderLayer':
                pass
            else:
                # delete it and add it again
                if target in layers.layers:
                    del layers.layers[target]
                layers.addLayer(target, source_dict)

            # write to attribute editor
            cache.assignations.writeLayer()

            # reload the shader manager
            self.shaderManager.reset(shape=cache.shape)         

        self.shaderManager.setLayer(target)
        self.close()

    def get_layers(self):
        """Get current layers"""

        renderLayers = []
        for layer in cmds.ls(type="renderLayer"):
            con = cmds.connectionInfo(layer + ".identification", sourceFromDestination=True)
            if con:
                if con.split(".")[0] == "renderLayerManager":
                    renderLayers.append(layer)

        for i in renderLayers:
            self.source_combo.addItem(i)
        for i in renderLayers:
            if i != 'defaultRenderLayer':
                self.target_combo.addItem(i)
