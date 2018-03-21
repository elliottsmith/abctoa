from pymel.core import *
import maya.cmds as cmds
import functools

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
        mel.AEswatchDisplay(nodeName)
        self.beginScrollLayout()
        self.buildBody(nodeName)
        self.endScrollLayout()

class AEabcMayaShaderTemplate(BaseTemplate):
    """
    Alembic Holder Template
    """

    def _abcWidget(self, cacheName):
        """
        ABC Path widgets
        """
        # fix attr name firstly
        self.cache = cacheName

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
        cmds.connectControl("abcpathNameField", self.cache)

    def _abcBrowser(self, args):
        """
        Open file dialog and set the cache attribute
        """
        ret = cmds.fileDialog2(fileFilter="Alembic (*.abc)", fileMode=1, dialogStyle=2, caption="Select Alembic File")
        cmds.setAttr(self.cache, ret[0], type="string")

    def _setDropDown(self, nodeName):
        """
        Set the values of the shader drop down
        """
        nodeName = nodeName.split('.')[0]

        if cmds.columnLayout("foobar", query=True, exists=True):
            cmds.deleteUI("foobar")
        cmds.columnLayout("foobar")

        attrs = cmds.listAttr("%s.shaders" % nodeName, multi=True)
        shaderFrom = cmds.getAttr("%s.shaderFrom" % nodeName)
        shaderMenu = cmds.optionMenuGrp(label='Shader: ')

        if attrs:
            cmds.menuItem(label="None")

            for attr in attrs:
                index = attr.split('[')[1].replace(']', '')
                at = cmds.getAttr("%s.%s" % (nodeName, attr))
                cmds.menuItem(label=at)

        cmds.optionMenuGrp(shaderMenu, edit=True, changeCommand=functools.partial(self._setDropDownAttr, node=nodeName, menu=shaderMenu))

        if attrs and shaderFrom != "":
            cmds.optionMenuGrp(shaderMenu, edit=True, value=shaderFrom)

    def _setDropDownAttr(self, unused, node, menu):
        """
        Set the shaderFrom attribute after an option is chosen
        """
        selected = cmds.optionMenuGrp(menu, value=True, query=True)
        cmds.setAttr("%s.shaderFrom" % (node), selected, type="string")

    def buildBody(self, nodeName):
        """
        Build the body of the attribute editor template according to shotgun context
        """
        self.beginLayout(name="Alembic Shader", collapse=False)
        self.callCustom(self._abcWidget, self._abcConnect, "shader")
        self.callCustom(self._setDropDown, self._setDropDown, nodeName)
        self.endLayout()

        self.addExtraControls()
