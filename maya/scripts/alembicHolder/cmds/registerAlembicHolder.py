# Alembic Holder
# Copyright (c) 2014, Gael Honorez, All rights reserved.
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library.

import os
import maya.cmds as cmds
import json

import maya.OpenMayaUI as apiUI
import shiboken2
from PySide2 import QtGui, QtWidgets

from alembicHolder.cmds import abcToApi

global _shadermanager
_shadermanager = None

def getMayaWindow():
    """
    Get Main window
    :return: main window 
    """
    mainWindow = QtWidgets.QApplication.activeWindow()
    while True:
        if mainWindow:
            parentWin = mainWindow.parent()
            if parentWin:
                mainWindow = parentWin
            else:
                break
    return mainWindow

def shaderManager(mayaWindow):
    global _shadermanager
    import shaderManager
    return shaderManager.manager(mayaWindow)

def reloadShaderManager(mayaWindow):
    global _shadermanager
    import shaderManager
    _shadermanager.clearing()
    try:
        _shadermanager.deleteLater()
    except:
        pass
    
    reload(shaderManager)
    reload(abcToApi)
    
    _shadermanager = shaderManager.manager(mayaWindow)

def exportManager(mayaWindow):
    ''' export alembic'''
    global _exportmanager
    import alembicExport
    
    reload(alembicExport)
    return alembicExport.manager(win=mayaWindow)

def exportAssignments(mayaWindow):
    ''' export json and shaders'''
    global _exportassignments
    import alembicExport
    
    reload(alembicExport)
    return alembicExport.export_package(win=mayaWindow)

def importPackageManager():
    ''' import package'''

    singleFilter = "ABC Files (*.abc)"
    files = cmds.fileDialog2(fileMode=1, caption="Import Alembic File", fileFilter=singleFilter)
    if files:
        if len(files) > 0:
            f = files[0]

        transform_name = os.path.split(f)[-1].split('.abc')[0]
        x = cmds.createNode("alembicHolder", n="%sShape" % transform_name)
        cmds.setAttr("%s.overrideLevelOfDetail" % x, 1)
        cmds.setAttr("%s.overrideVisibility" % x, 1) 
        cmds.setAttr("%s.visibleInRefractions" % x, 1)
        cmds.setAttr("%s.visibleInReflections" % x, 1)
        cmds.connectAttr("time1.outTime", "%s.time" % x)

        cmds.setAttr("%s.cacheFileNames[0]" % x, f, type='string')

def validateDictionaries():
    print "\n"
    print "*"*100
    print 'Checking Dictionaries'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.validateDictionaries()

def importLookdev():
    print "\n"
    print "*"*100
    print 'Importing Lookdev'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        namespace = i.data['shapeNode'] + '_lookdev'
        i.importLookdev(namespace)

def registerAlembicHolder():
    if not cmds.about(b=1):
        mayaWindow = getMayaWindow()
        
        global _shadermanager
        global _exportmanager
        global _exportassignments

        _shadermanager = shaderManager(mayaWindow)
        _exportmanager = exportManager(mayaWindow)
        _exportassignments = exportAssignments(mayaWindow)

        cmds.menu('AlembicHolderMenu', label='AbcToArnold', parent='MayaWindow', tearOff=True )       
        cmds.menuItem('shaderManager', label='Shader Manager', parent='AlembicHolderMenu', c=lambda *args: _shadermanager.show())
        cmds.menuItem( divider=True )
        cmds.menuItem('importAlembic', label='Load Alembic', parent='AlembicHolderMenu', c=lambda *args: importPackageManager())
        cmds.menuItem( divider=True )        
        cmds.menuItem('AlembicHolderUtilsMenu', label='Utilities', parent='AlembicHolderMenu', sm=1)
        cmds.menuItem('checkSyntax', label='Validate Attributes (Selection)', parent='AlembicHolderUtilsMenu', c=lambda *args: validateDictionaries())
        cmds.menuItem('importJson', label='Localise Lookdev (Selection)', parent='AlembicHolderUtilsMenu', c=lambda *args: importLookdev())
        cmds.menuItem( divider=True )
        cmds.menuItem('reload', label='Reload (coding)', parent='AlembicHolderUtilsMenu', c=lambda *args: reloadShaderManager(mayaWindow))
