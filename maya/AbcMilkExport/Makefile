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

SRCDIR := $(TOP)/AbcMilkExport
DSTDIR := $(TOP)/AbcMilkExport

AbcMilkExport_SOURCES  := $(TOP)/AbcMilkExport/AbcMilkExport.cpp $(TOP)/AbcMilkExport/AbcWriteJob.cpp $(TOP)/AbcMilkExport/AttributesWriter.cpp $(TOP)/AbcMilkExport/MayaMeshWriter.cpp $(TOP)/AbcMilkExport/MayaPointPrimitiveWriter.cpp $(TOP)/AbcMilkExport/MayaTransformWriter.cpp $(TOP)/AbcMilkExport/MayaUtility.cpp $(TOP)/AbcMilkExport/MayaCameraWriter.cpp $(TOP)/AbcMilkExport/MayaNurbsCurveWriter.cpp $(TOP)/AbcMilkExport/MayaLocatorWriter.cpp $(TOP)/AbcMilkExport/MayaNurbsSurfaceWriter.cpp
AbcMilkExport_OBJECTS  := $(TOP)/AbcMilkExport/AbcMilkExport.o $(TOP)/AbcMilkExport/AbcWriteJob.o $(TOP)/AbcMilkExport/AttributesWriter.o $(TOP)/AbcMilkExport/MayaMeshWriter.o $(TOP)/AbcMilkExport/MayaPointPrimitiveWriter.o $(TOP)/AbcMilkExport/MayaTransformWriter.o $(TOP)/AbcMilkExport/MayaUtility.o $(TOP)/AbcMilkExport/MayaCameraWriter.o $(TOP)/AbcMilkExport/MayaNurbsCurveWriter.o $(TOP)/AbcMilkExport/MayaLocatorWriter.o $(TOP)/AbcMilkExport/MayaNurbsSurfaceWriter.o
AbcMilkExport_PLUGIN   := $(DSTDIR)/AbcMilkExport.$(EXT)
AbcMilkExport_MAKEFILE := $(DSTDIR)/Makefile

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

$(AbcMilkExport_OBJECTS): CFLAGS   := $(CFLAGS)   $(AbcMilkExport_EXTRA_CFLAGS)
$(AbcMilkExport_OBJECTS): C++FLAGS := $(C++FLAGS) $(AbcMilkExport_EXTRA_C++FLAGS)
$(AbcMilkExport_OBJECTS): INCLUDES := $(INCLUDES) $(AbcMilkExport_EXTRA_INCLUDES)

depend_AbcMilkExport:     INCLUDES := $(INCLUDES) $(AbcMilkExport_EXTRA_INCLUDES)

$(AbcMilkExport_PLUGIN):  LFLAGS   := $(LFLAGS) $(AbcMilkExport_EXTRA_LFLAGS) 
$(AbcMilkExport_PLUGIN):  LIBS     := $(LIBS)   -lOpenMaya -lFoundation -lOpenMayaAnim -lOpenMayaFX -lOpenMayaRender -lOpenMayaUI -lAlembicAbcCoreFactory -lAlembicAbcCoreHDF5 -lAlembicAbcCoreOgawa -lAlembicAbcGeom -lAlembicAbc -lAlembicAbcCoreAbstract -lAlembicAbcMaterial -lAlembicAbcCollection -lAlembicOgawa -lAlembicUtil -lhdf5_hl -lhdf5 -lAlembicIex -lAlembicHalf -lAlembicImath -lz $(AbcMilkExport_EXTRA_LIBS) 

#
# Rules definitions
#

.PHONY: depend_AbcMilkExport clean_AbcMilkExport Clean_AbcMilkExport


$(AbcMilkExport_PLUGIN): $(AbcMilkExport_OBJECTS) 
	-rm -f $@
	$(LD) -o $@ $(LFLAGS) $^ $(LIBS)

depend_AbcMilkExport :
	makedepend $(INCLUDES) $(MDFLAGS) -f$(DSTDIR)/Makefile $(AbcMilkExport_SOURCES)

clean_AbcMilkExport:
	-rm -f $(AbcMilkExport_OBJECTS)

Clean_AbcMilkExport:
	-rm -f $(AbcMilkExport_MAKEFILE).bak $(AbcMilkExport_OBJECTS) $(AbcMilkExport_PLUGIN)


prebuiltPlugins: $(AbcMilkExport_PLUGIN)
depend:	 depend_AbcMilkExport
clean:	 clean_AbcMilkExport
Clean:	 Clean_AbcMilkExport

