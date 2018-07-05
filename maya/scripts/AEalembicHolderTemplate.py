
import os
import maya.cmds as cmds
from milk.utils.v1_0.pyside.loader import QtGui, QtCore, shiboken
import maya.OpenMayaUI as mui

################################################################################
#Base Attribute Widget
################################################################################
class BaseAttrWidget(QtGui.QWidget):
    '''
    This is the base attribute widget from which all other attribute widgets
    will inherit. Sets up all the relevant methods + common widgets and initial
    layout.
    '''
    def __init__(self, node, attr, label='', parent=None):
        '''
        Initialize
        
        @type node: str
        @param node: The name of the node that this widget should start with.
        @type attr: str
        @param attr: The name of the attribute this widget is responsible for.
        @type label: str
        @param label: The text that should be displayed in the descriptive label.
        '''
        super(BaseAttrWidget, self).__init__(parent)
        
        self.node = node    #: Store the node name
        self.attr = attr    #: Store the attribute name
        
        #: This will store information about the scriptJob that we will create
        #: so that we can update this widget whenever its attribute is updated
        #: separately.
        self.sj = None
        
        #: Use this variable to track whether the gui is currently being updated
        #: or not.
        self.updatingGUI = False

    def callUpdateGUI(self):
        '''
        Calls the updateGUI method but makes sure to set the updatingGUI variable
        while doing so.
        
        This is necessary so that we don't get caught in a loop where updating
        the UI will trigger a signal that updates the attr on the node, which
        in turn triggers the scriptJob to run updateGUI again.
        '''
        self.updatingGUI = True
        
        self.updateGUI()
        
        self.updatingGUI = False
        
    def updateGUI(self):
        '''
        VIRTUAL method. Called whenever the widget needs to update its displayed
        value to match the value of the attribute on the node.
        '''
        raise NotImplementedError
        
    def callUpdateAttr(self):
        '''
        Calls the updateAttr method but only if not currently updatingGUI
        '''
        if not self.updatingGUI:
            self.updateAttr()
            
    def updateAttr(self):
        '''
        VIRTUAL method. Should be called whenever the user makes a change to this
        widget via the UI. This method is then responsible for applying the same
        change to the actual attribute on the node.
        '''
        raise NotImplementedError
        
    def setNode(self, node):
        '''
        This widget should now represent the same attr on a different node.
        '''
        oldNode = self.node
        self.node = node
        self.callUpdateGUI()
        
        if not self.sj or not cmds.scriptJob(exists=self.sj) or not oldNode == self.node:
            #script job
            ct = 0
            while self.sj:
                #Kill the old script job.
                try:
                    if cmds.scriptJob(exists=self.sj):
                        cmds.scriptJob(kill=self.sj, force=True)
                    self.sj = None
                except RuntimeError:
                    #Could not kill the old script job for some reason.
                    #This happens, albeit very rarely, when that scriptJob is
                    #being executed at the same time we try to kill it. Pause
                    #for a second and then retry.
                    ct += 1
                    if ct < 10:
                        cmds.warning("Got RuntimeError trying to kill scriptjob...trying again")
                        time.sleep(1)
                    else:
                        #We've failed to kill the scriptJob 10 consecutive times.
                        #Time to give up and move on.
                        cmds.warning("Killing scriptjob is taking too long...skipping")
                        break
                        
            #Set the new scriptJob to call the callUpdateGUI method everytime the
            #node.attr is changed.
            self.sj = cmds.scriptJob(ac=['%s.%s' % (self.node, self.attr), self.callUpdateGUI], killWithScene=1)
        

################################################################################
#Attribute widgets
################################################################################
class IntWidget(BaseAttrWidget):
    '''
    This widget can be used with numerical attributes.
    '''
    def __init__(self, node, attr, label='', parent=None):
        '''
        Initialize
        '''
        super(IntWidget, self).__init__(node, attr, label, parent)

        self.valLE = QtGui.QLineEdit(parent=self)
        self.valLE.setValidator(QtGui.QIntValidator(self.valLE))
        self.connect(self.valLE, QtCore.SIGNAL("editingFinished()"), self.callUpdateAttr)
        self.setNode(node)
        
    def updateGUI(self):
        '''
        Implement this virtual method to update the value in valLE based on the
        current node.attr
        '''
        self.valLE.setText('%.03f' % round(cmds.getAttr("%s.%s" % (self.node, self.attr)), 3))
        
    def updateAttr(self):
        '''
        Implement this virtual method to update the actual node.attr value to
        reflect what's currently in the UI.
        '''
        cmds.setAttr("%s.%s" % (self.node, self.attr), float(self.valLE.text()))

class FloatWidget(BaseAttrWidget):
    '''
    This widget can be used with numerical attributes.
    '''
    def __init__(self, node, attr, label='', parent=None):
        '''
        Initialize
        '''
        super(FloatWidget, self).__init__(node, attr, label, parent)

        self.valLE = QtGui.QLineEdit(parent=self)
        self.valLE.setValidator(QtGui.QDoubleValidator(self.valLE))
        self.connect(self.valLE, QtCore.SIGNAL("editingFinished()"), self.callUpdateAttr)
        self.setNode(node)
        
    def updateGUI(self):
        '''
        Implement this virtual method to update the value in valLE based on the
        current node.attr
        '''
        self.valLE.setText('%.03f' % round(cmds.getAttr("%s.%s" % (self.node, self.attr)), 3))
        
    def updateAttr(self):
        '''
        Implement this virtual method to update the actual node.attr value to
        reflect what's currently in the UI.
        '''
        cmds.setAttr("%s.%s" % (self.node, self.attr), float(self.valLE.text()))

class StrWidget(BaseAttrWidget):
    '''
    This widget can be used with string attributes.
    '''
    def __init__(self, node, attr, label='', parent=None):
        '''
        Initialize
        '''
        super(StrWidget, self).__init__(node, attr, label, parent)

        self.valLE = QtGui.QLineEdit(parent=self)
        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        policy.setHorizontalStretch(1)
        # self.valLE.setSizePolicy(policy)
        # self.setSizePolicy(policy)
        self.connect(self.valLE, QtCore.SIGNAL("editingFinished()"), self.callUpdateAttr)
        self.setNode(node)
        
    def updateGUI(self):
        '''
        Implement this virtual method to update the value in valLE based on the
        current node.attr
        '''
        if cmds.getAttr("%s.%s" % (self.node, self.attr)):
            self.valLE.setText(str(cmds.getAttr("%s.%s" % (self.node, self.attr))))
        
    def updateAttr(self):
        '''
        Implement this virtual method to update the actual node.attr value to
        reflect what's currently in the UI.
        '''

        cmds.setAttr("%s.%s" % (self.node, self.attr), str(self.valLE.text()), type='string')

class EnumWidget(BaseAttrWidget):
    '''
    This widget can be used with enumerated attributes.
    '''
    def __init__(self, node, attr, label='', enums=None, parent=None):
        '''
        Initialize
        
        @type enum: list
        @param enum: An ordered list of the values to be show in the enumeration list
        '''
        super(EnumWidget, self).__init__(node, attr, label, parent)
        
        #Make sure the provided enums are not None
        enums = enums if enums else []

        self.valCB = QtGui.QComboBox(parent=self)
        self.valCB.addItems(enums)
        self.connect(self.valCB, QtCore.SIGNAL("currentIndexChanged(int)"), self.callUpdateAttr)
        self.setNode(node)
        
    def updateGUI(self):
        '''
        Implement this virtual method to update the value in valCB based on the
        current node.attr
        '''
        self.valCB.setCurrentIndex(cmds.getAttr('%s.%s' % (self.node, self.attr)))
        
    def updateAttr(self):
        '''
        Implement this virtual method to update the actual node.attr value to
        reflect what's currently in the UI.
        '''
        cmds.setAttr("%s.%s" % (self.node, self.attr), self.valCB.currentIndex())

class BoolWidget(BaseAttrWidget):
    '''
    This widget can be used with numerical attributes.
    '''
    def __init__(self, node, attr, label='', parent=None):
        '''
        Initialize
        '''
        super(BoolWidget, self).__init__(node, attr, label, parent)

        self.valLE = QtGui.QCheckBox(parent=self)
        self.connect(self.valLE, QtCore.SIGNAL("stateChanged(int)"), self.callUpdateAttr)
        self.setNode(node)
        
    def updateGUI(self):
        '''
        Implement this virtual method to update the value in valLE based on the
        current node.attr
        '''
        self.valLE.setChecked(bool(cmds.getAttr("%s.%s" % (self.node, self.attr))))
        
    def updateAttr(self):
        '''
        Implement this virtual method to update the actual node.attr value to
        reflect what's currently in the UI.
        '''
        cmds.setAttr("%s.%s" % (self.node, self.attr), bool(self.valLE.isChecked()))

################################################################################
#Main AETemplate Widget
################################################################################
class AEalembicHolderTemplate(QtGui.QWidget):
    '''
    The main class that holds all the controls for the alembicHolder node
    '''
    def __init__(self, node, parent=None):
        '''
        Initialize
        '''
        super(AEalembicHolderTemplate, self).__init__(parent)
        self.node = node

        self.row_height = 20
        stylesheet = "QGroupBox { margin-top: 6px; border-radius: 6px; font: bold 14px; border: 1px solid rgb(230, 230, 230); } QGroupBox:title { color: rgb(230, 230, 230); subcontrol-origin: margin; padding: 0px 5px 0px 5px; left: 10px; }"
        self.icon = QtGui.QIcon(QtGui.QPixmap(':/{}'.format('SP_DirIcon.png')))

        # main layout
        self.layout = QtGui.QVBoxLayout(self)

        #########################################################################################################
        # ALEMBIC
        self.alembic_group = QtGui.QGroupBox('Alembic')
        self.alembic_layout = QtGui.QVBoxLayout()
        self.alembic_layout.setContentsMargins(20, 20, 20, 20)
        self.alembic_group.setStyleSheet(stylesheet)
        
        self.alembic_grid = QtGui.QGridLayout()
        self.alembic_group.setContentsMargins(20, 20, 20, 20)


        # cacheFileNames
        self.alembic_btn = QtGui.QPushButton("Add Additional Alembic")
        self.alembic_btn.clicked.connect(self.addAlembicClicked)
        self.alembic_layout.addWidget(self.alembic_btn)
        self.alembic_layout.addLayout(self.alembic_grid)
        self.alembic_grid.setRowMinimumHeight(0, self.row_height)

        self.caches = {}
        ports = cmds.getAttr("%s.cacheFileNames" % (self.node), size=True)
        for i in range(ports):
            self.addCache(i)

        self.alembic_group.setLayout(self.alembic_layout)

        #########################################################################################################
        # GEOMETRY
        self.geometry_group = QtGui.QGroupBox('Geometry')
        self.geometry_group.setStyleSheet(stylesheet)
        self.geometry_grid = QtGui.QGridLayout(self.geometry_group)
        self.geometry_grid.setContentsMargins(20, 20, 20, 20)

        # updateTransforms
        self.updateTransforms = BoolWidget(node, 'updateTransforms', label='Selection Path', parent=self)
        self.geometry_grid.addWidget(QtGui.QLabel('Update Transforms'), 0, 0, 1, 1)
        self.geometry_grid.addWidget(self.updateTransforms, 0, 1, 1, 1)
        self.geometry_grid.setRowMinimumHeight(0, self.row_height)

        # cacheGeomPath
        self.cacheGeomPath = StrWidget(node, 'cacheGeomPath', label='Geometry Path', parent=self)
        self.geometry_grid.addWidget(QtGui.QLabel('Geometry Path'), 1, 0, 1, 1)
        self.geometry_grid.addWidget(self.cacheGeomPath, 1, 1, 1, 1)
        self.geometry_grid.setRowMinimumHeight(1, self.row_height)

        # cacheSelectionPath
        self.cacheSelectionPath = StrWidget(node, 'cacheSelectionPath', label='Selection Path', parent=self)
        self.geometry_grid.addWidget(QtGui.QLabel('Selection Path'), 2, 0, 1, 1)
        self.geometry_grid.addWidget(self.cacheSelectionPath, 2, 1, 1, 1)
        self.geometry_grid.setRowMinimumHeight(2, self.row_height)

        # boundingBoxExtendedMode
        self.boundingBoxExtendedMode = BoolWidget(node, 'boundingBoxExtendedMode', label='Selection Path', parent=self)
        self.geometry_grid.addWidget(QtGui.QLabel('Bounding Box'), 3, 0, 1, 1)
        self.geometry_grid.addWidget(self.boundingBoxExtendedMode, 3, 1, 1, 1)
        self.geometry_grid.setRowMinimumHeight(3, self.row_height)

        # timeOffset
        self.timeOffset = FloatWidget(node, 'timeOffset', label='Selection Path', parent=self)
        self.geometry_grid.addWidget(QtGui.QLabel('Time Offset'), 4, 0, 1, 1)
        self.geometry_grid.addWidget(self.timeOffset, 4, 1, 1, 1)
        self.geometry_grid.setRowMinimumHeight(4, self.row_height)

        self.geometry_group.setLayout(self.geometry_grid)

        #########################################################################################################
        # ASSIGNMENTS
        self.assignments_group = QtGui.QGroupBox('Assignments')
        self.assignments_group.setStyleSheet(stylesheet)
        self.assignments_grid = QtGui.QGridLayout(self.assignments_group)
        self.assignments_grid.setContentsMargins(20, 20, 20, 20)
        self.assignments_grid.setRowMinimumHeight(0, self.row_height)

        # shadersAssignation
        self.shadersAssignation = StrWidget(node, 'shadersAssignation', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Shaders Assignation'), 0, 0, 1, 1)
        self.assignments_grid.addWidget(self.shadersAssignation, 0, 1, 1, 1)
        self.assignments_grid.setRowMinimumHeight(0, self.row_height)

        # displacementsAssignation
        self.displacementsAssignation = StrWidget(node, 'displacementsAssignation', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Displacements Assignation'), 1, 0, 1, 1)
        self.assignments_grid.addWidget(self.displacementsAssignation, 1, 1, 1, 1)
        self.assignments_grid.setRowMinimumHeight(1, self.row_height)

        # attributes
        self.attributes = StrWidget(node, 'attributes', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Attributes'), 2, 0, 1, 1)
        self.assignments_grid.addWidget(self.attributes, 2, 1, 1, 1)
        self.assignments_grid.setRowMinimumHeight(2, self.row_height)

        # layersOverride
        self.layersOverride = StrWidget(node, 'layersOverride', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Layers Override'), 3, 0, 1, 1)
        self.assignments_grid.addWidget(self.layersOverride, 3, 1, 1, 1)
        self.assignments_grid.setRowMinimumHeight(3, self.row_height)

        # shadersNamespace
        self.shadersNamespace = StrWidget(node, 'shadersNamespace', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Shaders Namespace'), 4, 0, 1, 1)
        self.assignments_grid.addWidget(self.shadersNamespace, 4, 1, 1, 1)        
        self.assignments_grid.setRowMinimumHeight(4, self.row_height)

        # geometryNamespace
        self.geometryNamespace = StrWidget(node, 'geometryNamespace', label='', parent=self)
        self.assignments_grid.addWidget(QtGui.QLabel('Geometry Namespace'), 5, 0, 1, 1)
        self.assignments_grid.addWidget(self.geometryNamespace, 5, 1, 1, 1)      
        self.assignments_grid.setRowMinimumHeight(5, self.row_height)

        self.assignments_group.setLayout(self.assignments_grid)

        #########################################################################################################
        # PUBLISH
        self.publish_group = QtGui.QGroupBox('Published Lookdev')
        self.publish_group.setStyleSheet(stylesheet)
        self.publish_grid = QtGui.QGridLayout(self.publish_group)
        self.publish_grid.setContentsMargins(20, 20, 20, 20)

        # jsonFile
        self.jsonFile = StrWidget(node, 'jsonFile', label='', parent=self)
        self.publish_grid.addWidget(QtGui.QLabel('Json File'), 0, 0, 1, 1)
        self.publish_grid.addWidget(self.jsonFile, 0, 1, 1, 1)
        self.json_btn = QtGui.QPushButton()
        self.json_btn.setMaximumWidth(24)
        self.json_btn.setIcon(self.icon)
        self.json_btn.clicked.connect(lambda: self.button_click(self.jsonFile, '*.json'))

        self.publish_grid.addWidget(self.json_btn, 0, 2, 1, 1)
        self.publish_grid.setRowMinimumHeight(0, self.row_height)

        # abcShaders
        self.abcShaders = StrWidget(node, 'abcShaders', label='', parent=self)
        self.publish_grid.addWidget(QtGui.QLabel('Shaders File'), 1, 0, 1, 1)
        self.publish_grid.addWidget(self.abcShaders, 1, 1, 1, 1)
        self.abc_btn = QtGui.QPushButton()
        self.abc_btn.setMaximumWidth(24)
        self.abc_btn.setIcon(self.icon)
        self.abc_btn.clicked.connect(lambda: self.button_click(self.abcShaders, '*.abc'))

        self.publish_grid.addWidget(self.abc_btn, 1, 2)
        self.publish_grid.setRowMinimumHeight(1, self.row_height)

        self.publish_group.setLayout(self.publish_grid)

        
        #########################################################################################################
        self.layout.addWidget(self.alembic_group)
        self.layout.addWidget(self.geometry_group)
        self.layout.addWidget(self.assignments_group)
        self.layout.addWidget(self.publish_group)                
        self.setLayout(self.layout)

    def setNode(self, node):
        '''
        Set the current node
        '''
        self.node = node

        for i in self.caches.keys():
            self.caches[i].setNode(node)
        self.cacheGeomPath.setNode(node)
        self.cacheSelectionPath.setNode(node)
        self.boundingBoxExtendedMode.setNode(node)
        self.timeOffset.setNode(node)
        self.shadersAssignation.setNode(node)
        self.displacementsAssignation.setNode(node)
        self.attributes.setNode(node)
        self.layersOverride.setNode(node)
        self.shadersNamespace.setNode(node)
        self.geometryNamespace.setNode(node)
        self.jsonFile.setNode(node)
        self.abcShaders.setNode(node)

    def button_click(self, widget, filter_type):
        '''
        '''
        filename = QtGui.QFileDialog.getOpenFileName(filter=filter_type)[0]

        if os.path.isfile(filename):
            widget.valLE.setText(filename)
            widget.updateAttr()

    def addAlembicClicked(self):
        '''
        '''
        ports = cmds.getAttr("%s.cacheFileNames" % (self.node), size=True)
        self.addCache(ports)

    def addCache(self, i):
        '''
        '''
        cache = StrWidget(self.node, 'cacheFileNames[%i]' % i, label='', parent=self)
        self.alembic_grid.addWidget(QtGui.QLabel('Alembic [%i]' % i), i, 0, 1, 1)
        self.alembic_grid.addWidget(cache, i, 1, 1, 1)
        cache_btn = QtGui.QPushButton()
        cache_btn.setMaximumWidth(24)
        cache_btn.setIcon(self.icon)
        cache_btn.clicked.connect(lambda: self.button_click(cache, '*.abc'))
        self.alembic_grid.addWidget(cache_btn, i, 2, 1, 1)
        self.alembic_grid.setRowMinimumHeight(i, self.row_height)

        self.caches[i] = cache             

################################################################################
#Initialize/Update methods:
#   These are the methods that get called to Initialize & install the QT GUI
#   and to update/repoint it to a different node
################################################################################
def getLayout(lay):
    '''
    Get the layout object
    
    @type lay: str
    @param lay: The (full) name of the layout that we need to get
    
    @rtype: QtGui.QLayout (or child)
    @returns: The QLayout object
    '''
    ptr = mui.MQtUtil.findLayout(lay)
    layObj = shiboken.wrapInstance(long(ptr),QtGui.QWidget)
    return layObj
    
def buildQT(lay, node):
    '''
    Build/Initialize/Install the QT GUI into the layout.
    
    @type lay: str
    @param lay: Name of the Maya layout to add the QT GUI to
    @type node: str
    @param node: Name of the node to (initially) connect to the QT GUI
    '''
    mLayout = getLayout(lay)

    #create the GUI/widget
    widg = AEalembicHolderTemplate(node)
      
    #add the widget to the layout
    mLayout.layout().addWidget(widg)
    
def updateQT(lay, node):
    '''
    Update the QT GUI to point to a different node
    
    @type lay: str
    @param lay: Name of the Maya layout to where the QT GUI lives
    @type node: str
    @param node: Name of the new node to connect to the QT GUI
    '''
    mLayout = getLayout(lay)
      
    #find the widget
    for c in range(mLayout.layout().count()):
        widg = mLayout.layout().itemAt(c).widget()
        if isinstance(widg, AEalembicHolderTemplate):
            #found the widget, update the node it's pointing to
            widg.setNode(node)
            break