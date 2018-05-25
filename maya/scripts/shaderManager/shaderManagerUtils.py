from PySide2 import QtWidgets, QtGui, QtCore
import maya.cmds as cmds
import maya.mel as mel
import cask

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
            cmd = 'AbcImport "%s" -d -rpr "%s" -ft "%s" -eft "Shape"' % (abcfile, parent_under, ' '.join( [ i['transform'] for i in update_data ] ))

            try:
                print '\n%s\n' % cmd
                mel.eval(cmd)
            except Exception as e:
                print "Error running update transforms : %s" % e
        return

    # conntect type AbcImport
    if update and update_data != []:
        cmd = 'AbcImport "%s" -d -rpr "%s" -ft "%s" -ct "%s" -crt -eft "Shape"' % (abcfile, parent_under, ' '.join( [ i['transform'] for i in update_data ] ), parent_under)

        try:
            print '\n%s\n' % cmd
            mel.eval(cmd)
        except Exception as e:
            print "Error running update transforms : %s" % e

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
            # print 'Descendent : %s' % d
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

    print 'Previously Imported : %s' % previous
    return previous

def get_xform_shape():
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
            return shape

def prompt_import_xforms():
    """"""

    result = cmds.promptDialog(
            title='Import Xforms',
            message='Enter comma separated transform names:',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel')

    if result == 'OK':
        text = cmds.promptDialog(query=True, text=True)
        
        transform_names = text.replace(' ', '').split(',')
        update = True
        parent_under = cmds.ls(sl=True)[0]
        abcfile = str(cmds.getAttr('%s.cacheFileNames[0]' % get_xform_shape()))
        import_xforms(abcfile, transform_names, parent_under, update)

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
