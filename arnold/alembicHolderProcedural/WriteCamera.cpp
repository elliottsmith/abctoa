#include "WriteCamera.h"

#include <ai.h>
#include <sstream>

void ProcessCamera( ICamera &camera, const ProcArgs &args,
        MatrixSampleMap * xformSamples)
{
    if (!camera.valid())
        return;

    SampleTimeSet sampleTimes;

    ICameraSchema ps = camera.getSchema();

    TimeSamplingPtr ts = ps.getTimeSampling();
    sampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );


    std::string name = args.nameprefix + camera.getFullName();

    SampleTimeSet singleSampleTimes;
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ISampleSelector sampleSelector( *singleSampleTimes.begin() );

    Alembic::AbcGeom::CameraSample sample = ps.getValue( sampleSelector );

    AtNode * cameraNode = AiNode("persp_camera", name.c_str(), args.proceduralNode);
    AiNodeSetFlt(cameraNode, "fov", sample.getFocalLength());

    args.createdNodes->addNode(cameraNode);
}
