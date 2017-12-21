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
    
    # reload(shaderManager)
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

        x = cmds.createNode('alembicHolder', n="AlembicHolderShape")
        cmds.setAttr("%s.overrideLevelOfDetail" % x, 1)
        cmds.setAttr("%s.overrideVisibility" % x, 1) 
        cmds.setAttr("%s.visibleInRefractions" % x, 1)
        cmds.setAttr("%s.visibleInReflections" % x, 1)
        cmds.connectAttr("time1.outTime", "%s.time" % x)

        cmds.setAttr("%s.cacheFileNames[0]" % x, f, type='string')

def assignTagsFromSetName():
    sets = cmds.ls(sl=True, type="objectSet")

    for set in sets:
        for s in cmds.sets( set, q=True ):
            tags = []
            if not cmds.objExists(s + ".mtoa_constant_tags"): 
                cmds.addAttr(s, ln='mtoa_constant_tags', dt='string') 
            else:
                try:
                    tags = json.loads(cmds.getAttr(s + ".mtoa_constant_tags"))
                except:
                    pass

            if not set in tags:
                tags.append(set)
                cmds.setAttr(s + ".mtoa_constant_tags", json.dumps(tags), type="string")

def checkConnected():
    print "\n"
    print "*"*100
    print 'Checking Connections'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.checkConnections()

def makeConnected():
    print "\n"
    print "*"*100
    print 'Making Connections'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.checkConnections()
        i.makeConnections()

def breakConnected():
    print "\n"
    print "*"*100
    print 'Breaking Connections'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.breakConnections()

def runProcedural():
    print "\n"
    print "*"*100
    print 'Simulate Render'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.runProcedural()

def validateDictionaries():
    print "\n"
    print "*"*100
    print 'Checking Dictionaries'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.validateDictionaries()

def importJson():
    print "\n"
    print "*"*100
    print 'Importing Json'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.importJson()

def importShaders():
    print "\n"
    print "*"*100
    print 'Importing Shaders'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.importShaders()

def importAbc():
    res = cmds.confirmDialog( title='Transform', message='Do you want to parent the incoming geo to the alembicHolder transform?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
    if res == 'Yes':
        parent_transform = True
    else:
        parent_transform = False

    print "\n"
    print "*"*100
    print 'Importing Abc'
    print "*"*100
    x = abcToApi.getSelected(cls=True)
    for i in x:
        i.importAbc(parent_transform=parent_transform)

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
        cmds.menuItem('exportAlembic', label='Export Alembic', parent='AlembicHolderMenu', c=lambda *args: _exportmanager.show())
        cmds.menuItem( divider=True )
        cmds.menuItem('exportJson', label='Export Shaders / Assignments', parent='AlembicHolderMenu', c=lambda *args: _exportassignments.show())
        cmds.menuItem( divider=True )
        cmds.menuItem('AlembicHolderUtilsMenu', label='Utilities', parent='AlembicHolderMenu', sm=1)
        cmds.menuItem('checkSyntax', label='Validate Dictionaries', parent='AlembicHolderUtilsMenu', c=lambda *args: validateDictionaries())
        cmds.menuItem( divider=True )
        cmds.menuItem('checkConnected', label='Check Connections', parent='AlembicHolderUtilsMenu', c=lambda *args: checkConnected())
        cmds.menuItem('makeConnected', label='Make Connections', parent='AlembicHolderUtilsMenu', c=lambda *args: makeConnected())
        cmds.menuItem('breakConnected', label='Break Connections', parent='AlembicHolderUtilsMenu', c=lambda *args: breakConnected())
        cmds.menuItem( divider=True )
        cmds.menuItem('importJson', label='Import Json', parent='AlembicHolderUtilsMenu', c=lambda *args: importJson())
        # cmds.menuItem('importMergeJson', label='Import + Merge Json', parent='AlembicHolderUtilsMenu', c=lambda *args: importMergeJson())
        cmds.menuItem('importShaders', label='Import Shaders', parent='AlembicHolderUtilsMenu', c=lambda *args: importShaders())
        cmds.menuItem('importAbc', label='Import Abc', parent='AlembicHolderUtilsMenu', c=lambda *args: importAbc())
        cmds.menuItem( divider=True )
        cmds.menuItem('assignTagsSets', label='Assign Tags from Selected Selection Sets', parent='AlembicHolderUtilsMenu', c=lambda *args: assignTagsFromSetName())
        cmds.menuItem('wiki', label='Wiki', parent='AlembicHolderUtilsMenu', c=lambda *args: cmds.launch(webPage='http://wiki/index.php/abcToArnold'))
        cmds.menuItem( divider=True )
        cmds.menuItem('reload', label='Reload (coding)', parent='AlembicHolderUtilsMenu', c=lambda *args: reloadShaderManager(mayaWindow))
        cmds.menuItem('runProcedural', label='Run procedural (beta)', parent='AlembicHolderUtilsMenu', c=lambda *args: runProcedural())
