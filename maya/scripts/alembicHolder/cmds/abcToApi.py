import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import cask
import json
import ast
import os

class alembicHolderClass():
    def __init__(self, data):
        """
        alembicHolderClass holding alembicHolder attribute data
        """

        self.data = data

    def printMessage(self, msg_type, msg):
        """
        printMessage - generic message printing
        params:
            msg_type - print prefix
            msg - message
        """

        print "\n%s: %s" % (msg_type, msg)

    def setAttr(self, attr, value, attr_type="string"):
        """
        setAttr - generic setAttr method
        params:
            attr - attribute name
            value - attribute value
            attr_type - attribute type
        """

        try:
            if attr_type:
                cmds.setAttr("%s.%s" % (self.data['shapeNode'], attr), value, type=attr_type)
            else:
                cmds.setAttr("%s.%s" % (self.data['shapeNode'], attr), value)
        except Exception as e:
            self.printMessage("Exception", e)

    def getAttr(self, attr):
        """
        getAttr - generic getAttr method
        params:
            attr - attribute name
        """

        try:
            return cmds.getAttr("%s.%s" % (self.data['shapeNode'], attr))
        except Exception as e:
            self.printMessage("Exception", e)

    def attrExists(self, attr):
        """
        attrExists - check if an attribute exists
        params:
            attr - attribute to check
        """

        return cmds.objExists("%s.%s" % (self.data['shapeNode'], attr))

    def getConnectedShaders(self):
        """
        getConnectedShaders - returns a list of shaders / displacements connected the alembicHolder
        """

        connected = []
        for connections in pm.listConnections(self.data['shapeNode'], plugs=True, connections=True):
            if cmds.getClassification(connections[-1].nodeType(), satisfies="shader"):
                connected.append(connections[-1].node())
        return connected

    def slashesToPipes(self):
        """
        slashesToPipes - utility method
        """

        if self.getAttr(attr='cacheGeomPath') != "":
            
            # cleanup the attribute value
            value = self.getAttr(attr='cacheGeomPath').lstrip('["').rstrip('"]').replace('/', '|')
            self.setAttr(attr='cacheGeomPath', value=value)

    def validateDictionaries(self):
        """
        validateDictionaries - reads in the values of the attribute editor and attempts to read them as json dicts
        if it fails, raise an error to indicate why the string isnt a valid dictoinary
        """
        self.printMessage("Validate Dictionaries", self.data['shapeNode'])

        message = ''
        shader_dict = {}
        disp_dict = {}
        attr_dict = {}
        layers_dict = {}
        namespace_str = ''

        shader_attr = self.getAttr("shadersAssignation")
        disp_attr = self.getAttr("displacementsAssignation")
        attr_attr = self.getAttr("attributes")
        layers_attr = self.getAttr("layersOverride")
        namespace_attr = self.getAttr("shadersNamespace")

        shaders = None
        disp = None
        attr = None
        layers = None
        namespace = None

        fail = False

        if shader_attr:
            try:
                shader_dict = json.loads(shader_attr)
                if shader_dict.has_key('shaders'):
                    fail = True
                    shaders = 'please remove the shaders key'
            except ValueError as e:
                shaders = e
                fail = True

        if disp_attr:
            try:
                disp_dict = json.loads(disp_attr)
                if disp_dict.has_key('displacement'):
                    fail = True
                    disp = 'please remove the displacement key'
            except ValueError as e:
                disp = e
                fail = True

        if attr_attr:
            try:
                attr_dict = json.loads(attr_attr)
                if attr_dict.has_key('attributes'):
                    fail = True
                    attr = 'please remove the attributes key'
            except ValueError as e:
                attr = e
                fail = True

        if layers_attr:
            try:
                layers_dict = json.loads(layers_attr)
                if layers_dict.has_key('layers'):
                    fail = True
                    layers = 'please remove the layers key'
            except ValueError as e:
                layers = e
                fail = True

        if namespace_attr:
            try:
                namespace_str = ast.literal_eval(namespace_attr)
                if type(namespace_attr) == dict:
                    if namespace_attr.has_key('namespace'):
                        fail = True
                        namespace = 'please remove the namespace key'

            except ValueError as e:
                namespace = e
                fail = True

        if not fail:
            msg = self.data['shapeNode']
            self.printMessage("Valid", msg)
        else:
            if shaders:
                msg = "%s.shadersAssignation : %s" % (self.data['shapeNode'], shaders)
                self.printMessage("Invalid", msg)

            if disp:
                msg = "%s.displacementsAssignation : %s" % (self.data['shapeNode'], disp)
                self.printMessage("Invalid", msg)                

            if attr:
                msg = "%s.attributes : %s" % (self.data['shapeNode'], attr)
                self.printMessage("Invalid", msg)

            if layers:
                msg = "%s.layersOverride : %s" % (self.data['shapeNode'], layers)
                self.printMessage("Invalid", msg)                

            if namespace:
                msg = "%s.shadersNamespace : %s" % (self.data['shapeNode'], namespace)
                self.printMessage("Invalid", msg)                
    
    def importAbc(self, parent_transform=None):
        """
        importAbc - import alembic cache as maya geometry
        params:
            parent_transform - reparent the new maya geometry under alembicHolder transform
        """
        self.printMessage("Import Abc", self.data['shapeNode'])

        if self.data['cacheFileNameAttr'] != '':
            if os.path.isfile(self.data['cacheFileNameAttr']):

                # prompt for parent_transform if not specified
                if parent_transform == None:
                    res = cmds.confirmDialog( title='Transform', message='Do you want to parent the incoming geo to the alembicHolder transform?', button=['Yes','No', 'Cancel'], defaultButton='Yes', cancelButton='Cancel', dismissString='No' )

                    if res == 'Yes':
                        parent_transform = True
                    elif res == 'No':
                        parent_transform = False
                    else:
                        return

                if parent_transform:
                    cmds.AbcImport(self.data['cacheFileNameAttr'], reparent=self.data['transformNode'])
                else:
                    cmds.AbcImport(self.data['cacheFileNameAttr'])

                msg = self.data['cacheFileNameAttr']
                self.printMessage("Imported", msg)
            else:
                msg = self.data['cacheFileNameAttr']
                self.printMessage("Missing", msg)                
        else:
            self.printMessage("Empty Attribute", "")

    def importJson(self, namespace=None):
        """
        importJson - import json assignment file as live scene based assignments
        params:
            namespace - set the shaders namespace attribute
        """
        self.printMessage("Import Json", self.data['shapeNode'])

        if self.data['jsonFileAttr']:

            if os.path.isfile(self.data['jsonFileAttr']):
                with open(self.data['jsonFileAttr']) as json_file:
                    json_data = json.load(json_file)

                if json_data.has_key('shaders'):
                    self.setAttr(attr='shadersAssignation', value=json.dumps(json_data['shaders']))
                if json_data.has_key('attributes'):
                    self.setAttr(attr='attributes', value=json.dumps(json_data['attributes']))
                if json_data.has_key('displacement'):
                    self.setAttr(attr='displacementsAssignation', value=json.dumps(json_data['displacement']))
                if json_data.has_key('layers'):
                    self.setAttr(attr='layersOverride', value=json.dumps(json_data['layers']))
                if json_data.has_key('namespace'):
                    if namespace:
                        self.setAttr(attr='shadersNamespace', value=json.dumps(json_data['namespace']))

                self.setAttr(attr='forceReload', value=1, attr_type=None)
                self.setAttr(attr='jsonFile', value='')

                msg = self.data['jsonFileAttr']
                self.printMessage("Imported", msg)
            
            else:
                msg = self.data['jsonFileAttr']
                self.printMessage("Missing", msg)

        else:
            msg = self.data['jsonFileAttr']
            self.printMessage("Empty Attribute", msg)

    def importShaders(self, namespace=None):
        """
        importShaders - imports external alembic shaders as maya shaders
        params:
            namespace - import the shaders under given namespace
        """
        self.printMessage("Import Shaders", self.data['shapeNode'])

        if self.data['abcShadersAttr'] != '':

            # real simple way of finding the associated maya file
            abcfile = self.data['abcShadersAttr']
            mayafile = abcfile.replace('.abc', '.ma')

            if os.path.isfile(mayafile):
                
                if namespace:
                    # if the namespace param is just a bool, make a namespace from the incoming alembic filename
                    if isinstance(namespace, bool):
                        namespace = mayafile.split(os.path.sep)[-1].split('.')[0]
                    imported_shaders = cmds.file(mayafile, i=True, rnn=True, mergeNamespacesOnClash=False, namespace=namespace)
                
                else:
                    imported_shaders = cmds.file(mayafile, i=True, rnn=True, mergeNamespacesOnClash=False)

                self.setAttr("abcShaders", "")

                # reset selection back to alembicHolder
                cmds.select(self.data['shapeNode'])

                msg = self.data['abcShadersAttr']
                self.printMessage("Imported", msg)

            else:
                msg = self.data['abcShadersAttr']
                self.printMessage("Missing", msg)
        else:
            msg = self.data['abcShadersAttr']
            self.printMessage("Empty Attribute", msg)

    def writeAbcShaders(self, shader_out_path=""):
        """
        writeAbcShaders - export all shaders connected to the alembicHolder. exports both an alembic and maya file
        params:
            shader_out_path - path to export the alembic shaders to
        """
        self.printMessage("Export Shaders", self.data['shapeNode'])

        try:
            # export the alembic file
            cmds.abcCacheExport(f=shader_out_path, node=self.data['shapeNode'])

            # export the maya file
            shadersSelection = self.getConnectedShaders()
            cmds.select(shadersSelection,r=True,noExpand=True)
            cmds.file(shader_out_path, f=True,options='v=0', type='mayaAscii', pr=True, es=True)

            # reselect the shape
            cmds.select(self.data['shapeNode'])

            self.printMessage("Exported", shader_out_path)
            return "Exported: %s" % shader_out_path

        except Exception, e:
            self.printMessage("Export Failed", shader_out_path)
            return "Export Shaders Failed: %s" % shader_out_path

    def writeJson(self, namespace=None, json_out_path=""):
        """
        writeJson - write json assignments
        params:
            namespace - 
            json_out_path - path to export the json assignments to

        """
        self.printMessage("Export Assignments", self.data['shapeNode'])

        assignations = {}

        try:
            if self.attrExists('shadersAssignation'):
                if self.getAttr('shadersAssignation'):
                    assignations["shaders"] = json.loads(self.getAttr('shadersAssignation'))

            if self.attrExists('attributes'):
                if self.getAttr('attributes'):
                    assignations["attributes"] = json.loads(self.getAttr('attributes'))

            if self.attrExists('displacementsAssignation'):
                if self.getAttr('displacementsAssignation'):
                    assignations["displacement"] = json.loads(self.getAttr('displacementsAssignation'))

            if self.attrExists('layersOverride'):
                if self.getAttr('layersOverride'):
                    assignations["layers"] = json.loads(self.getAttr('layersOverride'))

            if namespace:
                assignations["namespace"] = namespace
            else :
                assignations["namespace"] = self.data['shapeNode'].replace(":", "_").replace("|", "_")

            # now write out json
            with open(json_out_path, 'w') as outfile:
                json.dump(assignations, outfile, separators=(',',':'), sort_keys=True, indent=4)
            
            self.printMessage("Exported", json_out_path)
            return "Exported: %s" % json_out_path

        except Exception, e:
            self.printMessage("Export Failed", json_out_path)
            return "Export Json Failed: %s" % json_out_path

    def checkConnections(self):
        """
        checkConnections - check the connections between shaders and the alembicHolder node
        """
        self.printMessage("Check Connections", self.data['shapeNode'])

    def makeConnections(self):
        """
        """
        self.printMessage("Make Connections", self.data['shapeNode'])

    def breakConnections(self):
        """
        breakConnections - break all connections between shaders and the alembicHolder node
        """
        self.printMessage("Break Connections", self.data['shapeNode'])

        for connections in pm.listConnections(self.data['shapeNode'], plugs=True, connections=True):
            if cmds.getClassification(connections[-1].nodeType(), satisfies="shader"):
                pm.disconnectAttr(str(connections[-1]), str(connections[0]))
                msg = "%s > %s" % (str(connections[-1]), str(connections[0]))
                self.printMessage("Break", msg)

def getSelected(cls=False, filter_string=""):
    """
    getSelected - function to read attributes from a selected alembicHolder nodes
    params:
        cls - return attribute data as an abcClass instance or as a simple dictionary
    """

    selected = pm.ls(sl=True, visible=True, l=True)
    selected_abc = pm.ls(sl=True, dag=True, leaf=True, visible=True, type='alembicHolder', l=True)

    if filter_string != "":
        filter_string = filter_string.replace('*', '')
        temp = []
        for i in selected_abc:
            if filter_string in str(i):
                temp.append(i)
        selected_abc = temp
    
    abcnodes = []
    non_abcnodes = []

    for i in selected:
        if i not in selected_abc:
            x = False
            children = i.getChildren()
            for each in children:
                if each.nodeType() == 'alembicHolder':
                    x = True
            if not x:
                non_abcnodes.append(i)

    abcnodes = selected_abc
    abclist = []

    for node in abcnodes:
        trans = node.getParent()
        data = {}
        
        data['transformNode'] = str(trans)
        data['shapeNode'] = str(node)

        # shape attributes
        data["shadersAssignationAttr"] = pm.getAttr("%s.shadersAssignation" % node)
        data["attributesAttr"] = pm.getAttr("%s.attributes" % node)
        data["displacementsAssignationAttr"] = pm.getAttr("%s.displacementsAssignation" % node)
        data["layersOverrideAttr"] = pm.getAttr("%s.layersOverride" % node)
        data["shadersNamespaceAttr"] = pm.getAttr("%s.shadersNamespace" % node)

        data["abcShadersAttr"] = pm.getAttr("%s.abcShaders" % node)
        data["jsonFileAttr"] = pm.getAttr("%s.jsonFile" % node)

        data["cacheFileNameAttr"] = str(pm.getAttr("%s.cacheFileNames[0]" % node))

        # transform attributes
        data["translateXAttr"] = pm.getAttr("%s.translateX" % trans)
        data["translateYAttr"] = pm.getAttr("%s.translateY" % trans)
        data["translateZAttr"] = pm.getAttr("%s.translateZ" % trans)

        data["rotateXAttr"] = pm.getAttr("%s.rotateX" % trans)
        data["rotateYAttr"] = pm.getAttr("%s.rotateY" % trans)
        data["rotateZAttr"] = pm.getAttr("%s.rotateZ" % trans)
        
        data["scaleXAttr"] = pm.getAttr("%s.scaleX" % trans)
        data["scaleYAttr"] = pm.getAttr("%s.scaleY" % trans)
        data["scaleZAttr"] = pm.getAttr("%s.scaleZ" % trans)

        # non attributes

        # read the scene shaders
        data['sceneShaders'] = cmds.ls( mat=True )

        if os.path.isfile(data['cacheFileNameAttr']):
            # read the shapes in the abc file
            cache = data['cacheFileNameAttr']
            archive = cask.Archive(cache)
            shapes = cask.find(archive.top, ".*Shape")
            data['abcShapes'] = [i.name for i in shapes]

            # read the shaders from the abc file
            data['abcShaderList'] = None
            if data["abcShadersAttr"]:
                shaders = []
                archive = cask.Archive(str(data["abcShadersAttr"]))
                keys = archive.top.children['materials'].children.keys()
                for k in keys:
                    shaders.append(k)
                data['abcShaderList'] = shaders

            # read the shaders needed for assignment from json file
            data['jsonFileShaders'] = None
            if data['jsonFileAttr']:
                temp = []
                with open(str(data['jsonFileAttr'])) as json_file:
                    json_data = json.load(json_file)
                
                if json_data.has_key('shaders'):
                    json_shaders = json_data['shaders'].keys()
                    # json_shaders = [i.split('.message')[0] for i in json_shaders]
                    data['jsonFileShaders'] = json_shaders

                    for shd in json_data['shaders']:
                        # loop over shapes in json[shader], if those shapes are in the abc file, add them to data dict
                        for shp in json_data['shaders'][shd]:
                            if shp in data['abcShapes']:
                                if shd not in temp:
                                    temp.append(shd)

                    data['actualJsonFileShaders'] = temp

            data['assignedShaders'] = None
            if data['shadersAssignationAttr']:
                temp = []
                try:
                    # x = ast.literal_eval(data['shadersAssignation']).keys()
                    json_data = json.loads(data['shadersAssignationAttr'])
                    if json_data.has_key('shaders'):
                        for shd in json_data['shaders']:
                            # loop over shapes in json[shader], if those shapes are in the abc file, add them to data dict
                            for shp in json_data['shaders'][shd]:
                                if shp in data['abcShapes']:
                                    if shd not in temp:
                                        temp.append(shd)

                    data['actualAssignedShaders'] = temp
                    data['assignedShaders'] = json_data

                except ValueError as e:
                    pass

            # DISPLACEMENTS
            data['jsonFileDisp'] = None
            if data['jsonFileAttr']:
                with open(str(data['jsonFileAttr'])) as json_file:
                    json_data = json.load(json_file)
                if json_data.has_key('displacement'):
                    json_disp = json_data['displacement'].keys()
                    json_disp = [i.split('.message')[0] for i in json_disp]
                    data['jsonFileDisp'] = json_disp

            data['displacementsAssignation'] = None
            if data['displacementsAssignationAttr'] != None:
                try:
                    json_data = json.loads(data['displacementsAssignationAttr']).keys()
                    json_data = [i.split('.message')[0] for i in json_data]
                    data['displacementsAssignation'] = json_data
                except:
                    pass

            abclist.append(data)
        else:
            print "Missing: %s" % data['cacheFileNameAttr']
    
    if not cls:
        return abclist
    else:
        cls_list = []
        for i in abclist:
            cls_list.append(alembicHolderClass(i))
        return cls_list
