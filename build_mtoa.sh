#!/usr/bin/env bash
echo ""
echo "Compiling MtoA"

cd /milk/users/esmith/Downloads/mtoa.git.3.0.0.2

export DISTRIBUTION=centos6
export DSO=so
export COMPILER=gcc-4.9.2
export PYTHONVER=2.7.5

export MAYAVER=2018.2
export ARNOLDVER=5.1.0.1
export MTOAVER=3.0.0.2

export STAGE=/tmp/mtoa
export PROCS=20

rm -rf $STAGE
mkdir $STAGE

rm MtoA-*.run

echo "Compiling MtoA installer"

./abuild ARNOLD=/milk/apps/arnold/Arnold-$ARNOLDVER-linux \
	GLEW_LIB=/milk/code/central/lib/$DISTRIBUTION/$COMPILER/libGLEW.a \
	TARGET_MODULE_PATH=$STAGE \
	MAYA_ROOT=/milk/apps/autodesk/maya/$MAYAVER \
	SHCC=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/gcc \
	SHCXX=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/g++ \
	GLEW_INCLUDES=/milk/code/central/include/$DISTRIBUTION/$COMPILER/ \
	COMPILER=gcc \
	MODE=profile create_installer \
	-j $PROCS

chmod +x MtoA-*.run

rm -rf $STAGE

echo
echo "Finished"
echo "Now run : ./"`ls MtoA-*.run`

