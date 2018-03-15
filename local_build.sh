#!/usr/bin/env bash

export DISTRIBUTION=centos6
export DSO=so
export COMPILER=gcc-4.9.2
export PYTHONVER=2.7.5

export CC=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/gcc
export CXX=/milk/code/dev/tools/$DISTRIBUTION/$COMPILER/bin/g++

export MAYAVER=2018.2
export MAYASHORT=_2018
export ARNOLDVER=5.0.2.3
export MTOAVER=2.1.1
export MTOAVER_=2.1.1

export PREFIX=$HOME/devinstall
export CENTRAL=/milk/code/central
export VERSION=dev

export LDFLAGS="-L$CENTRAL/lib/$DISTRIBUTION/$COMPILER"
export CXXFLAGS="-D_GLIBCXX_USE_CXX11_ABI=0 -I$CENTRAL/include/$DISTRIBUTION/$COMPILER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/OpenEXR"
export CFLAGS="-I$CENTRAL/include/$DISTRIBUTION/$COMPILER"
export MAYA_VERSION=$MAYAVER
export LD_LIBRARY_PATH=/milk/apps/arnold/Arnold-$ARNOLDVER-linux/bin:$CENTRAL/lib/$DISTRIBUTION/$COMPILER:$LD_LIBRARY_PATH

mkdir BUILD
cd BUILD

cmake -DCMAKE_INSTALL_PREFIX=$PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa/$VERSION \
	-DINSTALL_DIR=$PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa/$VERSION \
	-DARNOLD_ROOT=/milk/apps/arnold/Arnold-$ARNOLDVER-linux \
	-DMTOA_BASE_DIR=/milk/apps/arnold/MtoA-$MTOAVER_$MAYASHORT \
	-DMAYA_LOCATION=/milk/apps/autodesk/maya/$MAYAVER \
	-DBOOST_ROOT=$CENTRAL/include/$DISTRIBUTION/$COMPILER \
	-DBoost_REGEX_LIBRARY=$CENTRAL/lib/$DISTRIBUTION/$COMPILER/libboost_regex.$DSO \
	-DCMAKE_CXX_FLAGS="-Wno-deprecated-declarations -Wno-enum-compare -Wno-unused-variable -Wno-pointer-arith -I$CENTRAL/include/$DISTRIBUTION/mtoa/$MTOAVER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/OpenEXR -I$CENTRAL/include/$DISTRIBUTION/$COMPILER/jsoncpp -I$PWD/../thirdParty/ezOptionParser" \
	..

mkdir -p $PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa/$VERSION

make -j 16
make install

export MOD_FILE=$PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa.mod
echo "+ abctoa any $PREFIX/addons/$DISTRIBUTION/maya$MAYAVER/modules/abctoa/\$ABCTOAVER" > $MOD_FILE
echo "PATH +:=procedurals" >> $MOD_FILE
echo "ARNOLD_PLUGIN_PATH +:=procedurals" >> $MOD_FILE
echo "MTOA_EXTENSIONS_PATH +:=extensions" >> $MOD_FILE
echo "SAMPLES +:=samples" >> $MOD_FILE

cd ..
rm -rf BUILD