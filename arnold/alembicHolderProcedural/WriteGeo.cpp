//-*****************************************************************************
//
// Copyright (c) 2009-2011,
//  Sony Pictures Imageworks Inc. and
//  Industrial Light & Magic, a division of Lucasfilm Entertainment Company Ltd.
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

#include "WriteGeo.h"
#include "WriteTransform.h"
#include "WriteLight.h"
#include "WriteOverrides.h"
#include "ArbGeomParams.h"
#include "../../common/PathUtil.h"
#include "parseAttributes.h"
#include "NodeCache.h"

#include <ai.h>
#include <sstream>

#include "json/json.h"
#include "json/value.h"

//-*****************************************************************************

#if AI_VERSION_ARCH_NUM == 3
    #if AI_VERSION_MAJOR_NUM < 4
        #define AiNodeGetNodeEntry(node)   ((node)->base_node)
    #endif
#endif

//-*************************************************************************
// ProcessIndexedBuiltinParam
// This function processes the alembic parameters and fills the values vector
template <typename geomParamT>
void ProcessIndexedBuiltinParam( const geomParamT& param, const SampleTimeSet & sampleTimes, std::vector<float> & values, std::vector<unsigned int> & idxs, size_t elementSize)
{
    if ( !param.valid() ) { return; }

    bool isFirstSample = true;
    for ( SampleTimeSet::iterator I = sampleTimes.begin();
          I != sampleTimes.end(); ++I, isFirstSample = false)
    {
        ISampleSelector sampleSelector( *I );


        switch ( param.getScope() )
        {
        case kVaryingScope:
        case kVertexScope:
        {
            // a value per-point, idxs should be the same as vidxs
            // so we'll leave it empty

            // we'll get the expanded form here
            typename geomParamT::Sample sample = param.getExpandedValue(
                    sampleSelector);

            size_t footprint = sample.getVals()->size() * elementSize;

            values.reserve( values.size() + footprint );
            values.insert( values.end(),
                    (float32_t*) sample.getVals()->get(),
                    ((float32_t*) sample.getVals()->get()) + footprint );

            break;
        }
        case kFacevaryingScope:
        {
            // get the indexed form and feed to nidxs

            typename geomParamT::Sample sample = param.getIndexedValue(
                    sampleSelector);

            if ( isFirstSample )
            {
                idxs.reserve( sample.getIndices()->size() );
                idxs.insert( idxs.end(),
                        sample.getIndices()->get(),
                        sample.getIndices()->get() +
                                sample.getIndices()->size() );
            }

            size_t footprint = sample.getVals()->size() * elementSize;
            values.reserve( values.size() + footprint );
            values.insert( values.end(),
                    (const float32_t*) sample.getVals()->get(),
                    ((const float32_t*) sample.getVals()->get()) + footprint );

            break;
        }
        default:
            break;
        }
    }
}

//-*************************************************************************
// getSampleTimes
// This function fills the sampleTimes timeSet array
template <typename primT>
void getSampleTimes( primT & prim, ProcArgs & args, SampleTimeSet & sampleTimes )
{
    typename primT::schema_type  &ps = prim.getSchema();
    TimeSamplingPtr ts = ps.getTimeSampling();
    if ( ps.getTopologyVariance() != kHeterogenousTopology )
    {
        GetRelevantSampleTimes( args, ts, ps.getNumSamples(), sampleTimes );
    }
    else
    {
        sampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );
    }

}

//-*************************************************************************
// doNormals
// This function does nothing for subdv, but write normals for non-subdvided meshes. Called in writeMesh.
// we also have to pass the number of vertex times in case we use motion vectors, as arnold needs the same amount of keys for
// the normals like the vertices
template<typename primT> 
inline void doNormals( primT& prim, AtNode *meshNode, const SampleTimeSet& sampleTimes, size_t numVertexSamples, const std::vector<unsigned int>& vidxs)
{
}

template<> 
inline void doNormals<IPolyMesh>(IPolyMesh& prim, AtNode *meshNode, const SampleTimeSet& sampleTimes, size_t numVertexSamples, const std::vector<unsigned int>& vidxs)
{
    if (AiNodeGetInt(meshNode, "subdiv_type") == 0 && sampleTimes.size() > 0) // if the mesh has subdiv, we don't need normals as they are recomputed by arnold!
    {
        std::vector<float> nlist;
        std::vector<unsigned int> nidxs;

        ProcessIndexedBuiltinParam( prim.getSchema().getNormalsParam(), sampleTimes, nlist, nidxs, 3);


        const size_t numSampleTimes = sampleTimes.size();
        const size_t numNormals = nlist.size() / (numSampleTimes * 3);
        // AiMsgDebug("nlist size : %i, nidxs size : %i, numSampleTimes : %i, numNormals :%i", nlist.size(), nidxs.size(), sampleTimes.size(), numNormals);

        if (numNormals > 0)
        {            
            if (numSampleTimes < numVertexSamples)
            {
                AtArray* narr = AiArrayAllocate(numNormals, numVertexSamples, AI_TYPE_VECTOR);
                const size_t numValidNormals = numNormals * numSampleTimes;
                for (size_t i = 0; i < numValidNormals; ++i)
                {
                    const size_t id = i * 3;
                    AtVector v = AtVector(nlist[id], nlist[id + 1], nlist[id + 2]);
                    AiArraySetVec(narr, i, v);
                }

                const size_t validNormalSource = (numSampleTimes - 1) * 3 * numNormals;
                const size_t sampleDiff = numVertexSamples - numSampleTimes;
                for (size_t i = 0; i < sampleDiff; ++i)
                {
                    const size_t normalTarget = numValidNormals + i * numNormals;
                    for (size_t j = 0; j < numNormals; ++j)
                    {
                        const size_t id = validNormalSource + j * 3;
                        AtVector v = AtVector(nlist[id], nlist[id + 1], nlist[id + 2]);
                        AiArraySetVec(narr, normalTarget + j, v);
                    }
                }
                // AiMsgInfo("  [setting nlist size : %i - using narr AtArray]", AiArrayGetDataSize(narr));
                AiNodeSetArray(meshNode, "nlist", narr);
            }
            else
            {
                // AiMsgInfo("  [setting nlist size : %i - using nlist]", nlist.size());
                AiNodeSetArray(meshNode, "nlist",
                               AiArrayConvert(numNormals,
                                              numVertexSamples, AI_TYPE_VECTOR, &nlist[0]));
            }

            if (!nidxs.empty())
            {
               // we must invert the idxs
               //unsigned int facePointIndex = 0;
               unsigned int base = 0;
               AtArray* nsides = AiNodeGetArray(meshNode, "nsides");
               std::vector<unsigned int> nvidxReversed;
               if ( AiArrayGetNumKeys(nsides) != 0 )
               {
                   for (unsigned int i = 0; i < AiArrayGetNumElements(nsides) / AiArrayGetNumKeys(nsides); ++i)
                   {
                      int curNum = AiArrayGetUInt(nsides ,i);

                      for (int j = 0; j < curNum; ++j)
                      {
                          nvidxReversed.push_back(nidxs[base+curNum-j-1]);
                      }
                      base += curNum;
                   }
                    // AiMsgInfo("  [nidxs is not empty AND nsides has more than 0 keys]");
                    AiNodeSetArray(meshNode, "nidxs", AiArrayConvert(nvidxReversed.size(), 1, AI_TYPE_UINT, &nvidxReversed[0]));
                }
                else {
                    // AiMsgInfo("  [nidxs is not empty BUT nsides has 0 keys - set to vidxs instead]");
                    AiNodeSetArray(meshNode, "nidxs", AiArrayConvert(vidxs.size(), 1, AI_TYPE_UINT, &vidxs[0]));                    
                }
            }
            else
            {
                // AiMsgInfo("  [nidxs is empty - set to vidxs instead]");
                AiNodeSetArray(meshNode, "nidxs",
                        AiArrayConvert(vidxs.size(), 1, AI_TYPE_UINT,
                                &vidxs[0]));
            }
        }
    }
}

//-*************************************************************************
// writeMesh
// This function creates & returns a mesh node with displace & attributes related to it.
template <typename primT>
AtNode* writeMesh( const std::string& name, const std::string& originalName, primT & prim, ProcArgs & args, const SampleTimeSet& sampleTimes )
{
    AiMsgInfo("%s", name.c_str());
    typename primT::schema_type  &ps = prim.getSchema();
    TimeSamplingPtr ts = ps.getTimeSampling();

    SampleTimeSet singleSampleTimes;
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );
    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    //get tags
    std::vector<std::string> tags;
    getAllTags(ps.getObject(), tags, &args);

    // Getting all the data relative to the mesh.
    std::vector<unsigned int> vidxs;
    std::vector<uint32_t> nsides;
    std::vector<float> vlist;
    std::vector<float> uvlist;
    std::vector<unsigned int> uvidxs;

    size_t numSampleTimes = sampleTimes.size();
    bool isFirstSample = true;

    for ( SampleTimeSet::iterator I = sampleTimes.begin();
          I != sampleTimes.end(); ++I, isFirstSample = false)
    {
        ISampleSelector sampleSelector( *I );
        typename primT::schema_type::Sample sample = ps.getValue( sampleSelector );

        if ( isFirstSample )
        {

            size_t numPolys = sample.getFaceCounts()->size();
            nsides.reserve( sample.getFaceCounts()->size() );
            for ( size_t i = 0; i < numPolys; ++i )
            {
                Alembic::Util::uint32_t n = sample.getFaceCounts()->get()[i];
                nsides.push_back( (uint32_t) n );
            }

            size_t vidxSize = sample.getFaceIndices()->size();
            vidxs.reserve( vidxSize );

            unsigned int facePointIndex = 0;
            unsigned int base = 0;

            for (unsigned int i = 0; i < numPolys; ++i)
            {
               // reverse the order of the faces
               int curNum = nsides[i];
               for (int j = 0; j < curNum; ++j, ++facePointIndex)
               {
                  vidxs.push_back((*sample.getFaceIndices())[base+curNum-j-1]);

               }
               base += curNum;
            }
        }

        if(numSampleTimes == 1 && (args.shutterOpen != args.shutterClose) && (ps.getVelocitiesProperty().valid()) && isFirstSample )
        {
            float scaleVelocity = 1.0f/args.fps;

            // Attribute overrides..
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

                                if(attribute == "velocity_multiplier")
                                {
                                    Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                                    scaleVelocity *= val.asDouble();
                                }
                            }
                        }
                    }
                }
            }

            if (AiNodeLookUpUserParameter(args.proceduralNode, "scaleVelocity") !=NULL )
                scaleVelocity *= AiNodeGetFlt(args.proceduralNode, "scaleVelocity");

            Alembic::Abc::V3fArraySamplePtr velptr = sample.getVelocities();
            Alembic::Abc::P3fArraySamplePtr v3ptr = sample.getPositions();

            size_t pSize = sample.getPositions()->size();
            vlist.resize(pSize*3*2);
            numSampleTimes = 2;
            float timeoffset = ((args.frame / args.fps) - ts->getFloorIndex((*I), ps.getNumSamples()).second) * args.fps;
            for ( size_t vId = 0; vId < pSize; ++vId )
            {

                Alembic::Abc::V3f posAtOpen = ((*v3ptr)[vId] + (*velptr)[vId] * scaleVelocity *-timeoffset);
                vlist[3*vId + 0] = posAtOpen.x;
                vlist[3*vId + 1] = posAtOpen.y;
                vlist[3*vId + 2] = posAtOpen.z;

                Alembic::Abc::V3f posAtEnd = ((*v3ptr)[vId] + (*velptr)[vId] * scaleVelocity *(1.0f-timeoffset));
                vlist[3*vId + 3*pSize + 0] = posAtEnd.x;
                vlist[3*vId + 3*pSize + 1] = posAtEnd.y;
                vlist[3*vId + 3*pSize + 2] = posAtEnd.z;
            }
        }
        else
        {

            vlist.reserve( vlist.size() + sample.getPositions()->size() * 3);
            vlist.insert( vlist.end(),
                    (const float32_t*) sample.getPositions()->get(),
                    ((const float32_t*) sample.getPositions()->get()) +
                            sample.getPositions()->size() * 3 );
        }
    }

    // UVs.
    ProcessIndexedBuiltinParam(ps.getUVsParam(), singleSampleTimes, uvlist, uvidxs, 2);

    // Set the meshNode.
    AtNode* meshNode = AiNode( "polymesh", (name + ":src").c_str(), args.proceduralNode );

    if (!meshNode)
    {
        AiMsgError(" Failed to make polymesh node for %s",
                prim.getFullName().c_str());
        return NULL;
    }

    AiNodeSetByte( meshNode, "visibility", 0 );
    AiNodeSetBool(meshNode, "smoothing", true);

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

                        // All these attribute affect the nodeCacheId.
                        if (attribute=="smoothing"
                            || attribute=="subdiv_iterations"
                            || attribute=="subdiv_type"
                            || attribute=="subdiv_adaptive_metric"
                            || attribute=="subdiv_uv_smoothing"
                            || attribute=="subdiv_pixel_error"
                            || attribute=="disp_height"
                            || attribute=="disp_padding"
                            || attribute=="disp_zero_value"
                            || attribute=="disp_autobump"
                            || attribute=="sss_setname"
                            || attribute=="invert_normals"
                            || attribute=="step_size"
                            || attribute=="volume_padding")
                        {
                            const AtNodeEntry* nodeEntry = AiNodeGetNodeEntry(meshNode);
                            const AtParamEntry* paramEntry = AiNodeEntryLookUpParameter(nodeEntry, attribute.c_str());

                            Json::Value val = args.attributesRoot[*it][itr.key().asString()];

                            if ( paramEntry == NULL)
                            {
                                // the param doesn't exists, but we can add it!
                                if( val.isString() )
                                    AiNodeDeclare(meshNode, attribute.c_str(), "constant STRING");
                                else if( val.isBool() )
                                    AiNodeDeclare(meshNode, attribute.c_str(), "constant BOOL");
                                else if ( val.type() == Json::realValue )
                                    AiNodeDeclare(meshNode, attribute.c_str(), "constant FLOAT");
                                else if( val.isInt() || val.isUInt() )
                                    AiNodeDeclare(meshNode, attribute.c_str(), "constant INT");
                            }
                                
                            if( val.isString() )
                                AiNodeSetStr(meshNode, attribute.c_str(), val.asCString());
                            else if( val.isBool() )
                                AiNodeSetBool(meshNode, attribute.c_str(), val.asBool());
                            else if ( val.type() == Json::realValue )
                              AiNodeSetFlt(meshNode, attribute.c_str(), val.asDouble());
                            else if( val.isInt() )
                            {
                                //make the difference between Byte & int!
                                if ( paramEntry != NULL)
                                {
                                    int typeEntry = AiParamGetType(paramEntry);
                                    if(typeEntry == AI_TYPE_BYTE)
                                        AiNodeSetByte(meshNode, attribute.c_str(), val.asInt());
                                    else
                                        AiNodeSetInt(meshNode, attribute.c_str(), val.asInt());
                                }
                                else
                                    AiNodeSetInt(meshNode, attribute.c_str(), val.asInt());
                            }
                            else if( val.isUInt() )
                                AiNodeSetUInt(meshNode, attribute.c_str(), val.asUInt());
                        }
                    }
                }
            }
        }
    }

    // displaces assignation
    // displacement stuff
    AtNode* appliedDisplacement = NULL;
    if(args.linkDisplacement)
    {
        bool foundInPath = false;
        for(std::map<std::string, AtNode*>::iterator it = args.displacements.begin(); it != args.displacements.end(); ++it)
        {
            //check both path & tag
            if(it->first.find("/") != string::npos)
            {
                if(pathContainsOtherPath(originalName, it->first))
                {
                    appliedDisplacement = it->second;
                    foundInPath = true;
                }
            }
            else if(matchPattern(originalName,it->first)) // based on wildcard expression
            {
                appliedDisplacement = it->second;
                foundInPath = true;
            }
            else if(foundInPath == false)
            {
                if (std::find(tags.begin(), tags.end(), it->first) != tags.end())
                {
                    appliedDisplacement = it->second;
                }
            }
        }
    }

    if(appliedDisplacement!= NULL)
        AiNodeSetPtr(meshNode, "disp_map", appliedDisplacement);


    // Fill mesh infos
    AiNodeSetArray(meshNode, "vidxs",
            AiArrayConvert(vidxs.size(), 1, AI_TYPE_UINT,
                    (void*)&vidxs[0]));

    AiNodeSetArray(meshNode, "nsides",
            AiArrayConvert(nsides.size(), 1, AI_TYPE_UINT,
                    &(nsides[0])));

    AiNodeSetArray(meshNode, "vlist",
            AiArrayConvert( vlist.size() / (numSampleTimes * 3),
                    numSampleTimes, AI_TYPE_VECTOR, &vlist[0]
                            ));


    if ( !uvlist.empty() )
    {
       AtArray* a_uvlist = AiArrayAllocate( uvlist.size() , 1, AI_TYPE_FLOAT);

       for (unsigned int i = 0; i < uvlist.size() ; ++i)
       {
          AiArraySetFlt(a_uvlist, i, uvlist[i]);
       }

        AiNodeSetArray(meshNode, "uvlist", a_uvlist);

        if ( !uvidxs.empty() )
        {
           // we must invert the idxs
           unsigned int facePointIndex = 0;
           unsigned int base = 0;

           AtArray* uvidxReversed = AiArrayAllocate(uvidxs.size(), 1, AI_TYPE_UINT);
           for (unsigned int i = 0; i < nsides.size() ; ++i)
           {
              int curNum = nsides[i];
              for (int j = 0; j < curNum; ++j, ++facePointIndex)
                 AiArraySetUInt(uvidxReversed, facePointIndex, uvidxs[base+curNum-j-1]);


              base += curNum;
           }

            AiNodeSetArray(meshNode, "uvidxs",
                  uvidxReversed);
        }
        else
        {
            AiNodeSetArray(meshNode, "uvidxs",
                    AiArrayConvert(vidxs.size(), 1, AI_TYPE_UINT,
                            &(vidxs[0])));
        }
    }
    
    // NORMALS   
    doNormals(prim, meshNode, sampleTimes, numSampleTimes, vidxs);

    // facesets
    std::vector< std::string > faceSetNames;
    ps.getFaceSetNames(faceSetNames);
    
    if ( faceSetNames.size() > 0 )
    {

        std::vector<uint8_t> faceSetArray;
        // By default, we are using all the faces.
        faceSetArray.resize(nsides.size());
        for ( int i = 0; i < (int) nsides.size(); ++i )
            faceSetArray[i] = 0;

        for(int i = 0; i < faceSetNames.size(); i++)
        {
            if ( ps.hasFaceSet( faceSetNames[i] ) )
            {
                
                IFaceSet faceSet = ps.getFaceSet( faceSetNames[i] );
                IFaceSetSchema::Sample faceSetSample = faceSet.getSchema().getValue( frameSelector );

                const int* faceArray((int *)faceSetSample.getFaces()->getData()); 
                AiMsgDebug(" Faceset %s on %s with %i faces",  faceSetNames[i].c_str(), originalName.c_str(),  faceSetSample.getFaces()->size());
                for( int f = 0; f < (int) faceSetSample.getFaces()->size(); f++)
                {
                    if(faceArray[f] <= nsides.size() )
                        faceSetArray[faceArray[f]] = (uint8_t) i;
                    else
                        AiMsgWarning(" Face set is higher than nsides side");
                }
            }
        }
        AtArray *tmpArray = AiArrayConvert( faceSetArray.size(), 1, AI_TYPE_BYTE, (void *) &faceSetArray[0]);
        AiNodeSetArray( meshNode, "shidxs", tmpArray );
    }

    {
        ICompoundProperty arbGeomParams = ps.getArbGeomParams();
        ISampleSelector frameSelector( *singleSampleTimes.begin() );

        AddArbitraryGeomParams( arbGeomParams, frameSelector, meshNode );

    }

    args.createdNodes->addNode(meshNode);
    return meshNode;
}

//-*************************************************************************
// createInstance
// This function creates & returns a instance node with shaders & attributes applied.
template <typename primT>
AtNode* createInstance(const std::string& name, const std::string& originalName, primT & prim, ProcArgs & args, MatrixSampleMap * xformSamples, AtNode* mesh)
{
    AiMsgInfo("%s:ginstance", name.c_str());
    typename primT::schema_type  &ps = prim.getSchema();
    ICompoundProperty arbGeomParams = ps.getArbGeomParams();

    SampleTimeSet singleSampleTimes;
    TimeSamplingPtr ts = ps.getTimeSampling();
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    AtNode* instanceNode = AiNode("ginstance", (name + ":ginstance").c_str(), args.proceduralNode);
    if (!instanceNode)
    {
        AiMsgError(" Failed to make ginstance node for %s",
                prim.getFullName().c_str());
        return NULL;
    }

    AtNode* camera = AiUniverseGetCamera();    

    AiNodeSetBool( instanceNode, "inherit_xform", false );
    AiNodeSetFlt(instanceNode, "motion_start", AiNodeGetFlt(camera, "motion_start"));
    AiNodeSetFlt(instanceNode, "motion_end", AiNodeGetFlt(camera, "motion_end"));  
    
    if ( args.proceduralNode )
        AiNodeSetByte( instanceNode, "visibility", AiNodeGetByte( args.proceduralNode, "visibility" ) );
    else
        AiNodeSetByte( instanceNode, "visibility", AI_RAY_ALL );

    // Xform
    ApplyTransformation( instanceNode, xformSamples, args );

    // adding arbitary parameters
    AddArbitraryGeomParams(arbGeomParams, frameSelector, instanceNode );

    // adding attributes on procedural
    AddArbitraryProceduralParams(args.proceduralNode, instanceNode);

    //get tags
    std::vector<std::string> tags;
    getAllTags(ps.getObject(), tags, &args);

    // Arnold Attribute from json
    if(args.linkAttributes)
        ApplyOverrides(originalName, instanceNode, tags, args);

    // shader assignation
    if (nodeHasParameter( instanceNode, "shader" ) )
    {
        std::vector< std::string > faceSetNames;
        ps.getFaceSetNames(faceSetNames);

        // Managing faceSets.
        if ( faceSetNames.size() > 0 )
        {
            AtArray* shadersArray = AiArrayAllocate( faceSetNames.size() , 1, AI_TYPE_NODE);
            for(int i = 0; i < faceSetNames.size(); i++)
            {
                if ( ps.hasFaceSet( faceSetNames[i] ) )
                {
                    AiMsgDebug(" Faceset %s on %s",  faceSetNames[i].c_str(), originalName.c_str());
                    std::string faceSetNameForShading = originalName + "/" + faceSetNames[i];
                    AtNode* shaderForFaceSet  = getShader(faceSetNameForShading, tags, args);
                    if(shaderForFaceSet == NULL)
                    {
                        // We can't have a NULL.
                        shaderForFaceSet = AiNode("utility", faceSetNameForShading.c_str(), args.proceduralNode);
                        args.createdNodes->addNode(shaderForFaceSet);
                    }
                        AiArraySetPtr(shadersArray, i, shaderForFaceSet);
                }
            }
            AiNodeSetArray(instanceNode, "shader", shadersArray);
        }
        else
            ApplyShaders(originalName, instanceNode, tags, args);
    } else {
        AiMsgDebug(" Node type doesn't have a shader parameter");
    }

    AiNodeSetPtr( instanceNode, "node", mesh );
    args.createdNodes->addNode(instanceNode);
    return instanceNode;
}

//-*************************************************************************
// isMeshLight
template <typename primT>
bool isMeshLight(const std::string& originalName, primT & prim, ProcArgs & args)
{
    typename primT::schema_type  &ps = prim.getSchema();

    TimeSamplingPtr ts = ps.getTimeSampling();

    SampleTimeSet singleSampleTimes;
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ICompoundProperty arbGeomParams = ps.getArbGeomParams();
    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    //get tags
    std::vector<std::string> tags;
    getAllTags(ps.getObject(), tags, &args);

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

                    if (attribute=="convert_to_mesh_light")
                    {
                        Json::Value val = args.attributesRoot[*it][itr.key().asString()];
                        return val.asBool();
                    }
                }
            }
        }
    }
    return false;
}

double CalculateTriangleArea(const AtVector& p0, const AtVector& p1, const AtVector& p2)
{
   const AtVector t0(p1.x - p0.x, p1.y - p0.y, p1.z - p0.z);
   const AtVector t1(p2.x - p0.x, p2.y - p0.y, p2.z - p0.z);
   return double(AiV3Length(AiV3Cross(t0, t1)) * 0.5f);
}

//-*****************************************************************************

// parameter_name <num_elements> <num_motionblur_keys> <data_type> <elem1> <elem2> <elem3> <elem4> ...
void NormalizeRGB(AtNode* mesh, AtRGB &colorMultiplier){

    AtNode *poly = (AtNode*)AiNodeGetPtr(mesh, "node");
    double surfaceArea = 0.f;
    int counter = 0;

    for(unsigned int e=0; e < AiArrayGetNumElements(AiNodeGetArray(poly, "nsides")); e++){

        int element_nsides = AiArrayGetUInt(AiNodeGetArray(poly, "nsides"), e);

        // build a list of element vectors
        std::vector<AtVector> element_vectors;

        for (unsigned int v=0; v < element_nsides; ++v){
            int vlist_index = AiArrayGetUInt(AiNodeGetArray(poly, "vidxs"), counter);
            AtVector vec = AiArrayGetVec(AiNodeGetArray(poly, "vlist"), vlist_index);
            element_vectors.push_back(vec);
            counter += 1;
        }

        // we have all the vectors for all the sides, now we must find the triangles
        // in the element (poly)
        AtVector vector0 = element_vectors[0];

        for (int i=1; i < element_nsides - 1 ; ++i){
            AtVector vector1 = element_vectors[i];
            AtVector vector2 = element_vectors[i+1];
            surfaceArea += CalculateTriangleArea(vector0, vector1, vector2);
        }
    }
    colorMultiplier = colorMultiplier / float(surfaceArea);    
    AiMsgDebug(" Normalized RGB - r : %f, g : %f, b : %f", float(colorMultiplier.r), float(colorMultiplier.g), float(colorMultiplier.b));
}

//-*************************************************************************
// createMeshLight
template <typename primT>
void createMeshLight(const std::string& name, const std::string& originalName, primT & prim, ProcArgs & args, MatrixSampleMap * xformSamples, AtNode* mesh)
{
    AiMsgInfo("%s:meshlight", name.c_str());
    std::string meshlightname = name + ":meshlight";

    typename primT::schema_type  &ps = prim.getSchema();
    ICompoundProperty arbGeomParams = ps.getArbGeomParams();

    SampleTimeSet singleSampleTimes;
    TimeSamplingPtr ts = ps.getTimeSampling();
    singleSampleTimes.insert( ts->getFloorIndex(args.frame / args.fps, ps.getNumSamples()).second );

    ISampleSelector frameSelector( *singleSampleTimes.begin() );

    AtNode* meshLightNode = AiNode( "mesh_light", meshlightname.c_str(), args.proceduralNode );
    AiNodeSetPtr(meshLightNode, "mesh", mesh );

    //get tags
    std::vector<std::string> tags;
    getAllTags(ps.getObject(), tags, &args);

    // Arnold Attribute from json
    if(args.linkAttributes)
        ApplyOverrides(originalName, meshLightNode, tags, args);

    // adding arbitary parameters
    AddArbitraryGeomParams(arbGeomParams, frameSelector, meshLightNode );

    // adding attributes on procedural
    AddArbitraryProceduralParams(args.proceduralNode, meshLightNode);

    args.createdNodes->addNode(meshLightNode);
    createMeshLightShader(name, originalName, prim, args, xformSamples, mesh, meshLightNode);
}

//-*************************************************************************
// createMeshLightShader
template <typename primT>
void createMeshLightShader(const std::string& name, const std::string& originalName, primT & prim, ProcArgs & args, MatrixSampleMap * xformSamples, AtNode* mesh, AtNode* meshLightNode)
{
    AiMsgInfo("%s:meshlightshader", name.c_str());
    typename primT::schema_type  &ps = prim.getSchema();

    std::vector<std::string> tags;
    getAllTags(ps.getObject(), tags, &args);

    // this stuff was missing
    std::string meshlightshadername = name + ":meshlightshader";
    AtNode* meshLightShader = AiNode( "MtoaMeshLightMaterial", meshlightshadername.c_str(), args.proceduralNode);

    // see if light is visible
    bool light_visible = false;
    bool use_color_temperature = false;
    float color_temperature = 0.0;

    for(std::vector<std::string>::iterator it=args.attributes.begin(); it!=args.attributes.end(); ++it)
    {
        Json::Value overrides;
        overrides = args.attributesRoot[*it];

        for( Json::ValueIterator itr = overrides.begin() ; itr != overrides.end() ; itr++ )
        {
            std::string attribute = itr.key().asString();
            Json::Value val = args.attributesRoot[*it][itr.key().asString()];          

            if(attribute=="light_visible")
            {
                light_visible = val.asBool();
            }
            if(attribute=="use_color_temperature")
            {
                use_color_temperature = val.asBool();
            }
            if(attribute=="color_temperature")
            {
                color_temperature = val.asFloat();
            }                                          
        }
    }

    if(args.linkAttributes)
        // this pretty much only sets the color attribute
        ApplyOverrides(originalName, meshLightShader, tags, args);

    if (use_color_temperature) {
        AtRGB color = ConvertKelvinToRGB(color_temperature);
        AiNodeSetRGB(meshLightShader, "color", color.r, color.g, color.b);
    }

    if (light_visible) {
        AiNodeSetByte(mesh, "visibility", AI_RAY_ALL);

        AtRGB colorMultiplier = AI_RGB_WHITE;
        colorMultiplier = colorMultiplier * AiNodeGetFlt(meshLightNode, "intensity") * powf(2.f, AiNodeGetFlt(meshLightNode, "exposure"));

        // if normalize is set to false, we need to multiply
        // the color with the surface area
        // doing a very simple triangulation, good for
        // approximating the Arnold one
        if (AiNodeGetBool(meshLightNode, "normalize"))
         NormalizeRGB(mesh, colorMultiplier);

        AiNodeSetRGB(meshLightShader, "color_multiplier", colorMultiplier.r, colorMultiplier.g, colorMultiplier.b);
    }
    else {
        AiNodeSetByte(mesh, "visibility", AI_RAY_SPECULAR_REFLECT);
        AiNodeSetRGB(meshLightShader, "color_multiplier", 0.f, 0.f, 0.f);
    }

    // set the ptr
    AiNodeSetPtr(mesh, "shader", meshLightShader);    
    args.createdNodes->addNode(meshLightShader);
}

//-*************************************************************************
// ProcessPolyMesh
void ProcessPolyMesh( IPolyMesh &polymesh, ProcArgs &args, MatrixSampleMap * xformSamples)
{
    AiMsgInfo("");   
    if ( !polymesh.valid() )
        return;

    std::string originalName = polymesh.getFullName();
    std::string name = args.nameprefix + originalName;
    SampleTimeSet sampleTimes;
    getSampleTimes(polymesh, args, sampleTimes);

    AtNode* meshNode = writeMesh(name, originalName, polymesh, args, sampleTimes);
    if(meshNode != NULL)
    {
        AtNode *instanceNode = createInstance(name, originalName, polymesh, args, xformSamples, meshNode);
        if(instanceNode != NULL)
        {
            if(isMeshLight(originalName, polymesh, args))
            {
                createMeshLight(name, originalName, polymesh, args, xformSamples, instanceNode);    
            }  
        }
        else{
            AiNodeDestroy(instanceNode);
            AiMsgWarning("NULL GINSTANCE %s", originalName.c_str());
        }
    }
    else{
        AiNodeDestroy(meshNode);
        AiMsgWarning("NULL MESH %s", originalName.c_str());
    }
}

//-*************************************************************************
// ProcessSubD
void ProcessSubD( ISubD &subd, ProcArgs &args, MatrixSampleMap * xformSamples )
{
    AiMsgInfo("");
    if ( !subd.valid() )
        return;

    std::string originalName = subd.getFullName();
    std::string name = args.nameprefix + originalName;
    SampleTimeSet sampleTimes;
    getSampleTimes( subd, args, sampleTimes);

    AtNode* meshNode = writeMesh(name, originalName, subd, args, sampleTimes);
    if(meshNode != NULL)
    {
        AtNode *instanceNode = createInstance(name, originalName, subd, args, xformSamples, meshNode);
        if(instanceNode == NULL)
        {
            AiNodeDestroy(instanceNode);
            AiMsgWarning("NULL GINSTANCE %s", originalName.c_str());  
        }
    }
    else{
        AiNodeDestroy(meshNode);
        AiMsgWarning("NULL MESH %s", originalName.c_str());
    }
}
