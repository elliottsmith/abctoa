
#ifndef _Alembic_Arnold_WriteCamera_h_
#define _Alembic_Arnold_WriteCamera_h_

#include <Alembic/AbcGeom/All.h>

#include "ProcArgs.h"
#include "SampleUtil.h"

#include <string>
#include <vector>

using namespace Alembic::AbcGeom;
//-*****************************************************************************


void ProcessCamera( ICamera &camera, const ProcArgs &args,
        MatrixSampleMap * xformSamples);

#endif
