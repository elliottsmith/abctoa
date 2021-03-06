#!/usr/bin/env bash
echo ""
echo "Compiling AbcToA"

pyside-uic maya/scripts/shaderManager/ui/UI_ABCHierarchy.ui -o maya/scripts/shaderManager/ui/UI_ABCHierarchy.py
sed -i 's/from PySide import QtCore, QtGui/from milk.utils.v1_0.pyside.loader import QtCore, QtGui/g' maya/scripts/shaderManager/ui/UI_ABCHierarchy.py

export DISTRIBUTION=centos6
export DSO=so
export COMPILER=gcc-4.9.2
export PYTHONVER=2.7.5

export MAYAVER=2018.2
export MAYASHORT=2018

# ARNOLD 5.0
export ARNOLDVER=5.0.2.4
export ARNOLD_SHORT=5.0
export MTOAVER=2.1.0.3

# sys argv
export PREFIX=$1
export VERSION=$2
export CENTRAL=/milk/code/central

export LDFLAGS="-L$CENTRAL/lib/$DISTRIBUTION/$COMPILER"
export CXXFLAGS="-D_GLIBCXX_USE_CXX11_ABI=0 -I$CENTRAL/include/$DISTRIBUTION/$COMPILER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/OpenEXR"
export CFLAGS="-I$CENTRAL/include/$DISTRIBUTION/$COMPILER"
export CC=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/gcc
export CXX=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/g++

if [[ $PREFIX = *$CENTRAL* ]]; then
	export CMAKE_BUILD_TYPE=Release
else
	export CMAKE_BUILD_TYPE=Debug
fi

export MAYA_VERSION=$MAYAVER
export LD_LIBRARY_PATH=/milk/apps/arnold/Arnold-$ARNOLDVER-linux/bin:$CENTRAL/lib/$DISTRIBUTION/$COMPILER:$LD_LIBRARY_PATH

mkdir BUILD
cd BUILD

echo ""
echo "Running cmake"
echo ""

cmake -DCMAKE_INSTALL_PREFIX=$PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa/$VERSION \
	-DINSTALL_DIR=$PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa/$VERSION \
	-DARNOLD_ROOT=/milk/apps/arnold/Arnold-$ARNOLDVER-linux \
	-DMTOA_BASE_DIR=/milk/apps/arnold/MtoA-${MTOAVER}_${MAYASHORT} \
	-DMAYA_LOCATION=/milk/apps/autodesk/maya/$MAYAVER \
	-DBOOST_ROOT=$CENTRAL/include/$DISTRIBUTION/$COMPILER \
	-DBoost_REGEX_LIBRARY=$CENTRAL/lib/$DISTRIBUTION/$COMPILER/libboost_regex.$DSO \
	-DCMAKE_CXX_FLAGS="-Wno-deprecated-declarations -Wno-enum-compare -Wno-unused-variable -Wno-pointer-arith -I$CENTRAL/include/$DISTRIBUTION/mtoa/$MTOAVER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/OpenEXR -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/jsoncpp" \
	..

echo ""
echo "Running make"
echo ""
make -j 16

# echo "mkdir " $PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa/$VERSION
mkdir -p $PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa/$VERSION

echo ""
echo "Running make install"
echo ""
make install

export MOD_FILE=$PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa.mod
if [ ! -f $MOD_FILE ]; then
	echo ""
	echo "Writing maya module file :" $MOD_FILE
	echo ""

	echo "+ abctoa any $PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa/\$ABCTOAVER" > $MOD_FILE
	echo "PATH +:=procedurals" >> $MOD_FILE
	echo "ARNOLD_PLUGIN_PATH +:=procedurals" >> $MOD_FILE
	echo "MTOA_EXTENSIONS_PATH +:=extensions" >> $MOD_FILE
fi

# copy the procedurals to central arnold shaders
echo ""
echo "Installing procedurals"
echo ""
mkdir -p $PREFIX/addons/$DISTRIBUTION/arnold$ARNOLD_SHORT/abcToA-$VERSION
cp $PREFIX/addons/$DISTRIBUTION/maya$MAYASHORT/modules/abctoa/$VERSION/procedurals/* $PREFIX/addons/$DISTRIBUTION/arnold$ARNOLD_SHORT/abcToA-$VERSION/

cd ..
rm -rf BUILD
