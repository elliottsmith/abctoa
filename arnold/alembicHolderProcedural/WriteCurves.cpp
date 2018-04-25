//-*****************************************************************************
//
// Copyright (c) 2016,
//  Nozon
//
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are
// met:
// *       Redistributions of source code must retain the above copyright
// notice, this list of conditions and the following disclaimer.
// *       Redistributions in binary form must reproduce the above
// copyright notice, this list of conditions and the following disclaimer
// in the documentation and/or other materials provided with the
// distribution.
// *       Neither the name of Sony Pictures Imageworks, nor
// Industrial Light & Magic, nor the names of their contributors may be used
// to endorse or promote products derived from this software without specific
// prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
// "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
// LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
// A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
// OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
// LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
// DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
// THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//-*****************************************************************************


#include "WriteCurves.h"
#include "WriteTransform.h"
#include "WriteOverrides.h"
#include "ArbGeomParams.h"
#include "parseAttributes.h"
#include "NodeCache.h"

#include "../../common/PathUtil.h"

#include <ai.h>
#include <sstream>

#include "json/value.h"

//-*****************************************************************************

#if AI_VERSION_ARCH_NUM == 3
    #if AI_VERSION_MAJOR_NUM < 4
        #define AiNodeGetNodeEntry(node)   ((node)->base_node)
    #endif
#endif

//-*************************************************************************
// getSampleTimes
// This function fill the sampleTimes timeSet array.

void getSampleTimes(
    ICurves & prim,
    ProcArgs & args,
    SampleTimeSet & sampleTimes
    )
{
    Alembic::AbcGeom::ICurvesSchema  &ps = prim.getSchema();
    TimeSamplingPtr ts = ps.getTimeSampling();

    sampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );
}

//-*************************************************************************

//-*************************************************************************
// getHash
// This function return the hash of the points, with attributes applied to it.
std::string getHash(
    const std::string& name,
    const std::string& originalName,
    ICurves & prim,
    ProcArgs & args,
    const SampleTimeSet& sampleTimes
    )
{
    Alembic::AbcGeom::ICurvesSchema  &ps = prim.getSchema();

    TimeSamplingPtr ts = ps.getTimeSampling();

    std::string cacheId;

    SampleTimeSet singleSampleTimes;
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ICompoundProperty arbGeomParams = ps.getArbGeomParams();
    ISampleSelector frameSelector( *singleSampleTimes.begin() );

  //get tags
    std::vector<std::string> tags;
    getAllTags(prim, tags, &args);


    // overrides that can't be applied on instances
    // we create a hash from that.
    std::string hashAttributes("@");
    Json::FastWriter writer;
    Json::Value rootEncode;


    if(args.linkAttributes)
    {
        bool foundInPath = false;
        for(std::vector<std::string>::iterator it=args.attributes.begin(); it!=args.attributes.end(); ++it)
        {
            Json::Value overrides;
            if(it->find("/") != string::npos)
            {
                if(pathContainsOtherPath(originalName, *it))
                {
                    overrides = args.attributesRoot[*it];
                    foundInPath = true;
                }

            }
            else if(matchPattern(originalName,*it)) // based on wildcard expression
            {
                overrides = args.attributesRoot[*it];
                foundInPath = true;
            }
            else if(foundInPath == false)
            {
                if (std::find(tags.begin(), tags.end(), *it) != tags.end())
                {
                    overrides = args.attributesRoot[*it];
                }
            }
            if(overrides.size() > 0)
            {
                for( Json::ValueIterator itr = overrides.begin() ; itr != overrides.end() ; itr++ )
                {
                    std::string attribute = itr.key().asString();

                    if (attribute=="mode"
                        || attribute=="min_pixel_width"
                        || attribute=="step_size"
                        || attribute=="invert_normals"
                        )
                    {
                        Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                        rootEncode[attribute]=val;
                    }
                }
            }
        }
    }

    hashAttributes += writer.write(rootEncode);

    std::ostringstream buffer;
    AbcA::ArraySampleKey sampleKey;

    for ( SampleTimeSet::iterator I = sampleTimes.begin();
            I != sampleTimes.end(); ++I )
    {
        ISampleSelector sampleSelector( *I );
        ps.getPositionsProperty().getKey(sampleKey, sampleSelector);

        buffer << GetRelativeSampleTime( args, (*I) ) << ":";
        sampleKey.digest.print(buffer);
        buffer << ":";
    }

    buffer << "@" << computeHash(hashAttributes);

    cacheId = buffer.str();

    return cacheId;

}

AtNode* writeCurves(  
    const std::string& name,
    const std::string& originalName,
    const std::string& cacheId,
    ICurves & prim,
    ProcArgs & args,
    const SampleTimeSet& sampleTimes
    )
{
    // initialise some vars
	std::vector<AtVector> vlist;
	std::vector<double> radius;
	std::vector<double> finalRadius;

	size_t numCurves;
	Int32ArraySamplePtr nVertices;
	int basis = 3;

    float radiusCurves = 1.0f;
    float scaleVelocity = 1.0f/args.fps;
    std::string radiusParam = "pscale";    

    // get the curves schema from the curves reference
    Alembic::AbcGeom::ICurvesSchema  &ps = prim.getSchema();

    // get the timesamples from the curves refernce
    TimeSamplingPtr ts = ps.getTimeSampling();

    // new time sampling var
    SampleTimeSet singleSampleTimes;

    // add curves timesampling for current frame to newly created singleSampleTimes
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    // get arbitrary geo properties
    ICompoundProperty arbGeomParams = ps.getArbGeomParams();

    // via a pointer, get samples
    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    //get tags  
    std::vector<std::string> tags;
    getAllTags(prim, tags, &args);

    // create the arnold node, set name and visibilty and check if valid
	AtNode* curvesNode = AiNode( "curves" );
    AiNodeSetStr( curvesNode, "name", (name + ":src").c_str() );
    AiNodeSetByte( curvesNode, "visibility", 0 );
    if (!curvesNode)
    {
        AiMsgError("[WriteCurves] Failed to make points node for %s", prim.getFullName().c_str());
        return NULL;
    }

    // add to created nodes - if we need this again (instanced?)
	args.createdNodes->addNode(curvesNode);
    
    // check for radiusCurves arg param - exposed in shader manager
	if (AiNodeLookUpUserParameter(args.proceduralNode, "radiusCurves") !=NULL )
        radiusCurves = AiNodeGetFlt(args.proceduralNode, "radiusCurves");
    
	// look for various attributes and set them on curvesNode and / or store them for future use
    if(args.linkAttributes)
    {
        for(std::vector<std::string>::iterator it=args.attributes.begin(); it!=args.attributes.end(); ++it)
        {
            if(name.find(*it) != string::npos || std::find(tags.begin(), tags.end(), *it) != tags.end() || matchPattern(name,*it))
            {
                Json::Value overrides = args.attributesRoot[*it];
                if(overrides.size() > 0)
                {
                    for( Json::ValueIterator itr = overrides.begin() ; itr != overrides.end() ; itr++ )
                    {
                        std::string attribute = itr.key().asString();

                        if(attribute == "radius_attribute")
                        {
                            Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                            radiusParam = val.asString();
                        }

                        if(attribute == "radius_multiplier")
                        {
                            Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                            radiusCurves *= val.asDouble();
                        }

                        if(attribute == "velocity_multiplier")
                        {
                            Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                            scaleVelocity *= val.asDouble();
                        }

                        if (attribute=="mode"
                            || attribute=="min_pixel_width"
                            || attribute=="step_size"
                            || attribute=="invert_normals")
                        {
                            //AiMsgDebug("[WriteCurves] Checking attribute %s for shape %s", attribute.c_str(), name.c_str());
                            // check if the attribute exists ...
                            const AtNodeEntry* nodeEntry = AiNodeGetNodeEntry(curvesNode);
                            const AtParamEntry* paramEntry = AiNodeEntryLookUpParameter(nodeEntry, attribute.c_str());

                            if ( paramEntry != NULL)
                            {
                                //AiMsgDebug("[WriteCurves] attribute %s exists on shape", attribute.c_str());
                                Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                                if( val.isString() )
                                    AiNodeSetStr(curvesNode, attribute.c_str(), val.asCString());
                                else if( val.isBool() )
                                    AiNodeSetBool(curvesNode, attribute.c_str(), val.asBool());
                                else if ( val.type() == Json::realValue )
                                    AiNodeSetFlt(curvesNode, attribute.c_str(), val.asDouble());
                                else if( val.isInt() )
                                {
                                    //make the difference between Byte & int!
                                    int typeEntry = AiParamGetType(paramEntry);
                                    if(typeEntry == AI_TYPE_BYTE)
                                        AiNodeSetByte(curvesNode, attribute.c_str(), val.asInt());
                                    else
                                        AiNodeSetInt(curvesNode, attribute.c_str(), val.asInt());
                                }
                                else if( val.isUInt() )
                                    AiNodeSetUInt(curvesNode, attribute.c_str(), val.asUInt());
                            }
                        }
                    }
                }
            }
        }
    }

    bool isFirstSample = true;

    // set the radiusProperty node parameter is it exists
    if (AiNodeLookUpUserParameter(args.proceduralNode, "radiusProperty") !=NULL )
        radiusParam = std::string(AiNodeGetStr(args.proceduralNode, "radiusProperty"));

    bool useVelocities = false;
    // if we only have one time sample but motion blur is required
    if ((sampleTimes.size() == 1) && (args.shutterOpen != args.shutterClose))
    {
        // no sample, and motion blur needed, let's try to get velocities.
        if(ps.getVelocitiesProperty().valid())
            useVelocities = true;
    }


    // create an sample iterator from the begining of the time sample
    for ( SampleTimeSet::iterator I = sampleTimes.begin(); I != sampleTimes.end(); ++I, isFirstSample = false)
    {

        // grab the sample as a reference
        ISampleSelector sampleSelector( *I );

        // get the curves schema at specific sample
        Alembic::AbcGeom::ICurvesSchema::Sample sample = ps.getValue( sampleSelector );

        // get positions as an array pointer?
        Alembic::Abc::P3fArraySamplePtr v3ptr = sample.getPositions();
        
        // also get its size - usually it'll be 3 samples -0.25/+0.25
        size_t pSize = sample.getPositions()->size();


        // handling radius
        // init an empty width sample
        IFloatGeomParam::Sample widthSamp;

        // init width params, get mesh width
        IFloatGeomParam widthParam = ps.getWidthsParam();

        if(!widthParam)
        {
            // if the mesh doesnt have width, get any arbitrary params
            ICompoundProperty prop = ps.getArbGeomParams();
            if ( prop != NULL && prop.valid() )
            {
                // if 'pscale' property is found
                if (prop.getPropertyHeader(radiusParam) != NULL)
                {
                    const PropertyHeader * tagsHeader = prop.getPropertyHeader(radiusParam);

                    // check the type
                    if (IFloatGeomParam::matches( *tagsHeader ))
                    {   
                        // get the arbitrary width param and sample
                        widthParam = IFloatGeomParam( prop,  tagsHeader->getName());
                        widthSamp = widthParam.getExpandedValue( sampleSelector );
                    }
                }
            }
        }
        else
            widthParam.getExpanded(widthSamp, sampleSelector);


		if ( isFirstSample )
            // if its the first sample
		{
            // numCurves and nVertices are size_t type and Int32ArraySamplePtr type, respectively
			numCurves = sample.getNumCurves();
			nVertices = sample.getCurvesNumVertices();   

            // find the basis type of the sample, we support, bezier, bspline and catmull
			BasisType basisType = sample.getBasis();
            if ( basisType != kNoBasis )
            {
                switch ( basisType )
                {
                case kBezierBasis:
                    basis =  0;
                    break;
                case kBsplineBasis:
                    basis = 1;
                    break;
                case kCatmullromBasis:
                    basis = 2;
                    break;
                case kHermiteBasis:
					break;
                case kPowerBasis:
					break;
                default:
                    break;
                }
            }
			if(widthSamp)
			{
                // if the curve mesh has width, add those samples to the radius vector

                // for every sample in the sample array, get the coresponding width sample
                // then multiply that value by the radius curve - default 1.0f

                // this is only used if finalRadius is empty
				for ( size_t pId = 0; pId < pSize; ++pId )
					radius.push_back((double(*widthSamp.getVals())[pId] * radiusCurves));
			}

		}

        
        // HACK
        if(useVelocities && isFirstSample)
        {
            // no sample, motion needed and first sample - eeeek
            
            // default is 1.0f/args.fps = 1.00/24 = 0.0416666
            if (AiNodeLookUpUserParameter(args.proceduralNode, "scaleVelocity") !=NULL )
                scaleVelocity *= AiNodeGetFlt(args.proceduralNode, "scaleVelocity");

            // vlist is our list if AtVectors - we fake additional samples
            vlist.resize(pSize*2);
            Alembic::Abc::V3fArraySamplePtr velptr = sample.getVelocities();

            // low / high samples
            float timeoffset = ((args.frame / args.fps) - ts->getFloorIndex((*I), ps.getNumSamples()).second) * args.fps;

            for ( size_t pId = 0; pId < pSize; ++pId )
            {
                if(pId <= velptr->size())
                {
                    Alembic::Abc::V3f posAtOpen = ((*v3ptr)[pId] + (*velptr)[pId] * scaleVelocity *-timeoffset);
                    AtVector pos1;
                    pos1.x = posAtOpen.x;
                    pos1.y = posAtOpen.y;
                    pos1.z = posAtOpen.z;
                    vlist[pId]= pos1;

                    Alembic::Abc::V3f posAtEnd = ((*v3ptr)[pId] + (*velptr)[pId]* scaleVelocity *(1.0f-timeoffset));
                    AtVector pos2;
                    pos2.x = posAtEnd.x;
                    pos2.y = posAtEnd.y;
                    pos2.z = posAtEnd.z;
                    vlist[pId+pSize]= pos2;
                }
            }
        }
        else
            // not motion blur or correctly sampled curves
        {
            // for every sample, create an arnold AtVector
            for ( size_t pId = 0; pId < pSize; ++pId )
            {
                AtVector pos;
                pos.x = (*v3ptr)[pId].x;
                pos.y = (*v3ptr)[pId].y;
                pos.z = (*v3ptr)[pId].z;
                vlist.push_back(pos);
            }
        }
    }

    // we now have a vector of AtVectors - vlist - made from the Alembic::Abc::P3fArraySamplePtr v3ptr pointer

    // init an arnold array - numCuvres may be null - or taken from sample if were on the first sample (size_t)
	AtArray* curveNumPoints = AiArrayAllocate( numCurves , 1, AI_TYPE_UINT);

    // positive int
	unsigned int w_end = 0;

    for ( size_t i = 0; i < numCurves ; i++ )
	{
        // for each in size_t numCurves, get the index from the Int32ArraySamplePtr get method
		unsigned int c_verts = nVertices->get()[i];

        // add to the curve array
		AiArraySetUInt(curveNumPoints, i, c_verts);


        // radius will always be empty if widthSamp is NULL
		if ( !radius.empty() && ( basis == 1 || basis == 2 ) /* for spline & catmull */ )
		{
			unsigned int w_start = w_end;
			w_end += c_verts;
			std::vector<double> this_range(radius.begin() + w_start, radius.begin() + w_end );

			for ( size_t r=0; r < this_range.size(); ++r )
			{
              if ( r != 1 && r !=this_range.size()-2 )
                finalRadius.push_back(this_range[r]);
			}
		}
		else if ( !radius.empty() && basis == 0 /* for bezier */ )
		{
			//  skip the control points.
			unsigned int w_start = w_end;
			w_end += c_verts;
			std::vector<double> this_range(radius.begin() + w_start, radius.begin() + w_end );

			for (size_t r = 0; r < this_range.size() ; r+=3)
			{
				 finalRadius.push_back(this_range[r]);
			}
		}
	}

	if (!radius.empty() && finalRadius.empty())
		finalRadius.swap(radius);

	if(!finalRadius.empty()){
        AiNodeSetArray(curvesNode, "radius", AiArrayConvert( finalRadius.size(), 1, AI_TYPE_FLOAT, (void*)(&(finalRadius[0])));
	} else {
		AiNodeSetArray(curvesNode, "radius", AiArray( 1 , 1, AI_TYPE_FLOAT, radiusCurves));
    }

    if(!useVelocities){
        AiNodeSetArray(curvesNode, "points", AiArrayConvert( vlist.size() / sampleTimes.size(), sampleTimes.size(), AI_TYPE_VECTOR, (void*)(&(vlist[0]))));
    } else {
        AiNodeSetArray(curvesNode, "points", AiArrayConvert( vlist.size() / 2, 2, AI_TYPE_VECTOR, (void*)(&(vlist[0]))));
    }

	AiNodeSetInt(curvesNode, "basis", basis);
	AiNodeSetArray(curvesNode, "num_points", curveNumPoints);

    // add arbitary geom parameters
    ICompoundProperty arbPointsParams = ps.getArbGeomParams();
    AddArbitraryGeomParams( arbGeomParams, frameSelector, curvesNode );

    // add the node to the nodeCache
	args.nodeCache->addNode(cacheId, curvesNode);
    return curvesNode;

}

//-*************************************************************************
// createInstance
// This function create & return a instance node with shaders & attributes applied.
void createInstance(
    const std::string& name,
    const std::string& originalName,
    ICurves & prim,
    ProcArgs & args,
    MatrixSampleMap * xformSamples,
    AtNode* points)
{
    Alembic::AbcGeom::ICurvesSchema  &ps = prim.getSchema();
    ICompoundProperty arbGeomParams = ps.getArbGeomParams();

    SampleTimeSet singleSampleTimes;
    TimeSamplingPtr ts = ps.getTimeSampling();
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    AtNode* instanceNode = AiNode( "ginstance" );

    AiNodeSetStr( instanceNode, "name", name.c_str() );
    AiNodeSetPtr(instanceNode, "node", points );
    AiNodeSetBool( instanceNode, "inherit_xform", false );
    
    if ( args.proceduralNode )
        AiNodeSetByte( instanceNode, "visibility", AiNodeGetByte( args.proceduralNode, "visibility" ) );
    else
        AiNodeSetByte( instanceNode, "visibility", AI_RAY_ALL );

    // Xform
    ApplyTransformation( instanceNode, xformSamples, args );

    // adding arbitary parameters
    AddArbitraryGeomParams(
            arbGeomParams,
            frameSelector,
            instanceNode );

    // adding attributes on procedural
    AddArbitraryProceduralParams(args.proceduralNode, instanceNode);

    //get tags
    std::vector<std::string> tags;
	getAllTags(prim, tags, &args);

    // Arnold Attribute from json
    if(args.linkAttributes)
        ApplyOverrides(originalName, instanceNode, tags, args);


    // shader assignation
    if (nodeHasParameter( instanceNode, "shader" ))
        ApplyShaders(originalName, instanceNode, tags, args);

    args.createdNodes->addNode(instanceNode);

}


void ProcessCurves( ICurves &curves, ProcArgs &args,
        MatrixSampleMap * xformSamples)
{

    // check the curves are valid
    if ( !curves.valid() )
        return;

    // get the curve name
    std::string originalName = curves.getFullName();

    // create new name with args prefix
    std::string name = args.nameprefix + originalName;

    // init sampleTimes obj and add samples to it
    SampleTimeSet sampleTimes;
    getSampleTimes(curves, args, sampleTimes);

    // create a hash id of curves and attributes
    std::string cacheId = getHash(name, originalName, curves, args, sampleTimes);

    // so, weve checked the curves are valid, initialised some name vars, added time samples
    // and applied attributes to curves, to get a hash

    // now we try and retrieve the arnold mesh node from the node cache as it might already exist
    AtNode* curvesNode = args.nodeCache->getCachedNode(cacheId);

    if(curvesNode == NULL)
    { 
        // We don't have a cache, so we much create this points object.
        curvesNode = writeCurves(name, originalName, cacheId, curves, args, sampleTimes);
    }

    if(curvesNode != NULL)
    {
        // we can create the instance, with correct transform, attributes & shaders.
        createInstance(name, originalName, curves, args, xformSamples, curvesNode);
    }
}

