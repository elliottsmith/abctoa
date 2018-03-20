from pymel.core import *
import maya.cmds as cmds

from milk.shotgun.v1_1.tank import get_context
from alembicHolder.cmds import abcToApi

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
        cmds.symbolButton(image="download_small.png", width=15, height=15, command=self._abcImport)
        cmds.setParent('..')
        cmds.setUITemplate(popTemplate=True)
        cmds.setParent('..')
        self._abcConnect(cacheName)
        cmds.select()

    def _abcConnect(self, cacheName):
        """
        Connect the new control to existing control
        """
        cmds.connectControl("abcpathNameField", self.cache)

    def _abcBrowser(self, args):
        """
        Open file dialog and set the cache attribute
        """
        ret = cmds.fileDialog2(fileFilter="Alembic (*.abc)", fileMode=1, dialogStyle=2, caption="Select Alembic File")
        cmds.setAttr(self.cache, ret[0], type="string")

    def _abcImport(self, args):
        """
        Import the alembic file via abcToApi
        """
        for i in abcToApi.getSelectedAlembicHolder(cls=True):
            i.importAbc()

    def _jsonWidget(self, json):
        """
        Json Path widgets
        """
        self.json = json

        cmds.setUITemplate('attributeEditorTemplate', pushTemplate=True)
        cmds.columnLayout(adjustableColumn=True)
        cmds.rowLayout(numberOfColumns=4, adjustableColumn4=2)
        cmds.text(label="Json Path")
        cmds.textField("jsonpathNameField")
        cmds.symbolButton(image="navButtonBrowse.png", width=15, height=15, command=self._jsonBrowser)
        cmds.symbolButton(image="download_small.png", width=15, height=15, command=self._jsonImport)
        cmds.setParent('..')
        cmds.setUITemplate(popTemplate=True)
        cmds.setParent('..')
        self._jsonConnect(json)
        cmds.select()

    def _jsonConnect(self, json):
        """
        Connect the new control to existing control
        """
        cmds.connectControl("jsonpathNameField", self.json)

    def _jsonBrowser(self, args):
        """
        Open file dialog and set the jsonFile attribute
        """
        ret = cmds.fileDialog2(fileFilter="Json (*.json)", fileMode=1, dialogStyle=2, caption="Select Json File")
        cmds.setAttr(self.json, ret[0], type="string")

    def _jsonImport(self, args):
        """
        Import the json file via abcToApi
        """
        for i in abcToApi.getSelectedAlembicHolder(cls=True):
            i.importJson()

    def _shadersWidget(self, shaders):
        """
        Shaders Path widgets
        """
        self.shaders = shaders

        cmds.setUITemplate('attributeEditorTemplate', pushTemplate=True)
        cmds.columnLayout(adjustableColumn=True)
        cmds.rowLayout(numberOfColumns=4, adjustableColumn4=2)
        cmds.text(label="Shaders Path")
        cmds.textField("shaderspathNameField")
        cmds.symbolButton(image="navButtonBrowse.png", width=15, height=15, command=self._shadersBrowser)
        cmds.symbolButton(image="download_small.png", width=15, height=15, command=self._shadersImport)
        cmds.setParent('..')
        cmds.setUITemplate(popTemplate=True)
        cmds.setParent('..')
        self._shadersConnect(shaders)
        cmds.select()

    def _shadersConnect(self, json):
        """
        Connect the new control to existing control
        """
        cmds.connectControl("shaderspathNameField", self.shaders)

    def _shadersBrowser(self, args):
        """
        Open file dialog and set the shaders attribute
        """
        ret = cmds.fileDialog2(fileFilter="Alembic (*.abc)", fileMode=1, dialogStyle=2, caption="Select Alembic File")
        cmds.setAttr(self.shaders, ret[0], type="string")

    def _shadersImport(self, args):
        """
        Import the shaders file via abcToApi
        """
        for i in abcToApi.getSelectedAlembicHolder(cls=True):
            i.importShaders()

    def buildBody(self, nodeName):
        """
        Build the body of the attribute editor template according to shotgun context
        """
        context = get_context()
        print 'SG Context: %s' % context

        self.beginLayout(name="Cache File", collapse=False)
        self.callCustom(self._abcWidget, self._abcConnect, "cacheFileNames")
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
        self.callCustom(self._jsonWidget, self._jsonConnect, "jsonFile")
        self.callCustom(self._shadersWidget, self._shadersConnect, "abcShaders")             
        self.endLayout()

        render_attrs = ["primaryVisibility", "aiSelfShadows", "castsShadows", "receiveShadows", "motionBlur", "aiVisibleInDiffuse", "aiVisibleInGlossy", "visibleInRefractions", "visibleInReflections", "aiOpaque", "aiMatte", "overrideGlobalShader", "aiTraceSets", "aiSssSetname"]
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
