
# sys libs
import json
import ast
import os
import logging

# maya libs
import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
from maya.OpenMaya import MSelectionList, MObject, MGlobal

# milk libs
from mayautils.v1_2.tank import find_shader_package_from_shader_file
import cask

class alembicHolderClass():
    def __init__(self, data, logger):
        """
        alembicHolderClass holding alembicHolder attribute data
        """
        self.data = data
        self.logger = logger

    def findAttributes(self, assignations, attribute):
        """
        Args:
            assignations (dict): dictionary holding assignments
            attribute (str): attribute string to check

        check if an attribute exists and isnt empty
        """
        if self.objExists(attribute):
            if self.getAttr(attribute):
                assignations[attribute] = json.loads(self.getAttr(attribute))
        return assignations

    def addNamespace(self, namespace):
        """
        Add a namespace to all assignments

        Args:
            namespace (str): namespace string to add to assignments        
        """
        assignations = {}
        assignations = self.findAttributes(assignations, 'shadersAssignation')
        assignations = self.findAttributes(assignations, 'displacementsAssignation')
        assignations = self.findAttributes(assignations, 'layersOverride')
        assignations = self.findAttributes(assignations, 'attributes')

        #########################################################################################################################
        if assignations.has_key('shadersAssignation'):
            for shader in assignations['shadersAssignation'].keys():
                nm_values = []

                for value in assignations['shadersAssignation'][shader]:
                    if value != '/':
                        splits = value.split('/')
                        new_namespace = '/%s:' % namespace
                        nm_values.append(new_namespace.join(splits))
                    else:
                        nm_values.append(value)

                assignations['shadersAssignation'][shader] = nm_values  
        
        #########################################################################################################################
        if assignations.has_key('displacementsAssignation'):           
            for shader in assignations['displacementsAssignation']:
                nm_values = []

                for value in assignations['displacementsAssignation'][shader]:
                    if value != '/':
                        splits = value.split('/')
                        new_namespace = '/%s:' % namespace
                        nm_values.append(new_namespace.join(splits))
                    else:
                        nm_values.append(value)

                assignations['displacementsAssignation'][shader] = nm_values  

        #########################################################################################################################
        if assignations.has_key('attributes'):
            for geo in assignations['attributes'].keys():
                if geo != '/':
                    splits = geo.split('/')
                    new_namespace = '/%s:' % namespace
                    assignations['attributes'][new_namespace.join(splits)] = assignations['attributes'].pop(geo)
                else:
                    assignations['attributes'][geo] = assignations['attributes'].pop(geo)

        #########################################################################################################################
        if assignations.has_key('layersOverride'):           
            for layer in assignations['layersOverride']:
                layer = assignations['layersOverride'][layer]

                # displacements
                if layer.has_key('displacements'):
                    disp = layer['displacements']

                    for key in disp.keys():
                        nm_values = []
                        
                        for value in disp[key]:
                            if value != '/':
                                splits = value.split('/')
                                new_namespace = '/%s:' % namespace
                                nm_values.append(new_namespace.join(splits))
                            else:
                                nm_values.append(value)
                        disp[key] = nm_values

                # shaders
                if layer.has_key('shaders'):
                    disp = layer['shaders']

                    for key in disp.keys():
                        nm_values = []

                        for value in disp[key]:
                            if value != '/':
                                splits = value.split('/')
                                new_namespace = '/%s:' % namespace
                                nm_values.append(new_namespace.join(splits))
                            else:
                                nm_values.append(value)

                        disp[key] = nm_values 

                # properties
                if layer.has_key('properties'):
                    disp = layer['properties']

                    for key in disp.keys():
                        if key != '/':
                            splits = key.split('/')
                            new_namespace = '/%s:' % namespace
                            disp[new_namespace.join(splits)] = disp.pop(key)
                        else:
                            disp[key] = disp.pop(key)

        #########################################################################################################################
        if assignations.has_key('shadersAssignation'):
            self.setAttr(attr='shadersAssignation', value=json.dumps(assignations['shadersAssignation']))
        if assignations.has_key('attributes'):
            self.setAttr(attr='attributes', value=json.dumps(assignations['attributes']))
        if assignations.has_key('displacementsAssignation'):
            self.setAttr(attr='displacementsAssignation', value=json.dumps(assignations['displacementsAssignation']))
        if assignations.has_key('layersOverride'):
            self.setAttr(attr='layersOverride', value=json.dumps(assignations['layersOverride']))

    def removeNamespace(self, namespace):
        """
        Remove a namespace from all assignments

        Args:
            namespace (str): namespace string to remove from assignments
        """
        assignations = {}
        assignations = self.findAttributes(assignations, 'shadersAssignation')
        assignations = self.findAttributes(assignations, 'displacementsAssignation')
        assignations = self.findAttributes(assignations, 'layersOverride')
        assignations = self.findAttributes(assignations, 'attributes')

        #########################################################################################################################
        if assignations.has_key('shadersAssignation'):
            for shader in assignations['shadersAssignation'].keys():
                nm_values = []

                for value in assignations['shadersAssignation'][shader]:
                    no_namespace = value.replace('%s:' % namespace, '')
                    nm_values.append(no_namespace)

                assignations['shadersAssignation'][shader] = nm_values

        #########################################################################################################################
        if assignations.has_key('displacementsAssignation'):
            for shader in assignations['displacementsAssignation'].keys():
                nm_values = []

                for value in assignations['displacementsAssignation'][shader]:
                    no_namespace = value.replace('%s:' % namespace, '')
                    nm_values.append(no_namespace)

                assignations['displacementsAssignation'][shader] = nm_values

        #########################################################################################################################
        if assignations.has_key('attributes'):
            for geo in assignations['attributes'].keys():
                no_namespace = geo.replace('%s:' % namespace, '')
                assignations['attributes'][no_namespace] = assignations['attributes'].pop(geo)

        #########################################################################################################################
        for layer in assignations['layersOverride']:
            layer = assignations['layersOverride'][layer]

            if layer.has_key('displacements'):
                disp = layer['displacements']
                for key in disp.keys():

                    vals = disp[key]
                    nm_values = []
                    for v in vals:
                        t = v.replace('%s:' % namespace, '')
                        nm_values.append(t)

                    disp[key] = nm_values

            if layer.has_key('shaders'):
                disp = layer['shaders']
                for key in disp.keys():

                    vals = disp[key]
                    nm_values = []
                    for v in vals:
                        t = v.replace('%s:' % namespace, '')
                        nm_values.append(t)

                    disp[key] = nm_values 

            if layer.has_key('properties'):
                disp = layer['properties']
                for key in disp.keys():
                    t = key.replace('%s:' % namespace, '')
                    disp[t] = disp.pop(key)

        #########################################################################################################################
        if assignations.has_key('shadersAssignation'):
            self.setAttr(attr='shadersAssignation', value=json.dumps(assignations['shadersAssignation']))
        if assignations.has_key('attributes'):
            self.setAttr(attr='attributes', value=json.dumps(assignations['attributes']))
        if assignations.has_key('displacementsAssignation'):
            self.setAttr(attr='displacementsAssignation', value=json.dumps(assignations['displacementsAssignation']))
        if assignations.has_key('layersOverride'):
            self.setAttr(attr='layersOverride', value=json.dumps(assignations['layersOverride']))

    def importLookdev(self, namespace=':'):
        """
        Import both json and alembic shaders file. Ensure the imported shaders are connected the alembicHolder node.

        Args:
            namespace (str): namespace string to import lookdev under
        """
        self.logger.info("Import Lookdev")

        if self.importShaders(namespace):
            if self.importJson(namespace):
                if self.reconnectLookdev(namespace):
                    return True                    
        return False

    def importJson(self, namespace=':'):
        """
        Import json assignment file as live scene based assignments on the alembicHolder.

        Args:
            namespace (str):  When importing, override the default namespace
        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self.logger.info("Import Json")

        if self.data['jsonFileAttr']:

            if os.path.isfile(self.data['jsonFileAttr']):
                try:
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

                    self.setAttr(attr='forceReload', value=1, attr_type=None)
                    self.setAttr(attr='jsonFile', value='')

                    self.logger.info("Imported : %s" % self.data['jsonFileAttr'])
                    json_file.close()
                    return True
                
                except Exception, e:
                    self.logger.error("Import Json Error : %s" % e)
                    return False
            else:
                self.logger.error("Missing file : %s" % self.data['jsonFileAttr'])
                return False
        else:
            self.logger.info("Empty attribute : %s.jsonFile" % self.data['shapeNode'])
            return False

    def importShaders(self, namespace=':'):
        """
        Import external alembic shaders as maya shaders
        
        Args:
            namespace (str):  When importing, override the default namespace
        Returns:
            list: The imported shaders
            bool: False if failed
        """
        self.logger.info("Import Shaders")

        if self.data['abcShadersAttr']:

            abcfile = self.data['abcShadersAttr']
            
            # shotgun query for maya file
            mayafile = find_shader_package_from_shader_file(file_path=abcfile, file_type='ma')
            if mayafile != {}:
                mayafile = mayafile['ma']
                self.logger.debug("Found maya shader file: %s" % mayafile)
            else:
                localfile = abcfile.replace('.abc', '.ma')
                if os.path.isfile(localfile):
                    mayafile = localfile
                    self.logger.debug("Found maya shader file: %s" % mayafile)
                else:
                    self.logger.error("Missing file : %s" % self.data['abcShadersAttr'])
                    return False

            if os.path.isfile(mayafile):
                try:                
                    imported_shaders = cmds.file(mayafile, i=True, returnNewNodes=True, renameAll=True, mergeNamespacesOnClash=True, namespace=namespace)
                    self.setAttr("abcShaders", "")
                    self.logger.debug("Imported under %s namespace" % namespace)

                    # reset selection back to alembicHolder
                    cmds.select(self.data['shapeNode'])
                    self.logger.info("Imported : %s" % self.data['abcShadersAttr'])
                    return True

                except Exception, e:
                    self.logger.error("Import Json Error : %s" % e)
                    return False
            else:
                self.logger.error("Missing file : %s" % self.data['abcShadersAttr'])
                return False
        else:
            self.logger.info("Empty attribute : %s.abcShadersAttr" % self.data['shapeNode'])
            return False

    def breakConnections(self):
        """
        Break shader connections to the alembicHolder node
        """
        for connections in pm.listConnections(self.data['shapeNode'], plugs=True, connections=True):
            # if connections[-1].nodeType() in ['shadingEngine', 'displacementShader']:
            if cmds.getClassification(connections[-1].nodeType(), satisfies="shader"):
                pm.disconnectAttr(str(connections[-1]), str(connections[0]))
                self.logger.info("Break Connection : %s > %s" % (str(connections[-1]), str(connections[0])))

    def reconnectLookdev(self, namespace):
        """
        The json file and alembic shaders have been imported, now connect the imported shaders to the alembicHolder node
        and if necessary fix any namespace issues.

        Args:
            namespace (str): namespace
        """
        self.logger.debug("Reconnecting imported lookev")

        # lets break connections first
        self.breakConnections()

        assignations = {}

        if self.objExists('shadersAssignation'):
            shadersAssignation = self.getAttr('shadersAssignation')
            if shadersAssignation:
                assignations["shaders"] = json.loads(shadersAssignation)

        if self.objExists('displacementsAssignation'):
            displacementsAssignation = self.getAttr('displacementsAssignation')
            if displacementsAssignation:
                assignations["displacement"] = json.loads(displacementsAssignation)

        if self.objExists('layersOverride'):
            layersOverride = self.getAttr('layersOverride')
            if layersOverride:
                assignations["layers"] = json.loads(layersOverride)

        # fix the attribute editor
        fixed = {'shaders' : {}, 'displacement' : {}, 'layers' : {}}
        attrs_to_connect = []
        if assignations.has_key('shaders'):
            for shader in assignations['shaders']:
                if namespace != ':':
                    fixed['shaders']['%s:%s' % (namespace, shader)] = assignations['shaders'][shader]
                    attrs_to_connect.append('%s:%s' % (namespace, shader))
                else:
                    fixed['shaders']['%s' % (shader)] = assignations['shaders'][shader]
                    attrs_to_connect.append('%s' % (shader))
        
        if assignations.has_key('displacement'):
            for disp in assignations['displacement']:
                if namespace != ':':
                    fixed['displacement']['%s:%s' % (namespace, disp)] = assignations['displacement'][disp]
                    attrs_to_connect.append('%s:%s' % (namespace, disp))
                else:
                    fixed['displacement']['%s' % (disp)] = assignations['displacement'][disp]
                    attrs_to_connect.append('%s' % (disp))

        if assignations.has_key('layers'):
            for layer in assignations['layers']:
                if not fixed['layers'].has_key(layer):
                    fixed['layers'][layer] = {'shaders' : {}, 'displacements' : {}}
                
                if assignations['layers'][layer].has_key('shaders'):
                    for shader in assignations['layers'][layer]['shaders']:
                        if namespace != ':':
                            fixed['layers'][layer]['shaders']['%s:%s' % (namespace, shader)] = assignations['layers'][layer]['shaders'][shader]
                            attrs_to_connect.append('%s:%s' % (namespace, shader))
                        else:
                            fixed['layers'][layer]['shaders']['%s' % (shader)] = assignations['layers'][layer]['shaders'][shader]
                            attrs_to_connect.append('%s' % (shader))
                
                if assignations['layers'][layer].has_key('displacements'):
                    for disp in assignations['layers'][layer]['displacements']:
                        if namespace != ':':
                            fixed['layers'][layer]['displacements']['%s:%s' % (namespace, disp)] = assignations['layers'][layer]['displacements'][disp]
                            attrs_to_connect.append('%s:%s' % (namespace, disp))
                        else:
                            fixed['layers'][layer]['displacements']['%s' % (disp)] = assignations['layers'][layer]['displacements'][disp]
                            attrs_to_connect.append('%s' % (disp))                    

        self.setAttr(attr='shadersAssignation', value=json.dumps(fixed['shaders']))
        self.setAttr(attr='displacementsAssignation', value=json.dumps(fixed['displacement']))
        self.setAttr(attr='layersOverride', value=json.dumps(fixed['layers']))

        # connect the shaders to the alembicHolder
        port = 0
        added = []
        for attr in attrs_to_connect:
            if not attr in added:
                if not attr.endswith('.message'):
                    shader_attr = '%s.message' % attr
                else:
                    shader_attr = attr
                shape_attr = '%s.shaders[%i]' % (self.data['shapeNode'], port)
                self.connectAttr(shader_attr, shape_attr)
                added.append(attr)
                port += 1

    def rebuildLookdev(self):
        """
        Import the alembic geometry file, the alembic shaders file and reconnect them using the json file.
        """
        self.logger.info('Reverting Lookdev')
        # TODO

    def importAbc(self, parent_transform=True):
        """
        Import alembic cache as maya geometry

        Args:
            parent_transform (bool): parent the new maya geometry under alembicHolder transform, if None, user is prompted to choose. When executing via batch, ensure 'parent_transform' is True, if not specified.
        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self.logger.info("Import Alembic")

        if self.data['cacheFileNameAttr'] != '':
            if os.path.isfile(self.data['cacheFileNameAttr']):

                # now try the abcImport
                try:
                    if parent_transform:
                        cmds.AbcImport(self.data['cacheFileNameAttr'], reparent=self.data['transformNode'])
                        self.logger.debug("Parenting to %s " % self.data['transformNode'])
                    else:
                        cmds.AbcImport(self.data['cacheFileNameAttr']) 

                    self.logger.info("Imported : %s" % self.data['cacheFileNameAttr'])
                    return True

                except Exception, e:
                    self.logger.error("Import Alembic Error : %s" % e)
                    return False
            else:
                self.logger.error("Missing file : %s" % self.data['cacheFileNameAttr'])
                return False
        else:
            self.logger.info("Empty attribute : %s.cacheFileNames" % self.data['shapeNode'])
            return False

    def writeAbcShaders(self, shader_out_path):
        """
        Export all shaders connected to the alembicHolder. exports both an alembic and maya file
        
        Args:
            shader_out_path (str): Path to export the alembic shaders to

        Returns:
            bool: The return value. True for success, False otherwise.            
        """
        self.logger.info("Export Shaders")

        try:
            if not cmds.pluginInfo('abcMayaShader', loaded=True, query=True):
                cmds.loadPlugin('abcMayaShader')

            # make dirs
            if not os.path.isdir(os.path.dirname(shader_out_path)):
                os.makedirs(os.path.dirname(shader_out_path))

            # export the alembic file
            cmds.abcCacheExport(f=shader_out_path, node=self.data['shapeNode'])
            self.logger.debug("Exporting Alembic Shaders")

            # export the maya file
            shadersSelection = self.getConnectedShaders()
            cmds.select(shadersSelection,r=True,noExpand=True)
            cmds.file(shader_out_path, f=True,options='v=0', type='mayaAscii', pr=True, es=True)
            self.logger.debug("Exporting Maya Shaders")

            # reselect the shape
            cmds.select(self.data['shapeNode'])
            self.logger.info("Exported Shaders : %s" % shader_out_path)
            return True

        except Exception, e:
            self.logger.error("Export Shaders Error : %s" % e)
            return False

    def writeJson(self, json_out_path, namespace="default"):
        """
        Export shader and attributes assignments to json file.

        Args:
            namespace (str): Namespace for the prcedural to look in
            json_out_path (str): Path to export the json assignments to
        
        Returns:
            bool: The return value. True for success, False otherwise.             
        """
        self.logger.info("Export Shader and Attribute Assignments")

        assignations = {}

        try:
            if self.objExists('shadersAssignation'):
                shadersAssignation = self.getAttr('shadersAssignation')
                if shadersAssignation:
                    assignations["shaders"] = json.loads(shadersAssignation)

            if self.objExists('attributes'):
                attributes = self.getAttr('attributes')
                if attributes:
                    assignations["attributes"] = json.loads(attributes)

            if self.objExists('displacementsAssignation'):
                displacementsAssignation = self.getAttr('displacementsAssignation')
                if displacementsAssignation:
                    assignations["displacement"] = json.loads(displacementsAssignation)

            if self.objExists('layersOverride'):
                layersOverride = self.getAttr('layersOverride')
                if layersOverride:
                    assignations["layers"] = json.loads(layersOverride)

            if namespace != 'default':
                assignations["namespace"] = namespace
            else :
                assignations["namespace"] = self.data['shapeNode'].replace(":", "_").replace("|", "_")

            self.logger.debug("Using namespace : %s" % assignations['namespace'])

            # make dirs
            if not os.path.isdir(os.path.dirname(json_out_path)):
                os.makedirs(os.path.dirname(json_out_path))

            with open(json_out_path, 'w') as outfile:
                json.dump(assignations, outfile, separators=(',',':'), sort_keys=True, indent=4)
            outfile.close()
            
            self.logger.info("Exported Assignments : %s" % json_out_path)
            return True

        except Exception, e:
            self.logger.error("Export Assignments Error : %s" % e)
            return False

    def setAttr(self, attr, value, attr_type="string"):
        """
        setAttr method
        
        Args:
            attr (str): Attribute name
            value () - Attribute value
            attr_type (str) - Attribute type
        
        Returns:
            bool: The return value. True for success, False otherwise. 
        """
        try:
            if attr_type:
                cmds.setAttr("%s.%s" % (self.data['shapeNode'], attr), value, type=attr_type)
            else:
                cmds.setAttr("%s.%s" % (self.data['shapeNode'], attr), value)
            self.logger.debug("setAttr : %s.%s > %s"  % (self.data['shapeNode'], attr, value))
        except Exception as e:
            self.logger.error("setAttr : %s" % e)

    def getAttr(self, attr):
        """
        getAttr method
        
        Args:
            attr (str): Attribute name

        Returns:
            str: Attribute value
        """
        try:
            value = cmds.getAttr("%s.%s" % (self.data['shapeNode'], attr))
            self.logger.debug("getAttr : %s.%s = %s" % (self.data['shapeNode'], attr, value))
            return value
        except Exception as e:
            self.logger.error("getAttr : %s", e)
            return False

    def connectAttr(self, attr1, attr2):
        """
        connectAttr method
        
        Args:
            attr1 (str): Attribute name
            attr2 (str): Attribute name

        Returns:
            bool: The return value. True if exists, False otherwise. 
        """
        try:
            cmds.connectAttr(attr1, attr2)
            self.logger.debug("connectAttr : %s > %s" % (attr1, attr2))
            return True
        except Exception as e:
            self.logger.error("connectAttr : %s" % e)

    def objExists(self, attr):
        """
        Check if an attribute exists
        
        Args:
            attr - Attribute to check
        
        Returns:
            bool: The return value. True if exists, False otherwise. 
        """
        try:
            exists = cmds.objExists("%s.%s" % (self.data['shapeNode'], attr))
            self.logger.debug("objExists : %s.%s = %s" % (self.data['shapeNode'], attr, exists))
            return exists
        except Exception as e:
            self.logger.error("objExists : %s" % e)
            return False

    def getConnectedShaders(self):
        """
        Get the shaders / displacements connected the alembicHolder node

        Returns:
            list: The shaders and displacements connected to the alembicHolder node
        """
        self.logger.debug("Connected Shaders")

        connected = []
        for connections in pm.listConnections(self.data['shapeNode'], plugs=True, connections=True):
            if cmds.getClassification(connections[-1].nodeType(), satisfies="shader"):
                self.logger.debug("Connected shader : %s" % connections[-1].node())
                connected.append(connections[-1].node())
        return connected

    def slashesToPipes(self):
        """
        ScriptJob callback on alembicHolder.cacheGeomPath attribute to fix dag path
        """
        self.logger.debug("Convert slashes to pipes")

        if self.getAttr(attr='cacheGeomPath') != "":
            
            # cleanup the attribute value
            value = self.getAttr(attr='cacheGeomPath').lstrip('["').rstrip('"]').replace('/', '|')
            self.setAttr(attr='cacheGeomPath', value=value)

    def validateDictionaries(self):
        """
        Check the values of the attribute editor to ensure they are valid json strings.
        Raise a ValueError if it fails with the offending character.

        Returns:
            bool: The return value. True for success, False otherwise.
        """
        self.logger.info("Validating Dictionaries")

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
            self.logger.info("Valid")
            return True
        else:
            if shaders:
                self.logger.error("%s.shadersAssignation : %s" % (self.data['shapeNode'], shaders))
            if disp:
                self.logger.error("%s.displacementsAssignation : %s" % (self.data['shapeNode'], disp))
            if attr:
                self.logger.error("%s.attributes : %s" % (self.data['shapeNode'], attr))
            if layers:
                self.logger.error("%s.layersOverride : %s" % (self.data['shapeNode'], layers))
            if namespace:
                self.logger.error("%s.shadersNamespace : %s" % (self.data['shapeNode'], namespace))
            self.logger.info("Invalid")
            return False

def getLogger(node):
    """
    Simple logger

    Returns:
        object: Just a simple logger instance
    """
    level = logging.INFO
    if os.environ.has_key('ABCTOA_DEBUG'):
        if os.environ['ABCTOA_DEBUG'] == 'True' or os.environ['ABCTOA_DEBUG'] == '1':
            level = logging.DEBUG

    logger = logging.getLogger('[ abcToA - %s ]' % node)
    while logger.handlers:
        logger.handlers.pop()
    logger.propagate = False     
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main(cls, abcnodes):
    """
    Parse attributes from a given list alembicHolder nodes
    
    Args:
        cls (bool): Return attribute data as an alembicHolderClass instance or as a simple dictionary
        abcnodes (list): List of pymel instances of alembicHolder nodes

    Returns:
        list: List of either dictionaries or classes representing selected alembicHolder nodes
    """
    abclist = []

    for node in abcnodes:
        logger = getLogger(str(node))
        trans = node.getParent()
        data = {}
        
        # maya
        data['transformNode'] = str(trans)
        data['shapeNode'] = str(node)

        # live scene assignments
        data["shadersAssignationAttr"] = pm.getAttr("%s.shadersAssignation" % node)
        data["attributesAttr"] = pm.getAttr("%s.attributes" % node)
        data["displacementsAssignationAttr"] = pm.getAttr("%s.displacementsAssignation" % node)
        data["layersOverrideAttr"] = pm.getAttr("%s.layersOverride" % node)
        data["shadersNamespaceAttr"] = pm.getAttr("%s.shadersNamespace" % node)

        # external files
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

        if not cls:
            abclist.append(data)
        else:
            abclist.append(alembicHolderClass(data, logger))

    return abclist

def getAlembicHolder(cls=False, node_name=""):
    """
    Parse attributes from a given alembicHolder node
    
    Args:
        cls (bool): Return attribute data as an alembicHolderClass instance or as a simple dictionary
        node_name (str): Specified alembicHolder node name

    Returns:
        list: List of either dictionaries or classes representing selected alembicHolder node
    """

    tr = cmds.ls(node_name)
    if len(tr) == 0:
        return []
    shape_list = []
    for x in tr:
        if cmds.nodeType(x) == "alembicHolder":
            shape = x
        else:
            shapes = cmds.listRelatives(x, shapes=True, f=1)
            if not shapes:
                continue
            shape = shapes[0]
            shape_list += pm.ls(shape)
    return main(cls, shape_list)

def getSelectedAlembicHolder(cls=False, filter_string=""):
    """
    Parse attributes from selected alembicHolder nodes
    
    Args:
        cls (bool): Return attribute data as an alembicHolderClass instance or as a simple dictionary
        filter_string (str): Filter selection

    Returns:
        list: List of either dictionaries or classes representing selected alembicHolder nodes
    """
    selected_abc = pm.ls(sl=True, dag=True, leaf=True, visible=True, type='alembicHolder', l=True)

    if filter_string != "":
        filter_string = filter_string.replace('*', '')
        for i in selected_abc:
            if not filter_string in str(i):
                selected_abc.remove(i)

    if selected_abc != []:
        return main(cls, selected_abc)
    else:
        return []

def getSelected(cls=False, filter_string=""):
    """Legacy"""
    return(getSelectedAlembicHolder(cls, filter_string))

def build_path(cask_node, nodes):
    """
    Walk up the given alembic node, finding its parents, till we reach the top
    return a list of parent transforms of the given node
    """
    if cask_node.parent.name != 'ABC':
        nodes.insert(0, cask_node.parent.name)
        build_path(cask_node.parent, nodes)
    return nodes

def get_future_dag_path(transform, parent_under, archive):
    """
    Find the selected transforms matching our name, loop over them
    and construct the future dag path
    """

    importxform = cask.find(archive.top, transform, 'Xform')

    # importxform should only match one
    for foundnode in importxform:
        node_hierarchy = build_path(foundnode, [])
        node_hierarchy.append(foundnode.name)

        return parent_under + '|' + '|'.join( node_hierarchy )

def import_xforms(abcfile, transform_names, parent_under, update):
    """
    Imports and optionally, updates transforms from an alembic file.

    Params:
        abcfile : (str) the filepath of the alembic file
        transform_names : (list) a list of transform names to import / update
        parent_under : (str) the dag path to alembicHolder
        update : (bool) update previously imported transforms
    """
    archive = cask.Archive(abcfile)
    update_data =[]

    for tr in transform_names:

        data = {}
        data['transform'] = tr
        data['dag_path']= get_future_dag_path(tr, parent_under, archive)
        data['exists'] = cmds.objExists(data['dag_path'])

        if not data['exists']:
            update_data.append(data)
        elif data['exists'] and update:
            update_data.append(data)

    if get_previously_imported_transforms(abcfile, parent_under) == []:

        # this doesnt use the -ct and -crt flags, which will cause the import to fail if root nodes are not present
        if update and update_data != []:
            cmd = 'AbcImport -d -rpr "%s" -ft "%s" -eft "Shape" "%s"' % (parent_under, ' '.join( [ i['transform'] for i in update_data ] ), abcfile)

            try:
                mel.eval(cmd)
                MGlobal.displayInfo(cmd)
            except Exception as e:
                message = "Error running import transforms : %s" % e
                MGlobal.displayError(message)
        return

    # conntect type AbcImport
    if update and update_data != []:
        cmd = 'AbcImport -d -rpr "%s" -ft "%s" -ct "%s" -crt -eft "Shape" "%s"' % (parent_under, ' '.join( [ i['transform'] for i in update_data ] ), parent_under, abcfile)

        try:
            mel.eval(cmd)
            MGlobal.displayInfo(cmd)            
        except Exception as e:
            message = "Error running import transforms : %s" % e
            MGlobal.displayError(message)

def get_previously_imported_transforms(abcfile, root):
    """
    Return a list of transform that are present under 'root' that are
    also present in the given alembic file
    """
    archive = cask.Archive(abcfile)

    previous = []
    lowest_transforms = []
    descendents = cmds.listRelatives(root, f=True, allDescendents=True)        

    if descendents:
        for d in descendents:
            children = cmds.listRelatives(d, children=True)

            if not children:
                # the xform doesnt have any children
                last = d.split('|')[-1]
                if last not in lowest_transforms:
                    lowest_transforms.append(last)

            # OR - the xform does have children, but none that are from the alembic
            if children:
                for c in children:
                    if cask.find(archive.top, str(c)) != []:
                        last = c.split('|')[-1]
                        if last not in lowest_transforms:
                            lowest_transforms.append(last)

    for i in lowest_transforms:
        # if the descendent transform is in the alembic archive
        # safe to say its been imported before
        if cask.find(archive.top, str(i)) != []:
            previous.append(i)

    return previous

def update_xforms(abcfile, parent_under):
    """Update previously imported transforms"""
    
    cmd = 'AbcImport -d -rpr "%s" -ct "%s" -eft "Shape" "%s"' % (parent_under, parent_under, abcfile)
    try:
        mel.eval(cmd)
        MGlobal.displayInfo(cmd)
    except Exception as e:
        message = "Error running update transforms : %s" % e
        MGlobal.displayError(message)

def name_to_node(name):
    """Open Maya utility to convert a given node name to MObject"""
    selectionList = MSelectionList()
    selectionList.add(name)
    node = MObject()
    selectionList.getDependNode(0, node)
    return node

def checkTime(shape):
    """Connect alembicHolder to time"""
    if not cmds.isConnected("time1.outTime", "%s.time" % shape):
        message = 'Connecting : time1.outTime to %s.time' % shape
        cmds.connectAttr("time1.outTime", "%s.time" % shape)
        MGlobal.displayInfo(message)

def checkShadersAssignation(shape):
    """Ensure that required shaders are connected to alembicHolder"""
    required = []
    connected = []      

    # find the shaders / displacement that are required
    shadersAssignation = cmds.getAttr("%s.shadersAssignation" % shape)
    if shadersAssignation:
        shadersAssignation = json.loads(shadersAssignation)
        for shader in shadersAssignation.keys():
            if not shader in required:
                required.append(shader)
    
    shape_connections = cmds.listAttr("%s.shaders" % shape, multi=True)

    # go find the connected shaders
    if shape_connections:
        for con in shape_connections:
            connected_shader = cmds.listConnections("%s.%s" % (shape, con))[0]
            connected.append(connected_shader)
    
    port = len(connected)
    for req in required:
        if req not in connected:
            if cmds.objExists(req):
                cmds.connectAttr( req + ".message", shape + ".shaders[%i]" % port)
                port += 1
                message = 'Connected %s to %s' % (req, shape)
                MGlobal.displayInfo(message)
            else:
                message = "Missing shader : %s" % req
                MGlobal.displayWarning(message)

def checkLayersOverride(shape):
    """Ensure that required shaders are connected to alembicHolder"""
    required = []
    connected = []      

    # find the shaders / displacement that are required
    layersOverride = cmds.getAttr("%s.layersOverride" % shape)
    if layersOverride:
        layersOverride = json.loads(layersOverride)
        for layer in layersOverride:
            if layersOverride[layer].has_key('shaders'):
                for k in layersOverride[layer]['shaders'].keys():
                    if not k in required:
                        required.append(k)

    shape_connections = cmds.listAttr("%s.shaders" % shape, multi=True)

    # go find the connected shaders
    if shape_connections:
        for con in shape_connections:
            connected_shader = cmds.listConnections("%s.%s" % (shape, con))[0]
            connected.append(connected_shader)
    
    port = len(connected)
    for req in required:
        if req not in connected:
            if cmds.objExists(req):
                cmds.connectAttr( req + ".message", shape + ".shaders[%i]" % port)
                port += 1
                message = 'Connected %s to %s' % (req, shape)
                MGlobal.displayInfo(message)
            else:
                message = "Missing shader : %s" % req
                MGlobal.displayWarning(message)

def getCurrentSelection():
    """Return the shape of the currently selected alembicHolder"""
    node = cmds.ls(sl=True)
    if node:
        node = node[0]
        if cmds.nodeType(node) == 'alembicHolder':
            shape = node
            return shape
        else:
            relatives = cmds.listRelatives(node, shapes=True, f=1)
            if relatives:
                for i in relatives:
                    if cmds.nodeType(i) == "alembicHolder":
                        shape = i
                        return shape
    return None

def getCurrentTransformSelection():
    """Return the transform of the currently selected alembicHolder"""
    node = cmds.ls(sl=True)
    if node:
        node = node[0]
        if cmds.nodeType(node) == 'transform':
            xform = node
            return xform
        else:
            relatives = cmds.listRelatives(node, shapes=True, f=1)
            if relatives:
                for i in relatives:
                    if cmds.nodeType(i) == "transform":
                        xform = i
                        return xform
    return None                   