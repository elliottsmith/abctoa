#-
# ==========================================================================
# Copyright (c) 2011 Autodesk, Inc.
# All rights reserved.
# 
# These coded instructions, statements, and computer programs contain
# unpublished proprietary information written by Autodesk, Inc., and are
# protected by Federal copyright law. They may not be disclosed to third
# parties or copied or duplicated in any form, in whole or in part, without
# the prior written consent of Autodesk, Inc.
# ==========================================================================
#+

ifndef INCL_BUILDRULES

#
# Include platform specific build settings
#
TOP := ..
include $(TOP)/buildrules


#
# Always build the local plug-in when make is invoked from the
# directory.
#
all : prebuiltPlugins

endif

#
# Variable definitions
#

SRCDIR := $(TOP)/AbcMilkImport
DSTDIR := $(TOP)/AbcMilkImport

AbcMilkImport_SOURCES  := $(TOP)/AbcMilkImport/AbcMilkImport.cpp $(TOP)/AbcMilkImport/AbcMilkImportStrings.cpp $(TOP)/AbcMilkImport/AlembicNode.cpp $(TOP)/AbcMilkImport/CreateSceneHelper.cpp $(TOP)/AbcMilkImport/main.cpp $(TOP)/AbcMilkImport/MeshHelper.cpp $(TOP)/AbcMilkImport/NodeIteratorVisitorHelper.cpp $(TOP)/AbcMilkImport/PointHelper.cpp $(TOP)/AbcMilkImport/util.cpp $(TOP)/AbcMilkImport/XformHelper.cpp $(TOP)/AbcMilkImport/CameraHelper.cpp $(TOP)/AbcMilkImport/NurbsCurveHelper.cpp $(TOP)/AbcMilkImport/LocatorHelper.cpp $(TOP)/AbcMilkImport/NurbsSurfaceHelper.cpp $(TOP)/AbcMilkImport/AlembicImportFileTranslator.cpp
AbcMilkImport_OBJECTS  := $(TOP)/AbcMilkImport/AbcMilkImport.o $(TOP)/AbcMilkImport/AbcMilkImportStrings.o $(TOP)/AbcMilkImport/AlembicNode.o $(TOP)/AbcMilkImport/CreateSceneHelper.o $(TOP)/AbcMilkImport/main.o $(TOP)/AbcMilkImport/MeshHelper.o $(TOP)/AbcMilkImport/NodeIteratorVisitorHelper.o $(TOP)/AbcMilkImport/PointHelper.o $(TOP)/AbcMilkImport/util.o $(TOP)/AbcMilkImport/XformHelper.o $(TOP)/AbcMilkImport/CameraHelper.o $(TOP)/AbcMilkImport/NurbsCurveHelper.o $(TOP)/AbcMilkImport/LocatorHelper.o $(TOP)/AbcMilkImport/NurbsSurfaceHelper.o $(TOP)/AbcMilkImport/AlembicImportFileTranslator.o
AbcMilkImport_PLUGIN   := $(DSTDIR)/AbcMilkImport.$(EXT)
AbcMilkImport_MAKEFILE := $(DSTDIR)/Makefile

#
# Include the optional per-plugin Makefile.inc
#
#    The file can contain macro definitions such as:
#       {pluginName}_EXTRA_CFLAGS
#       {pluginName}_EXTRA_C++FLAGS
#       {pluginName}_EXTRA_INCLUDES
#       {pluginName}_EXTRA_LIBS
-include $(SRCDIR)/Makefile.inc


#
# Set target specific flags.
#

$(AbcMilkImport_OBJECTS): CFLAGS   := $(CFLAGS)   $(AbcMilkImport_EXTRA_CFLAGS)
$(AbcMilkImport_OBJECTS): C++FLAGS := $(C++FLAGS) $(AbcMilkImport_EXTRA_C++FLAGS)
$(AbcMilkImport_OBJECTS): INCLUDES := $(INCLUDES) $(AbcMilkImport_EXTRA_INCLUDES)

depend_AbcMilkImport:     INCLUDES := $(INCLUDES) $(AbcMilkImport_EXTRA_INCLUDES)

$(AbcMilkImport_PLUGIN):  LFLAGS   := $(LFLAGS) $(AbcMilkImport_EXTRA_LFLAGS) 
$(AbcMilkImport_PLUGIN):  LIBS     := $(LIBS)   -lOpenMaya -lFoundation -lOpenMayaAnim -lOpenMayaFX -lOpenMayaRender -lOpenMayaUI -lAlembicAbcCoreFactory -lAlembicAbcCoreHDF5 -lAlembicAbcCoreOgawa -lAlembicAbcGeom -lAlembicAbc -lAlembicAbcCoreAbstract -lAlembicAbcMaterial -lAlembicAbcCollection -lAlembicOgawa -lAlembicUtil -lhdf5_hl -lhdf5 -lAlembicIex -lAlembicHalf -lAlembicImath -lz $(AbcMilkImport_EXTRA_LIBS) 

#
# Rules definitions
#

.PHONY: depend_AbcMilkImport clean_AbcMilkImport Clean_AbcMilkImport


$(AbcMilkImport_PLUGIN): $(AbcMilkImport_OBJECTS) 
	-rm -f $@
	$(LD) -o $@ $(LFLAGS) $^ $(LIBS)

depend_AbcMilkImport :
	makedepend $(INCLUDES) $(MDFLAGS) -f$(DSTDIR)/Makefile $(AbcMilkImport_SOURCES)

clean_AbcMilkImport:
	-rm -f $(AbcMilkImport_OBJECTS)

Clean_AbcMilkImport:
	-rm -f $(AbcMilkImport_MAKEFILE).bak $(AbcMilkImport_OBJECTS) $(AbcMilkImport_PLUGIN)


prebuiltPlugins: $(AbcMilkImport_PLUGIN)
depend:	 depend_AbcMilkImport
clean:	 clean_AbcMilkImport
Clean:	 Clean_AbcMilkImport

