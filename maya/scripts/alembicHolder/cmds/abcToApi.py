import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import cask
import json, ast, os, pprint
from arnold import *

class abcClass():
    def __init__(self, data):
        self.data = data

    def exportAbc(self):
        pass

    def exportJson(self):
        pass

    def exportShaders(self):
        pass

    def importAbc(self, parent_transform=None):

        if parent_transform == None:
            res = cmds.confirmDialog( title='Transform', message='Do you want to parent the incoming geo to the alembicHolder transform?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            if res == 'Yes':
                parent_transform = True
            else:
                parent_transform = False

        if self.data['cacheFileNameAttr'] != '':

            if parent_transform:
                transform = self.data['transformNode']
                cmds.AbcImport(self.data['cacheFileNameAttr'], reparent=transform)
            else:
                cmds.AbcImport(self.data['cacheFileNameAttr'])

            msg = 'IMPORTED ABC : %s' % self.data['cacheFileNameAttr']
        
        else:
            msg = 'NO ABC FILE : %s' % self.data['cacheFileNameAttr']

        print msg

    def importJson(self, merge=None):        
        current = {}

        if cmds.getAttr("%s.shadersAssignation" %(self.data['shapeNode'])):
            current['shaders'] = ast.literal_eval(cmds.getAttr("%s.shadersAssignation" %(self.data['shapeNode'])))
        if cmds.getAttr("%s.attributes" %(self.data['shapeNode'])):
            current['attributes'] = ast.literal_eval(cmds.getAttr("%s.attributes" %(self.data['shapeNode'])))
        if cmds.getAttr("%s.displacementsAssignation" %(self.data['shapeNode'])):
            current['displacement'] = ast.literal_eval(cmds.getAttr("%s.displacementsAssignation" %(self.data['shapeNode'])))
        if cmds.getAttr("%s.layersOverride" %(self.data['shapeNode'])):
            current['layers'] = ast.literal_eval(cmds.getAttr("%s.layersOverride" %(self.data['shapeNode'])))
        if cmds.getAttr("%s.shadersNamespace" %(self.data['shapeNode'])):
            current['namespace'] = ast.literal_eval(cmds.getAttr("%s.shadersNamespace" %(self.data['shapeNode'])))

        # if current != {} and not merge and self.data['jsonFileAttr'] != '':
        #     res = cmds.confirmDialog( title='Confirm Merge', message='Attributes already exist for this node.\n\nDo you want to merge the current attributes into the incoming json file?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        #     if res == 'Yes':
        #         merge = True
        #     else:
        #         merge= False

        if self.data['jsonFileAttr']:
            with open(self.data['jsonFileAttr']) as json_file:
                json_data = json.load(json_file)

            if merge:
                json_data = mergeJson(json_data, current)

            if json_data.has_key('shaders'):
                cmds.setAttr("%s.shadersAssignation" %(self.data['shapeNode']), json.dumps(json_data['shaders']), type="string")
            if json_data.has_key('attributes'):
                cmds.setAttr("%s.attributes" %(self.data['shapeNode']), json.dumps(json_data['attributes']), type="string")
            if json_data.has_key('displacement'):
                cmds.setAttr("%s.displacementsAssignation" %(self.data['shapeNode']), json.dumps(json_data['displacement']), type="string")
            if json_data.has_key('layers'):
                cmds.setAttr("%s.layersOverride" %(self.data['shapeNode']), json.dumps(json_data['layers']), type="string")
            if json_data.has_key('namespace'):
                cmds.setAttr("%s.shadersNamespace" %(self.data['shapeNode']), json.dumps(json_data['namespace']), type="string")

            cmds.setAttr("%s.forceReload" %(self.data['shapeNode']), 1)
            cmds.setAttr("%s.jsonFile" %(self.data['shapeNode']), "", type="string")

            msg = 'IMPORTED JSON : %s' % self.data['jsonFileAttr']

        else:
            msg = 'NO JSON FILE : %s' % self.data['jsonFileAttr']

        print msg

    def importShaders(self, namespace=None):

        if self.data['abcShadersAttr'] != '':
            abcfile = self.data['abcShadersAttr']
            mayafile = abcfile.replace('.abc', '.ma')

            if os.path.isfile(mayafile):
                if not namespace:
                    namespace = mayafile.split(os.path.sep)[-1].split('.')[0]

                imported_shaders = cmds.file(mayafile, i=True, rnn=True, mergeNamespacesOnClash=False, namespace=namespace)
                cmds.setAttr("%s.abcShaders" %(self.data['shapeNode']), "", type="string")
                cmds.select(self.data['shapeNode'])
                msg = 'IMPORTED SHADERS : %s' % mayafile
            else:
                msg = 'MISSING SHADERS : %s' % mayafile
        else:
            msg = 'NO SHADERS FILE : %s' % self.data['abcShadersAttr']
        print msg

    def setAttr(self, attr, value, attr_type="string"):
        try:
            cmds.setAttr("%s.%s" % (self.data['shapeNode'], attr), value, type=attr_type)
        except Exception as e:
            print 'ERROR : %s' % e

    def getAttr(self, attr):
        try:
            return cmds.getAttr("%s.%s" % (self.data['shapeNode'], attr))
        except Exception as e:
            print 'ERROR : %s' % e

    def checkConnections(self):
        self.connected_dict = {}

        # GET SHADERS AND DISP REFERENCED IN ATTRS - NOT IN JSON FILE
        self.requiredShaders = []

        if self.data['assignedShaders'] != []:
            for i in self.data['assignedShaders']:
                self.requiredShaders.append(i)

        if self.data['displacementsAssignation'] != None:
            for i in self.data['displacementsAssignation']:
                self.requiredShaders.append(i)

        # GET CURRENT CONNECTIONS
        connections = pm.listConnections(str(self.data['shapeNode']))
        self.connections = []
        for i in connections:
            self.connections.append(str(i))

        # ARE ALL THE SHADERS/DISP CONNECTED? 
        for req in self.requiredShaders:
            if req not in self.connections:
                self.connected_dict[req] = False
            else:
                self.connected_dict[req] = True

        # PRINTOUT
        print 'SCENE BASED ASSIGNMENTS'
        for conn in self.connected_dict:
            if self.connected_dict[conn]:
                print 'CONNECTED   : %s > %s' % (self.data['shapeNode'], conn)
            else:
                print 'UNCONNECTED : %s > %s' % (self.data['shapeNode'], conn)

        ####################################################################################################
        # GET SHADERS AND DISP REFERENCED IN JSON FILE
        self.externalShaders = []
        self.externalDict = {}

        if self.data['abcShaderList'] != None:
            for i in self.data['abcShaderList']:
                self.externalShaders.append(i)

        # if self.data['displacementsAssignation'] != []:
        #     for i in self.data['displacementsAssignation']:
        #         self.externalShaders.append(i)

        # GET EXTERNAL ASSIGNMENTS
        # jsonFileShaders

        # connections = pm.listConnections(str(self.data['shapeNode']))
        # self.connections = []
        # for i in connections:
        #     self.connections.append(str(i))


        print self.externalShaders
        # ARE ALL THE SHADERS/DISP CONNECTED? 
        for req in self.externalShaders:
            if req not in self.data['jsonFileShaders']:
                self.externalDict[req] = False
            else:
                self.externalDict[req] = True

        # PRINTOUT
        print '\n\nEXTERNAL ASSIGNMENTS'
        for conn in self.externalDict:
            if self.externalDict[conn]:
                print 'CONNECTED   : %s > %s' % (self.data['shapeNode'], conn)
            else:
                print 'UNCONNECTED : %s > %s' % (self.data['shapeNode'], conn)


    def makeConnections(self):

        port = 0
        added = []

        ports_in_use = []
        shaders = pm.listConnections(self.data['shapeNode'], plugs=True, connections=True, type='shadingEngine')
        disps = pm.listConnections(self.data['shapeNode'], plugs=True, connections=True, type='displacementShader')

        c = shaders + disps

        for each in c:
            shp = str(each[0])
            shp_port = shp.split('[')[-1].split(']')[0]
            ports_in_use.append(int(shp_port))

        ports_in_use = sorted(ports_in_use)

        if ports_in_use != []:
            port = ports_in_use[-1]
            port = port + 1


        for shader in self.requiredShaders:
            # print shader
            if not shader in added:
                if cmds.objExists(shader):

                    already_connected = False
                    for each in c:
                        if shader == str(each[-1].split('.')[0]):
                            if self.data['shapeNode'] == str(each[0].split('.')[0]):
                                already_connected = True

                    if not already_connected:
                        print 'CONNECTING : %s > %s' % (self.data['shapeNode'], shader)
                        cmds.connectAttr("%s.message" % shader, "%s.shaders[%i]" % (self.data['shapeNode'], port))
                        added.append(shader)
                        port = port + 1
                    else:
                        print 'SCENE CONNECTED : %s > %s' % (self.data['shapeNode'], shader)
                
                elif shader in self.data['abcShaderList']:
                    print 'JSON CONNECTED : %s > %s' % (self.data['shapeNode'], shader)
                else:
                    print 'UNCONNECTED : %s > %s' % (self.data['shapeNode'], shader)


        for disp in self.requiredDisplacements:
            if not disp in added:
                if cmds.objExists(disp):

                    already_connected = False
                    for each in c:
                        if disp == str(each[-1].split('.')[0]):
                            if self.data['shapeNode'] == str(each[0].split('.')[0]):
                                already_connected = True

                    if not already_connected:
                        print 'CONNECTING : %s > %s' % (self.data['shapeNode'], disp)
                        cmds.connectAttr("%s.message" % disp, "%s.shaders[%i]" % (self.data['shapeNode'], port))
                        added.append(disp)
                        port = port + 1
                    else:
                        print 'SCENE CONNECTED : %s > %s' % (self.data['shapeNode'], disp)
                elif disp in self.data['abcShaderList']:
                    print 'JSON CONNECTED : %s > %s' % (self.data['shapeNode'], disp)
                else:
                    print 'UNCONNECTED : %s > %s' % (self.data['shapeNode'], disp)

    def breakConnections(self):
        for connections in pm.listConnections(self.data['shapeNode'], plugs=True, connections=True):
            if connections[-1].nodeType() in ['shadingEngine', 'displacementShader']:
                pm.disconnectAttr(str(connections[-1]), str(connections[0]))
                print 'BREAK :  %s > %s' % (str(connections[-1]), str(connections[0]))

    def runProcedural(self):
        print 'SIMULATE RENDER'

        start = str(1)
        end = str(1)
        dest = "/tmp/tmp.ass"
        command = 'arnoldExportAss -f "%s" -lightLinks 1 -shadowLinks 1 -sf %s -ef %s -fs 1 -ep' % (dest, start, end)

        mel.eval(command)
 
        # ass = "/shows/tlk2/user/elliott-s/maya/data/test.ass"
        ass = dest
        AiBegin()
        AiASSLoad(ass, AI_NODE_ALL)

        # list to hold cameras, filters, and drivers.
        l = []
         
        # this will let you iterate over all camera, driver, and filter nodes in the Arnold universe
        nodeIter = AiUniverseGetNodeIterator(AI_NODE_SHAPE)

        while not AiNodeIteratorFinished(nodeIter):
            node = AiNodeIteratorGetNext(nodeIter)
            # deletion_list.append(node)
            ne = AiNodeGetNodeEntry( node )
            name = AiNodeGetName(node)
            l.append(name)
              
            if not name.endswith(':src'):
                if not name == '':
                    if not name == 'root':
                        get_name = AiNodeGetStr(node, 'name')
                        get_node = AiNodeGetArray(node, 'node')
                        subt = AiNodeGetInt(node, 'subdiv_type')
                        subi = AiNodeGetInt(node, 'subdiv_iterations')
                        subae = AiNodeGetInt(node, 'subdiv_adaptive_error')
                        smoothing = AiNodeGetInt(node, 'smoothing')
                        vis = AiNodeGetInt(node, 'visibility')
                        shader = AiNodeGetArray(node, "shader")
                        # p = AiNodeGetParams(node)


                        jsonFile = AiNodeGetStr(node, 'jsonFile')
                        abcShaders = AiNodeGetStr(node, 'abcShaders')
                        
                        displacementsAssignation = AiNodeGetStr(node, 'displacementsAssignation')
                        shadersAssignation = AiNodeGetStr(node, 'shadersAssignation')
                        shadersNamespace = AiNodeGetStr(node, 'shadersNamespace')
                        attributes = AiNodeGetStr(node, 'attributes')
                        
                        print '*'*100
                        print 'NAME       : ', get_name
                        print 'NODE       : ', node
                        print 'VISI       : ', vis
                        print 'SUBT       : ', subt
                        print 'SUBI       : ', subi
                        print 'SUBAE      : ', subae
                        print 'SMOOTH     : ', smoothing
                        
                        print ''
                        print 'SHADER     : ', shader
                        print ''
                        print 'FILE INFO'
                        print '\tABC SHADER : ', abcShaders
                        print '\tJSON       : ', jsonFile
                        print ''
                        print 'SCENE INFO'
                        print '\tSHADER ASS : ', shadersAssignation
                        print '\tDISP ASS   : ', displacementsAssignation
                        print '\tSHADER NM  : ', shadersNamespace
                        print '\tATTRS      : ', attributes
                        # print p

                        #print shader
                        #print shader.contents
                        #print '*'*100



                        # paramIter = AiNodeEntryGetParamIterator(ne)


        AiNodeIteratorDestroy(nodeIter)

    def swap_slashes_for_pipes(self):
        if cmds.getAttr("%s.cacheGeomPath" % self.data['shapeNode']) != "":
            var = cmds.getAttr("%s.cacheGeomPath" % self.data['shapeNode'])
            var = var.lstrip('["')
            var = var.rstrip('"]')
            var = var.replace('/', '|')

            cmds.setAttr("%s.cacheGeomPath" % self.data['shapeNode'], var, type="string")

    def validateDictionaries(self):
        '''
        reads in the values of the attribute editor and attempts to read them as json dicts
        if it fails, raise an error to indicate why the string isnt a valid dictoinary

        '''
        message = ''
        shader_dict = {}
        disp_dict = {}
        attr_dict = {}
        layers_dict = {}
        namespace_str = ''

        shader_attr = cmds.getAttr("%s.shadersAssignation" % self.data['shapeNode'])
        disp_attr = cmds.getAttr("%s.displacementsAssignation" % self.data['shapeNode'])
        attr_attr = cmds.getAttr("%s.attributes" % self.data['shapeNode'])
        layers_attr = cmds.getAttr("%s.layersOverride" % self.data['shapeNode'])
        namespace_attr = cmds.getAttr("%s.shadersNamespace" % self.data['shapeNode'])

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
                # elif type(namespace_attr) == str:
                #     if 
            except ValueError as e:
                namespace = e
                fail = True

        if not fail:
            print 'VALID   : %s' % self.data['shapeNode']
        else:
            if shaders:
                print "INVALID : %s.shadersAssignation : %s" % (self.data['shapeNode'], shaders)

            if disp:
                print "INVALID : %s.displacementsAssignation : %s" % (self.data['shapeNode'], disp)

            if attr:
                print "INVALID : %s.attributes : %s" % (self.data['shapeNode'], attr)

            if layers:
                print "INVALID : %s.layersOverride : %s" % (self.data['shapeNode'], layers)

            if namespace:
                print "INVALID : %s.shadersNamespace : %s" % (self.data['shapeNode'], namespace)
    
    def writeAbcShaders(self, merge=False, shader_out_path=""):
        print '***** writeAbcShaders *****'
        ''' export all shaders connected to a holder in abc '''
        shape = self.data['shapeNode']
        try:
            # export the abc file
            cmds.abcCacheExport(f=shader_out_path, node=shape)

            # export the maya file
            shadersSelection = cmds.ls(type='shadingEngine')
            cmds.select(shadersSelection,r=True,noExpand=True)
            cmds.file(shader_out_path, f=True,options='v=0',type='mayaAscii' ,pr=True,es=True)

            msg = 'Shaders Export : Success\n%s\n' % shader_out_path

            cmds.select(shape)

            # merging is disabled for now

            if merge and cmds.getAttr("%s.abcShaders" % shape) != '':
                i = str(cmds.getAttr("%s.abcShaders" % shape))
                shader_out_path = str(shader_out_path)

                a = cask.Archive(i)
                b = cask.Archive(shader_out_path)

                a_keys = a.top.children['materials'].children.keys()
                b_keys = b.top.children['materials'].children.keys()

                for i in b.top.children['materials'].children:
                    if i in a_keys:
                        pass
                    else:
                        a.top.children['materials'].children[i] = b.top.children['materials'].children[i]

                shader_out_path = shader_out_path + '.merged'
                # print 'now write out'
                a.write_to_file(shader_out_path)


            return msg

        except Exception, e:
            msg = 'Shaders Export : Fail\n%s\n' % e
            return msg

    def writeJson(self, namespace=None, merge=False, json_out_path=""):
        print '***** writeJson *****'

        '''Write a json file next to the selected alembicHolders cache containing the current assignations.

        Keyword arguments:
        namespace -- When looking for shaders in the procedural, look/use this namespace.
        '''

        shape = self.data['shapeNode']

        if cmds.nodeType(shape) == "gpuCache" or cmds.nodeType(shape) == "alembicHolder":

            caches = cmds.getAttr("%s.cacheFileNames[0]" % shape)
            print caches

            assignations = {}

            if cmds.objExists("%s.shadersAssignation" % shape):
                try:
                    cur = cmds.getAttr("%s.shadersAssignation"  % shape)
                    assignations["shaders"] = json.loads(cur)
                except:
                    pass

            if cmds.objExists("%s.attributes" % shape):
                try:
                    cur = cmds.getAttr("%s.attributes"  % shape)
                    assignations["attributes"] = json.loads(cur)
                except:
                    pass

            if cmds.objExists("%s.displacementsAssignation" % shape):
                try:
                    cur = cmds.getAttr("%s.displacementsAssignation"  % shape)
                    assignations["displacement"] = json.loads(cur)
                except:
                    pass

            if cmds.objExists("%s.layersOverride" % shape):
                try:
                    cur = cmds.getAttr("%s.layersOverride"  % shape)
                    assignations["layers"] = json.loads(cur)
                except:
                    pass

            if namespace:
                assignations["namespace"] = namespace
            else :
                assignations["namespace"] = shape.replace(":", "_").replace("|", "_")

            try:
                if merge and cmds.getAttr("%s.jsonFile" % shape) != '':
                    with open(cmds.getAttr("%s.jsonFile" % shape)) as json_file:
                        json_data = json.load(json_file)

                    merged = mergeJson(json_data, assignations)

                    with open(json_out_path, 'w') as outfile:
                        json.dump(merged, outfile, separators=(',',':'), sort_keys=True, indent=4)                    

                    if os.path.isfile(json_out_path):
                        msg ='Json Export : Success\n%s\n' % json_out_path
                        return msg

                    else:
                        msg = 'Json Export : Fail\n%s\n' % json_out_path
                        return msg

                else:
                    with open(json_out_path, 'w') as outfile:
                        json.dump(assignations, outfile, separators=(',',':'), sort_keys=True, indent=4)
                
                    if os.path.isfile(json_out_path):
                        msg ='Json Export : Success\n%s\n' % json_out_path
                        return msg

                    else:
                        msg = 'Json Export : Fail\n%s\n' % json_out_path
                        return msg

            except Exception, e:
                msg = 'Json Export : Fail\n%s\n' % e
                return msg
    
def getSelected(cls=False, filter_string=""):

    selected = pm.ls(sl=True, visible=True, l=True)
    selected_abc = pm.ls(sl=True, dag=True, leaf=True, visible=True, type='alembicHolder', l=True)

    # cmds.ls( type= 'transform', sl=1) + cmds.ls(type= 'alembicHolder', sl=1)


    if filter_string != "":
        filter_string = filter_string.replace('*', '')
        temp = []
        for i in selected_abc:
            if filter_string in str(i):
                temp.append(i)
        selected_abc = temp
    
    abcnodes = []
    non_abcnodes = []

    # print 'SELECTED : %s' % selected
    # print 'SELECTED ABC : %s' % selected_abc

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
        # data["secondaryAttributesAttr"] = pm.getAttr("%s.secondaryAttributes" % node)

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

        # print '*'*100
        # import pprint
        # pprint.pprint(data)
        # print '*'*100

        # non attributes

        # read the scene shaders
        data['sceneShaders'] = cmds.ls( mat=True )

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
    
    # print 'NON ABC NODES : %s' % [str(i) for i in non_abcnodes]
    
    if not cls:
        return abclist
    else:
        cls_list = []
        for i in abclist:
            cls_list.append(abcClass(i))
        return cls_list


        
def mergeJson(base, override):
    ''' merge two json files '''
    # print '%s\nmergeJson' % ('*'*100)
    merged = base.copy()

    # print '*'*100
    # print override.keys()
    # print '*'*100

    for top_level_key in override.keys():
        # print ''
        # print 'override key : %s' % top_level_key
        # print 'override value : %s' % override[top_level_key]

        # iterate over the override keys and see if the base contains it
        if merged.has_key(top_level_key):
            # print 'base key : %s' % top_level_key
            # print 'base value : %s' % merged[top_level_key]
            # print ''
            # base contains the key, more logic required

            if top_level_key == 'attributes':
                # print '\nMERGING ATTRIBUTES KEY'
                #############################################################################################
                '''
                contains nested dicts

                base = {
                            'geo1' : {'attr1' : 0, 'attr2' : 1},
                            'geo2' : {'attr1' : 1, 'attr2' : 2}
                            }


                over = {
                            'geo1' : {'attr1' : 1, 'attr2' : 'catmull'},
                            'geo2' : {'attr1' : 1, 'attr2' : 2}
                            }
                 '''

                for geo in override[top_level_key].keys():
                    if geo in merged[top_level_key].keys():
                        for attr in override[top_level_key][geo].keys():
                            merged[top_level_key][geo][attr] = override[top_level_key][geo][attr]

                    else:
                        merged[top_level_key][geo] = override[top_level_key][geo]

            elif top_level_key == 'namespace':
                # print '\nMERGING NAMESPACE KEY'
                #############################################################################################
                '''
                contains just a string

                example = 'AlembicHolder1Shape'

                '''

                if not override[top_level_key] == merged[top_level_key]:
                    # if the override value differs from the base, override it
                    merged[top_level_key] = override[top_level_key]

            elif top_level_key == 'displacement':
                # print '\nMERGING DISPLACEMENT KEY'
                #############################################################################################
                '''
                contains a dictionary of disp shaders, list of geo values assigned to disp shader

                geo cannot be in more than one disp shader list

                base = {
                            'disp_shader1' : ['geo1', 'geo2'],
                            'disp_shader2' : ['geo3', 'geo4']
                            }

                over = {
                            'disp_shader1' : ['geo3', 'geo2'],
                            'disp_shader3' : ['geo1', 'geo5']
                            }

                merged = {
                            'disp_shader1' : ['geo2', 'geo3'],
                            'disp_shader2' : ['geo4'],
                            'disp_shader3' : ['geo1', 'geo5']
                            }

                '''

                for disp_shader in override[top_level_key].keys():
                    # iterate over disp shaders, if the override disp shader isnt in merged, add it

                    geos = override[top_level_key][disp_shader]
                    for geo in geos:
                        # check that the geo isnt in another disp shader list
                        for disp in merged[top_level_key].keys():
                            if geo in merged[top_level_key][disp]:
                                merged[top_level_key][disp].remove(geo) 

                    merged[top_level_key][disp_shader] = override[top_level_key][disp_shader]

            elif top_level_key == 'shaders':
                # print '\nMERGING SHADERS KEY'
                #############################################################################################
                '''
                contains a dictionary of shaders, list of geo values assigned to shader
                
                example = {
                            'shader1' : ['geo1', 'geo2']
                            'shader2' : ['geo3', 'geo4']
                            }

                '''

                for shader in override[top_level_key].keys():
                    # iterate over shaders, if the override shader isnt in merged, add it

                    geos = override[top_level_key][shader]
                    for geo in geos:
                        # check that the geo isnt in another shader list
                        for shad in merged[top_level_key].keys():
                            if geo in merged[top_level_key][shad]:
                                merged[top_level_key][shad].remove(geo) 

                    merged[top_level_key][shader] = override[top_level_key][shader]

            elif top_level_key == 'layers':
                # print '\nMERGING LAYERS KEY'
                #############################################################################################
                '''
                contains a dictionary of layers / shaders, list of geo values assigned to shader
                
                example = {'layer1' :{'properties' : {'/geo1' : {'subdiv_type' : 2, 'subdiv_iterations' : 5}}},
                                     {'shaders'    : {'shader1' : ['geo1', 'geo2']}},
                }

                '''

                for layer in override[top_level_key].keys():
                    # print 'layer : %s' % layer
                    # if the layer isnt already in the base dict, add it

                    if not merged[top_level_key].has_key(layer):
                        merged[top_level_key][layer] = override[top_level_key][layer]

                    else:
                        # the base dict has the layer key already - lets look at each of the keys - shaders, properties etc
                        for layer_key in override[top_level_key][layer]:
                            # print 'layer : %s, key : %s' % (layer, layer_key)
                            if layer_key in merged[top_level_key][layer]:
                                # print 'base has layer key already : %s' % layer_key
                                
                                if layer_key == 'shaders':
                                    for shader in override[top_level_key][layer][layer_key].keys():
                                        geos = override[top_level_key][layer][layer_key][shader]
                                        for geo in geos:
                                            # check that the geo isnt in another shader list
                                            for shad in merged[top_level_key][layer][layer_key].keys():
                                                if geo in merged[top_level_key][layer][layer_key][shad]:
                                                    merged[top_level_key][layer][layer_key][shad].remove(geo)
                                                    if merged[top_level_key][layer][layer_key][shad] == []:
                                                        merged[top_level_key][layer][layer_key].pop(shad, None)  

                                        merged[top_level_key][layer][layer_key][shader] = override[top_level_key][layer][layer_key][shader]


                                
                                elif layer_key == 'displacements':
                                    # print 'displacements'
                                    for shader in override[top_level_key][layer][layer_key].keys():
                                        geos = override[top_level_key][layer][layer_key][shader]
                                        for geo in geos:
                                            # check that the geo isnt in another shader list
                                            for shad in merged[top_level_key][layer][layer_key].keys():
                                                if geo in merged[top_level_key][layer][layer_key][shad]:
                                                    merged[top_level_key][layer][layer_key][shad].remove(geo)
                                                    if merged[top_level_key][layer][layer_key][shad] == []:
                                                        merged[top_level_key][layer][layer_key].pop(shad, None)  

                                        merged[top_level_key][layer][layer_key][shader] = override[top_level_key][layer][layer_key][shader]

                                
                                elif layer_key == 'properties':
                                    # print 'properties'

                                    for geo in override[top_level_key].keys():
                                        if geo in merged[top_level_key].keys():
                                            for attr in override[top_level_key][geo].keys():
                                                merged[top_level_key][geo][attr] = override[top_level_key][geo][attr]

                                        else:
                                            merged[top_level_key][geo] = override[top_level_key][geo]

                            else:
                                # print 'base doesnt have this layer yet - lets just add it'
                                merged[top_level_key][layer][layer_key] = override[top_level_key][layer][layer_key]

        else:
            # base doesnt contain the key already, lets add it and the values
            merged[top_level_key] = override[top_level_key]

    return merged

        