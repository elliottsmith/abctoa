from pymel.core import *
import maya.cmds as cmds
import cask

from maya.OpenMaya import MNodeMessage, MEventMessage, MSelectionList, MItSelectionList, MObject, MGlobal, MDagPath
import json

from milk.shotgun.v1_1.tank import get_context
from alembicHolder.cmds import abcToApi

RED = (1.0, 0.2, 0.2)
GREEN = (0.4, 1.0, 0.4)

class LocalizedTemplate(ui.AETemplate):
    """
    Automatically apply language localizations to template arguments
    """
    def _applyLocalization(self, name):
        if name is not None and len(name)>2 and name[0] == 'k' and name[1].isupper():
            return mel.uiRes('m_' + self.__class__.__name__ + '.' + name)
        return name

    def addControl(self, control, label=None, **kwargs):
        """
        Add localised control to template
        """
        label = self._applyLocalization(label)
        ui.AETemplate.addControl(self, control, label=label, **kwargs)

    def beginLayout(self, name, collapse=True):
        """
        Start layout
        """
        name =  self._applyLocalization(name)
        ui.AETemplate.beginLayout(self, name, collapse=collapse)

class BaseTemplate(LocalizedTemplate):
    def __init__(self, nodeName):
        """
        Base template
        """
        LocalizedTemplate.__init__(self,nodeName)
        self.beginScrollLayout()
        self.buildBody(nodeName)
        self.endScrollLayout()

class AEalembicHolderTemplate(BaseTemplate):
    """
    Alembic Holder Template
    """

    def _refresh(self, *args):
        """
        """
        if os.path.isfile(args[0]):
            bg_color = GREEN
            enable = True
        else:
            bg_color = RED
            enable = False

        cmds.button("%s" % (self.btn), backgroundColor=bg_color, edit=True, enable=enable)       

    def _abcWidget(self, cacheName):
        """
        ABC Path widgets
        """
        # fix attr name firstly
        self.cache = cacheName + "[0]"

        cmds.setUITemplate('attributeEditorTemplate', pushTemplate=True)
        cmds.columnLayout(adjustableColumn=True)
        cmds.rowLayout(numberOfColumns=4, adjustableColumn4=2)
        cmds.text(label="ABC Path")
        cmds.textField("abcpathNameField")
        cmds.symbolButton(image="navButtonBrowse.png", width=15, height=15, command=self._abcBrowser)
        cmds.setParent('..')
        cmds.setUITemplate(popTemplate=True)
        cmds.setParent('..')
        self._abcConnect(cacheName)
        cmds.select()

    def _abcConnect(self, cacheName):
        """
        Connect the new control to existing control
        """
        self.cache = cacheName + "[0]"        
        cmds.connectControl("abcpathNameField", self.cache)

    def _abcBrowser(self, args):
        """
        Open file dialog and set the cache attribute
        """
        ret = cmds.fileDialog2(fileFilter="Alembic (*.abc)", fileMode=1, dialogStyle=2, caption="Select Alembic File")
        if ret:
            selected = abcToApi.getCurrentSelection()
            cmds.setAttr("%s.cacheFileNames[0]" % selected, ret[0], type="string")

    def getNamespaceFromCache(self):

        cache = cmds.getAttr('%s.cacheFileNames[0]' % abcToApi.getCurrentSelection())
        archive = cask.Archive(str(cache))
        top_child = archive.top.children.keys()[0]
        if ':' in top_child:
            nm = top_child.split(':')[0]
        else:
            nm = 'root'            

        ret = cmds.promptDialog(title='Namespace', message='Enter Name:', button=['Ok', 'Cancel'], defaultButton='Ok', cancelButton='Cancel', dismissString='Cancel', text=nm)
        if ret == 'Ok':
            return cmds.promptDialog(query=True, text=True)
        return False

    def _menuCommand(self, command):

        reload(abcToApi)

        if command == 'Localise Lookdev':
            namespace = self.getNamespaceFromCache()
            if namespace:
                for i in abcToApi.getSelectedAlembicHolder(cls=True):
                    i.importLookdev(namespace)
        
        elif command == 'Add Namespace to Assignments':
            namespace = self.getNamespaceFromCache()
            if namespace:
                for i in abcToApi.getSelectedAlembicHolder(cls=True):
                    i.addNamespace(namespace)

        elif command == 'Remove Namespace from Assignments':
            namespace = self.getNamespaceFromCache()
            if namespace:
                for i in abcToApi.getSelectedAlembicHolder(cls=True):
                    i.removeNamespace(namespace)

    def _menuWidget(self, loader):

        cmds.setUITemplate('attributeEditorTemplate', pushTemplate=True)
        cmds.columnLayout(adjustableColumn=False)
        cmds.optionMenuGrp(label="Scripts", cc=self._menuCommand)
        cmds.menuItem(label="Add Namespace to Assignments")
        cmds.menuItem(label="Remove Namespace from Assignments")
        cmds.menuItem(label="Localise Lookdev")
        cmds.setParent('..')
        cmds.setUITemplate(popTemplate=True)
        cmds.setParent('..')
        cmds.select()

    def _menuConnect(self, args):
        pass

    def buildBody(self, nodeName):
        """
        Build the body of the attribute editor template according to shotgun context
        """
        self.beginLayout(name="Cache File", collapse=False)
        self.callCustom(self._abcWidget, self._abcConnect, "cacheFileNames")
        self.addControl(control="updateTransforms", label="Auto update transforms")
        self.addControl(control="cacheGeomPath", label="Geometry Path")
        self.addControl(control="cacheSelectionPath", label="Selection Path")
        self.addControl(control="boundingBoxExtendedMode", label="Bounding Box Extended Mode")
        self.addControl(control="timeOffset", label="Time Offset")
        self.addControl(control="loadAtInit", label="Load At Init")              
        self.endLayout()

        self.beginLayout(name="Shaders and Assignments", collapse=False)
        self.addControl(control="shadersAssignation", label="Shaders Assignation")
        self.addControl(control="displacementsAssignation", label="Displacements Assignation")
        self.addControl(control="attributes", label="Attributes")
        self.addControl(control="layersOverride", label="Layers Override")
        self.addControl(control="shadersNamespace", label="Shaders Namespace")
        self.addControl(control="geometryNamespace", label="Alembic Namespace")        
        self.endLayout()        

        self.beginLayout(name="Utilities", collapse=False)
        self.callCustom(self._menuWidget, self._menuConnect, "")
        self.endLayout()

        render_attrs = ["primaryVisibility", "aiSelfShadows", "castsShadows", "aiReceiveShadows", "motionBlur", "aiVisibleInDiffuse", "aiVisibleInGlossy", "visibleInRefractions", "visibleInReflections", "aiOpaque", "aiMatte", "overrideGlobalShader", "aiTraceSets", "aiSssSetname", "aiUserOptions"]
        self.beginLayout(name="Render Stats", collapse=True)
        self.beginNoOptimize()
        for attr in render_attrs:
            self.addControl(attr)
        self.endNoOptimize()
        self.endLayout()

        self.suppress("blackBox")
        self.suppress("borderConnections")
        self.suppress("isHierarchicalConnection")
        self.suppress("publishedNodeInfo")
        self.suppress("publishedNodeInfo.publishedNode")
        self.suppress("publishedNodeInfo.isHierarchicalNode")
        self.suppress("publishedNodeInfo.publishedNodeType")
        self.suppress("rmbCommand")
        self.suppress("templateName")
        self.suppress("templatePath")
        self.suppress("viewName")
        self.suppress("iconName")
        self.suppress("viewMode")
        self.suppress("templateVersion")
        self.suppress("uiTreatment")
        self.suppress("customTreatment")
        self.suppress("creator")
        self.suppress("creationDate")
        self.suppress("containerType")
        self.suppress("center")
        self.suppress("boundingBoxCenterX")
        self.suppress("boundingBoxCenterY")
        self.suppress("boundingBoxCenterZ")
        self.suppress("matrix")
        self.suppress("inverseMatrix")
        self.suppress("worldMatrix")
        self.suppress("worldInverseMatrix")
        self.suppress("parentMatrix")
        self.suppress("parentInverseMatrix")
        self.suppress("visibility")
        self.suppress("intermediateObject")
        self.suppress("template")
        self.suppress("ghosting")
        self.suppress("instObjGroups")
        self.suppress("instObjGroups.objectGroups")
        self.suppress("instObjGroups.objectGroups.objectGrpCompList")
        self.suppress("instObjGroups.objectGroups.objectGroupId")
        self.suppress("instObjGroups.objectGroups.objectGrpColor")
        self.suppress("renderInfo")
        self.suppress("identification")
        self.suppress("layerRenderable")
        self.suppress("layerOverrideColor")
        self.suppress("renderLayerInfo")
        self.suppress("renderLayerInfo.renderLayerId")
        self.suppress("renderLayerInfo.renderLayerRenderable")
        self.suppress("renderLayerInfo.renderLayerColor")
        self.suppress("ghostingControl")
        self.suppress("ghostCustomSteps")
        self.suppress("ghostPreSteps")
        self.suppress("ghostPostSteps")
        self.suppress("ghostStepSize")
        self.suppress("ghostFrames")
        self.suppress("ghostColorPreA")
        self.suppress("ghostColorPre")
        self.suppress("ghostColorPreR")
        self.suppress("ghostColorPreG")
        self.suppress("ghostColorPreB")
        self.suppress("ghostColorPostA")
        self.suppress("ghostColorPost")
        self.suppress("ghostColorPostR")
        self.suppress("ghostColorPostG")
        self.suppress("ghostColorPostB")
        self.suppress("ghostRangeStart")
        self.suppress("ghostRangeEnd")
        self.suppress("ghostDriver")
        self.suppress("renderType")
        self.suppress("renderVolume")
        self.suppress("visibleFraction")
        self.suppress("motionBlur")
        self.suppress("maxVisibilitySamplesOverride")
        self.suppress("maxVisibilitySamples")
        self.suppress("geometryAntialiasingOverride")
        self.suppress("antialiasingLevel")
        self.suppress("shadingSamplesOverride")
        self.suppress("shadingSamples")
        self.suppress("maxShadingSamples")
        self.suppress("volumeSamplesOverride")
        self.suppress("volumeSamples")
        self.suppress("depthJitter")
        self.suppress("ignoreSelfShadowing")
        self.suppress("referenceObject")
        self.suppress("compInstObjGroups")
        self.suppress("compInstObjGroups.compObjectGroups")
        self.suppress("compInstObjGroups.compObjectGroups.compObjectGrpCompList")
        self.suppress("compInstObjGroups.compObjectGroups.compObjectGroupId")
        self.suppress("tweak")
        self.suppress("relativeTweak")
        self.suppress("controlPoints")
        self.suppress("controlPoints.xValue")
        self.suppress("controlPoints.yValue")
        self.suppress("controlPoints.zValue")
        self.suppress("weights")
        self.suppress("tweakLocation")
        self.suppress("blindDataNodes")
        self.suppress("uvPivot")
        self.suppress("uvPivotX")
        self.suppress("uvPivotY")
        self.suppress("uvSet")
        self.suppress("uvSet.uvSetName")
        self.suppress("uvSet.uvSetPoints")
        self.suppress("uvSet.uvSetPoints.uvSetPointsU")
        self.suppress("uvSet.uvSetPoints.uvSetPointsV")
        self.suppress("uvSet.uvSetTweakLocation")
        self.suppress("currentUVSet")
        self.suppress("displayImmediate")
        self.suppress("displayColors")
        self.suppress("displayColorChannel")
        self.suppress("currentColorSet")
        self.suppress("colorSet")
        self.suppress("colorSet.colorName")
        self.suppress("colorSet.clamped")
        self.suppress("colorSet.representation")
        self.suppress("colorSet.colorSetPoints")
        self.suppress("colorSet.colorSetPoints.colorSetPointsR")
        self.suppress("colorSet.colorSetPoints.colorSetPointsG")
        self.suppress("colorSet.colorSetPoints.colorSetPointsB")
        self.suppress("colorSet.colorSetPoints.colorSetPointsA")
        self.suppress("ignoreHwShader")
        self.suppress("doubleSided")
        self.suppress("opposite")
        self.suppress("smoothShading")
        self.suppress("boundingBoxScale")
        self.suppress("boundingBoxScaleX")
        self.suppress("boundingBoxScaleY")
        self.suppress("boundingBoxScaleZ")
        self.suppress("featureDisplacement")
        self.suppress("initialSampleRate")
        self.suppress("extraSampleRate")
        self.suppress("textureThreshold")
        self.suppress("normalThreshold")
        self.suppress("displayHWEnvironment")
        self.suppress("collisionOffsetVelocityIncrement")
        self.suppress("collisionOffsetVelocityIncrement.collisionOffsetVelocityIncrement_Position")
        self.suppress("collisionOffsetVelocityIncrement.collisionOffsetVelocityIncrement_FloatValue")
        self.suppress("collisionOffsetVelocityIncrement.collisionOffsetVelocityIncrement_Interp")
        self.suppress("collisionDepthVelocityIncrement")
        self.suppress("collisionDepthVelocityIncrement.collisionDepthVelocityIncrement_Position")
        self.suppress("collisionDepthVelocityIncrement.collisionDepthVelocityIncrement_FloatValue")
        self.suppress("collisionDepthVelocityIncrement.collisionDepthVelocityIncrement_Interp")
        self.suppress("collisionOffsetVelocityMultiplier")
        self.suppress("collisionOffsetVelocityMultiplier.collisionOffsetVelocityMultiplier_Position")
        self.suppress("collisionOffsetVelocityMultiplier.collisionOffsetVelocityMultiplier_FloatValue")
        self.suppress("collisionOffsetVelocityMultiplier.collisionOffsetVelocityMultiplier_Interp")
        self.suppress("collisionDepthVelocityMultiplier")
        self.suppress("collisionDepthVelocityMultiplier.collisionDepthVelocityMultiplier_Position")
        self.suppress("collisionDepthVelocityMultiplier.collisionDepthVelocityMultiplier_FloatValue")
        self.suppress("collisionDepthVelocityMultiplier.collisionDepthVelocityMultiplier_Interp")
        self.suppress("time")
        self.suppress("shaders")

        self.addExtraControls()