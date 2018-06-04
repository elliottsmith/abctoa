import maya.cmds as cmds
from alembicHolder.cmds import abcToApi

def registerCallbacks():
	print 'abcToA userSetup.py'

	selectionChangedJob = cmds.scriptJob( event = ["SelectionChanged", selectionChanged])

def selectionChanged():
    """ Selction changed callback"""

    selected = abcToApi.getCurrentSelection()    
    # check time is connected to alembicHolder and that shaders / displacements that
    # are seen in the json assignments string exists in the scene
    if selected:
        abcToApi.checkTime(selected)
        abcToApi.checkShadersAssignation(selected)
        abcToApi.checkLayersOverride(selected)

cmds.evalDeferred(registerCallbacks)	
