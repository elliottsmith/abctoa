import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

import maya.cmds as cmds
import maya.mel as mel

import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

import numpy
import os, json
from alembicHolder.cmds import abcToApi

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

class AlembicExport(QtWidgets.QWidget):    
    def __init__(self, win, output_name=None, output_directory=None):        
        super(AlembicExport, self).__init__(win)
        
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose) 
        
        #Parent widget under Maya main window        
        self.setParent(win)        
        self.setWindowFlags(QtCore.Qt.Window)   
        
        self.setObjectName('AlembicExport')
        self.setWindowTitle('Alembic Export')        
        self.setGeometry(50, 50, 350, 350)
        
        self.main_layout = QtWidgets.QVBoxLayout()
           
        self.initUI()
        self.setLayout(self.main_layout)

        self.setDefaults()
        self.setConnections()

    def initUI(self):
        # FONTS
        self.bold_font = QtGui.QFont()
        self.bold_font.setBold(True)

        # SELECTION WIDGETS
        self.selection_radios_layout = QtWidgets.QHBoxLayout()
        self.selection_layout = QtWidgets.QVBoxLayout()
        self.selection_label = QtWidgets.QLabel('Selection: ')
        self.selection_label.setFont(self.bold_font)
        self.selected_radio = QtWidgets.QRadioButton('Selected')
        self.all_radio = QtWidgets.QRadioButton('All')
        self.selection_group = QtWidgets.QGroupBox()

        self.selection_layout.addWidget(self.selection_label)
        self.selection_radios_layout.addWidget(self.selected_radio)
        self.selection_radios_layout.addWidget(self.all_radio)
        self.selection_layout.addLayout(self.selection_radios_layout)

        self.selection_group.setLayout(self.selection_layout)

        # TIME WIDGETS
        self.time_range_layout = QtWidgets.QVBoxLayout()
        self.time_start_end_layout = QtWidgets.QHBoxLayout()
        self.time_range_label = QtWidgets.QLabel('Cache time range: ')
        self.time_range_label.setFont(self.bold_font)
        
        self.time_render_settings = QtWidgets.QRadioButton('Render settings')
        self.time_slider = QtWidgets.QRadioButton('Time Slider')
        self.time_start_end = QtWidgets.QRadioButton('Start/End')
        self.time_group = QtWidgets.QGroupBox()

        self.time_start = QtWidgets.QLineEdit('1001.0000')
        self.time_end = QtWidgets.QLineEdit('1100.0000')

        self.time_group.setLayout(self.time_range_layout)

        # TIME LAYOUT
        self.time_range_layout.addWidget(self.time_range_label)
        self.time_range_layout.addWidget(self.time_render_settings)
        self.time_range_layout.addWidget(self.time_slider)
        self.time_range_layout.addWidget(self.time_start_end)

        self.time_start_end_layout.addWidget(self.time_start)
        self.time_start_end_layout.addWidget(self.time_end)

        self.time_range_layout.addLayout(self.time_start_end_layout)

        # FRAME RELATIVE WIDGETS
        self.frame_relative_layout = QtWidgets.QVBoxLayout()
        self.frame_relative_low_high_layout = QtWidgets.QHBoxLayout()
        
        self.frame_relative_label = QtWidgets.QLabel('Frame relative sample: ')
        self.frame_relative_label.setFont(self.bold_font)
        self.frame_relative_checkbox = QtWidgets.QCheckBox('')

        self.frame_relative_keys = QtWidgets.QLineEdit('5')
        self.frame_relative_keys.setMaximumWidth(20)
        self.frame_relative_low = QtWidgets.QLineEdit('-0.48')
        self.frame_relative_high = QtWidgets.QLineEdit('0.48')

        # FRAME RELATIVE LAYOUT
        self.frame_relative_layout.addWidget(self.frame_relative_label)
        self.frame_relative_layout.addWidget(self.frame_relative_checkbox)

        self.frame_relative_low_high_layout.addWidget(self.frame_relative_low)
        self.frame_relative_low_high_layout.addWidget(self.frame_relative_keys)
        self.frame_relative_low_high_layout.addWidget(self.frame_relative_high)

        self.frame_relative_layout.addLayout(self.frame_relative_low_high_layout)

        self.frame_relative_group = QtWidgets.QGroupBox()
        self.frame_relative_group.setLayout(self.frame_relative_layout)

        # # FILE FORMAT WIDGETS
        # self.file_format_label = QtGui.QLabel('File format: ')
        # self.file_format_label.setFont(self.bold_font)
        # self.file_format_hdf5 = QtGui.QRadioButton('HDF5')
        # self.file_format_ogawa = QtGui.QRadioButton('Ogawa')

        # self.file_format_layout = QtGui.QVBoxLayout()
        # self.file_format_radios_layout = QtGui.QVBoxLayout()

        # # FILE FORMAT LAYOUT
        # self.file_format_radios_layout.addWidget(self.file_format_hdf5)
        # self.file_format_radios_layout.addWidget(self.file_format_ogawa)

        # self.file_format_layout.addWidget(self.file_format_label)
        # self.file_format_layout.addLayout(self.file_format_radios_layout)

        # OPTIONS
        self.options_layout = QtWidgets.QVBoxLayout()
        self.options_label = QtWidgets.QLabel('Advanced options: ')
        self.options_label.setFont(self.bold_font)
        
        self.options_write_visibility = QtWidgets.QCheckBox('Write Visibility')
        self.options_write_uvs = QtWidgets.QCheckBox('Write Uvs')
        self.options_world_space = QtWidgets.QCheckBox('World Space')
        self.options_verbosity = QtWidgets.QCheckBox('Verbosity')
        self.options_euler = QtWidgets.QCheckBox('Euler Filter')

        self.options_layout.addWidget(self.options_label)
        self.options_layout.addWidget(self.options_write_visibility)
        self.options_layout.addWidget(self.options_write_uvs)
        self.options_layout.addWidget(self.options_world_space)
        self.options_layout.addWidget(self.options_verbosity)
        self.options_layout.addWidget(self.options_euler)

        self.options_group = QtWidgets.QGroupBox()
        self.options_group.setLayout(self.options_layout) 


        # EXPORT
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.export_btn = QtWidgets.QPushButton('Export')
        self.close_btn = QtWidgets.QPushButton('Close')
        self.bottom_layout.addWidget(self.export_btn)
        self.bottom_layout.addWidget(self.close_btn)

        # MAIN LAYOUT
        self.main_layout.addWidget(self.selection_group)
        self.main_layout.addWidget(self.time_group)
        self.main_layout.addWidget(self.frame_relative_group)
        self.main_layout.addWidget(self.options_group)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_layout)

    def setDefaults(self):
        self.time_slider.setChecked(True)
        self.time_start.setEnabled(False)
        self.time_end.setEnabled(False)
        self.frame_relative_low.setEnabled(False)
        self.frame_relative_high.setEnabled(False)
        self.frame_relative_keys.setEnabled(False)
        self.selected_radio.setChecked(True)
        self.options_write_visibility.setChecked(True)
        self.options_write_uvs.setChecked(True)
        self.options_world_space.setChecked(True)
        self.options_verbosity.setChecked(True)
        self.options_euler.setChecked(False)

    def setConnections(self):
        self.time_start_end.clicked.connect(self.time_toggle)
        self.time_render_settings.clicked.connect(self.time_toggle)
        self.time_slider.clicked.connect(self.time_toggle)

        self.frame_relative_checkbox.clicked.connect(self.relative_toggle)
        self.frame_relative_keys.textChanged.connect(self.keys_changed)

        self.export_btn.clicked.connect(self.export_clicked)
        self.close_btn.clicked.connect(self.close_clicked)

    def time_toggle(self):
        if not self.time_start_end.isChecked():
            self.time_start.setEnabled(False)
            self.time_end.setEnabled(False)
        else:
            self.time_start.setEnabled(True)
            self.time_end.setEnabled(True)

    def relative_toggle(self):
        if not self.frame_relative_checkbox.isChecked():
            self.frame_relative_low.setEnabled(False)
            self.frame_relative_high.setEnabled(False)
            self.frame_relative_keys.setEnabled(False)
        else:
            self.frame_relative_low.setEnabled(True)
            self.frame_relative_high.setEnabled(True)
            self.frame_relative_keys.setEnabled(True)

    def keys_changed(self):
        if self.frame_relative_keys.text():
            key_num = int(self.frame_relative_keys.text())
            if key_num % 2 == 0:
                print 'even'
            else:
                print 'odd'

    def close_clicked(self):
        self.close()

    def export_clicked(self):
        project_location=cmds.workspace( q=True, fn=True )
        cache_dir = os.path.join(project_location, 'cache', 'alembic')

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        output_path = cmds.fileDialog2(dialogStyle=2, dir=cache_dir)[0]

        time = None
        relative_samples = []
        visibility = None
        root_node = '|'
        selected_nodes = cmds.ls(sl=True, l=True)

        # time
        if self.time_render_settings.isChecked():
            start = float(cmds.getAttr('defaultRenderGlobals.startFrame'))
            end = float(cmds.getAttr('defaultRenderGlobals.endFrame'))
        
        elif self.time_slider.isChecked():
            start = float(cmds.playbackOptions(q=True, ast=True))
            end = float(cmds.playbackOptions(q=True, aet=True))
        
        elif self.time_start_end.isChecked():
            start = float(self.time_start.text())
            end = float(self.time_end.text())
        
        time = [start, end]

        # frame relative samples
        if self.frame_relative_checkbox.isChecked():
            frs_start = float(self.frame_relative_low.text())
            frs_end = float(self.frame_relative_high.text())
            keys = int(self.frame_relative_keys.text())

            # numpy.linspace - allows you to get x number of keys between a range - evenly spaced
            relative_samples = numpy.linspace(frs_start, frs_end, keys)

        # visibility
        if self.options_write_visibility.isChecked():
            visibility = True
        else:
            visibility = False

        # uvs
        if self.options_write_uvs.isChecked():
            uvs = True
        else:
            uvs = False

        # world space
        if self.options_world_space.isChecked():
            world = True
        else:
            world = False

        # verbosity
        if self.options_verbosity.isChecked():
            verbosity = True
        else:
            verbosity = False

        # euler
        if self.options_euler.isChecked():
            euler = True
        else:
            euler = False

        # print 'OUTPUT PATH : %s' % output_path
        if output_path.endswith('.*'):
            output_path = output_path.split('.*')[0] + '.abc'
        # print output_path

        # build command
        cmd = 'AbcExport -j "'
        cmd += '-fr %s %s ' % (time[0], time[1])
        if relative_samples != []:
            for key in relative_samples:
                cmd += '-frs %s ' % key

        if self.selected_radio.isChecked():
            for node in selected_nodes:
                print 'selected : %s' % node
                if node.startswith('|'):
                    cmd += '-root %s ' % node
                else:
                    cmd += '-root |%s ' % node

        if visibility:
            cmd += '-writeVisibility '

        if uvs:
            cmd += '-uvWrite '

        if world:
            cmd += '-worldSpace '

        if euler:
            cmd += '-eulerFilter '

        if verbosity:
            cmd += '-verbose '

        cmd += '-df Ogawa '
        cmd += '-f %s' % output_path
        cmd += '"'

        # NOW EXECUTE COMMAND
        print cmd
        mel.eval(cmd)

class ExportPackage(QtWidgets.QWidget):    
    def __init__(self, win):        
        super(ExportPackage, self).__init__(win)
        
        # self.setAttribute(QtCore.Qt.WA_DeleteOnClose) 
        
        #Parent widget under Maya main window        
        #self.setParent(win)        
        self.setWindowFlags(QtCore.Qt.Window)   
        
        self.setObjectName('Export Manager')
        self.setWindowTitle('Export Manager')        
        self.setGeometry(50, 50, 250, 150)
        
        self.main_layout = QtWidgets.QVBoxLayout()
           
        self.initUI()
        self.setLayout(self.main_layout)

        self.setDefaults()
        self.setConnections()

    def initUI(self):
        # FONTS
        self.bold_font = QtGui.QFont()
        self.bold_font.setBold(True)


        self.prefix = QtWidgets.QLineEdit('')
        self.folder_chk = QtWidgets.QCheckBox('Export to Sub Folder') 

        self.json_chk = QtWidgets.QCheckBox('Json')
        self.shader_chk = QtWidgets.QCheckBox('Shaders (Connected)')
        self.settings_chk = QtWidgets.QCheckBox('Render Options')
        # self.alembic_chk = QtGui.QCheckBox('Alembic')
        # self.merge_chk = QtGui.QCheckBox('Merge Json')
        self.export_btn = QtWidgets.QPushButton('Export')
        self.export_btn.setEnabled(False)
        self.close_btn = QtWidgets.QPushButton('Close')

        self.layout = QtWidgets.QVBoxLayout()
        self.prefix_layout = QtWidgets.QVBoxLayout()
        self.opt_layout = QtWidgets.QHBoxLayout()
        
        # self.prefix_hlayout.addWidget(self.prefix_label)
        self.prefix_layout.addWidget(self.prefix)
        self.prefix_layout.addWidget(self.folder_chk)

        self.prefix_group = QtWidgets.QGroupBox('Prefix')
        self.prefix_group.setLayout(self.prefix_layout)

        # self.layout.addWidget(self.folder_chk)
        
        self.opt_layout.addWidget(self.json_chk)
        self.opt_layout.addWidget(self.shader_chk)
        self.opt_layout.addWidget(self.settings_chk)        
        # self.opt_layout.addWidget(self.alembic_chk)
        # self.opt_layout.addWidget(self.merge_chk) 
        self.warning = QtWidgets.QLabel('WARNING : PLEASE BE AWARE THAT YOU ARE ONLY EXPORTING THE SCENE BASED ASSIGNMENTS AND SHADERS.\n\nIF YOU WOULD LIKE TO COMBINE EXISTING JSON / SHADER FILES WITH YOUR SCENE BASED ASSIGNMENTS,\n\nPLEASE IMPORT/IMPORT & MERGE THEM FIRST, THEN EXPORT.')       
        self.opt_group = QtWidgets.QGroupBox('Options')
        self.opt_group.setLayout(self.opt_layout)
        
        self.layout.addWidget(self.prefix_group)
        self.layout.addWidget(self.opt_group)

        self.layout.addWidget(self.warning)
        

        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.addWidget(self.export_btn)
        self.bottom_layout.addWidget(self.close_btn)

        self.layout.addLayout(self.bottom_layout)
        self.layout.addStretch()

        self.setLayout(self.layout)
    
    def setDefaults(self):
        self.json_chk.setChecked(True)
        self.shader_chk.setChecked(True)
        self.folder_chk.setChecked(True)

    # def checkSelection(self):
    #     tr = cmds.ls( type= 'transform', sl=1) + cmds.ls(type= 'alembicHolder', sl=1)

    #     if len(tr) == 0:
    #         x = cmds.confirmDialog( title='Selection', message='Please select an Alembic Holder cache', button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )
    #         return False
    #     else:
    #         return True

    def setConnections(self):
        self.export_btn.clicked.connect(self.export_clicked)
        self.close_btn.clicked.connect(self.close_clicked)
        self.prefix.textChanged.connect(self.prefix_text_changed)

    def close_clicked(self):
        # self.setDefaults()
        self.close()

    def prefix_text_changed(self):
        if self.prefix.text() == "":
            self.export_btn.setEnabled(False)
        else:
            self.export_btn.setEnabled(True)

    def export_clicked(self):
        return_codes = []

        # # OUTPUT PATH
        # singleFilter = "Json Files (*.json)"
        # output_path = cmds.fileDialog2(fileFilter=singleFilter, dialogStyle=2)

        # if not output_path:
        #     return
        # else:
        #     output_path = output_path[0]
        #     if not output_path.endswith('.json'):
        #         ext = output_path.split('.')[-1]
        #         output_path = output_path.replace('.' + ext, '.json')
        #     else:
        #         output_path = os.path.join(output_directory, output_name) + '.json')

        jsonn = self.json_chk.isChecked()
        shader = self.shader_chk.isChecked()
        settings = self.settings_chk.isChecked()        
        folder = self.folder_chk.isChecked()

        project_location=cmds.workspace( q=True, fn=True )
        lookdev_dir = os.path.join(project_location, 'lookdev')

        if not os.path.exists(lookdev_dir):
            os.makedirs(lookdev_dir)

        output_directory = cmds.fileDialog2(dialogStyle=2, dir=lookdev_dir, fileMode=3)[0]
        output_name = self.prefix.text()

        # if output_name == "":
        #     res = cmds.confirmDialog( title='Please ', message='%s already exist.\nDo you want to replace them?' % confirm_msg, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )

        if folder:
            output_directory = os.path.join(output_directory, output_name)

        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        shader_path = os.path.join(output_directory, output_name) + '_shaders.abc'
        json_path = os.path.join(output_directory, output_name) + '_assignments.json'
        settings_path = os.path.join(output_directory, output_name) + '_render_settings.json'        

        confirm_msg = ''

        if os.path.isfile(shader_path):
            confirm_msg += '%s\n\n' % shader_path

        if os.path.isfile(json_path):
            confirm_msg += '%s\n\n' % json_path

        if confirm_msg != '':
            res = cmds.confirmDialog( title='Confirm Overwrite', message='%salready exist.\nDo you want to replace them?' % confirm_msg, button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
            if res == 'Yes':
                pass
            else:
                return

        if jsonn:
            x = abcToApi.getSelected(cls=True)
            for i in x:
                # were disbaling the merging of json files, even though it works fine
                # until we have a working shader merge module, doesnt make sense to have this merge also
                # instead we moved the merge logic into the import side, so artist can import json and shaders
                # directly from ae template
                
                json_return = i.writeJson(merge=False, json_out_path=json_path)
                return_codes.append(json_return)
        
        if shader:
            x = abcToApi.getSelected(cls=True)
            for i in x:
                # were disbaling this for now - ideally we want the cask module to stitch two abc material file together
                # really dont want to have to subprocess maya in any way just to re-export the merged maya scene
                # have an open discussion with author of cask module, ryan galloway

                # merge is false for now

                shader_return = i.writeAbcShaders(merge=False, shader_out_path=shader_path)
            
                return_codes.append(shader_return)

        if settings:
            import maya.app.renderSetup.model.renderSetup as renderSetup
            with open(settings_path, "w+") as file:
                json.dump(renderSetup.instance().encode(None), fp=file, indent=2, sort_keys=True)
        
        msg = ''
        for i in return_codes:
            msg += '%s\n' % i

        cmds.confirmDialog( title='Export Finished', message=msg, button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok' )