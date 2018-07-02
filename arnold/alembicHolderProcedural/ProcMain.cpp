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

#include <cstring>
#include <memory>
#include <vector>

#include "ProcArgs.h"
#include "../../common/PathUtil.h"
#include "SampleUtil.h"
#include "WriteGeo.h"
#include "WritePoint.h"
#include "WriteLight.h"
#include "WriteCurves.h"
#include "json/json.h"
#include "parseAttributes.h"
#include "NodeCache.h"

#include <Alembic/AbcGeom/All.h>

#include <Alembic/AbcCoreFactory/IFactory.h>
#include <Alembic/AbcCoreOgawa/ReadWrite.h>
#include <Alembic/AbcGeom/Visibility.h>

#include <iostream>
#include <fstream>

AI_PROCEDURAL_NODE_EXPORT_METHODS(alembicProceduralMethods);

node_parameters
{
    AiParameterArray("fileNames", AiArrayAllocate(0, 1, AI_TYPE_STRING));
    AiParameterStr("objectPath", "/");
    AiParameterStr("namePrefix", "");
    AiParameterFlt("frame", 0.0);
    AiParameterFlt("fps", 25.0);
    AiParameterStr("jsonFile", "");
    AiParameterStr("secondaryJsonFile", "");
    AiParameterStr("shadersNamespace", "");
    AiParameterStr("geometryNamespace", "");    
    AiParameterStr("shadersAttribute", "");
    AiParameterStr("abcShaders", "");
    AiParameterStr("shadersAssignation", "");
    AiParameterStr("attributes", "");
    AiParameterStr("displacementsAssignation", "");
    AiParameterStr("layersOverride", "");
    AiParameterBool("skipJsonFile", false);
    AiParameterBool("skipShaders", false);
    AiParameterBool("skipAttributes", false);
    AiParameterBool("skipLayers", false);
    AiParameterBool("skipDisplacements", false);
}

// Recursively copy the values of b into a.
void update(Json::Value& a, Json::Value& b) {
    Json::Value::Members memberNames = b.getMemberNames();
    for (Json::Value::Members::const_iterator it = memberNames.begin();
            it != memberNames.end(); ++it)
    {
        const std::string& key = *it;
        if (a[key].isObject()) {
            update(a[key], b[key]);
        } else {
            a[key] = b[key];
        }
    }
}

void WalkObject( IObject & parent, const ObjectHeader &i_ohead, ProcArgs &args,
             PathList::const_iterator I, PathList::const_iterator E,
                    MatrixSampleMap * xformSamples)
{
    IObject nextParentObject;
	
    std::auto_ptr<MatrixSampleMap> concatenatedXformSamples;

    // Check for instances
    const ObjectHeader ohead = parent.isChildInstance(i_ohead.getName()) ? parent.getChild(i_ohead.getName()).getHeader() : i_ohead;

    if ( IXform::matches( ohead ) )
    {
        IXform xform( parent, ohead.getName() );
        IXformSchema &xs = xform.getSchema();

        IObject child = IObject( parent, ohead.getName() );

        // also check visibility flags

        if (isVisible(child, xs, &args) == false)
        {
		}
        else
        {
            if ( xs.getNumOps() > 0 )
            {
                TimeSamplingPtr ts = xs.getTimeSampling();
                size_t numSamples = xs.getNumSamples();
                bool inherits = xs.getInheritsXforms();

                SampleTimeSet sampleTimes;
                GetRelevantSampleTimes( args, ts, numSamples, sampleTimes,
                        xformSamples);
                MatrixSampleMap localXformSamples;

                MatrixSampleMap * localXformSamplesToFill = 0;

                concatenatedXformSamples.reset(new MatrixSampleMap);

                if ( !xformSamples )
                {
                    // If we don't have parent xform samples, we can fill
                    // in the map directly.
                    localXformSamplesToFill = concatenatedXformSamples.get();
                }
                else
                {
                    //otherwise we need to fill in a temporary map
                    localXformSamplesToFill = &localXformSamples;
                }


                for (SampleTimeSet::iterator I = sampleTimes.begin();
                        I != sampleTimes.end(); ++I)
                {
                    XformSample sample = xform.getSchema().getValue(
                            Abc::ISampleSelector(*I));
                    (*localXformSamplesToFill)[(*I)] = sample.getMatrix();
                }
                if ( xformSamples )
                {
                    if (inherits){
                        ConcatenateXformSamples(args, 
                                *xformSamples,
                                localXformSamples,
                                *concatenatedXformSamples.get());
                    }
                }


                xformSamples = concatenatedXformSamples.get();
            }

            nextParentObject = xform;
        }
    }
    else if ( ISubD::matches( ohead ) )
    {
        ISubD subd( parent, ohead.getName() );
        ProcessSubD( subd, args, xformSamples );

        nextParentObject = subd;

    }
    else if ( IPolyMesh::matches( ohead ) )
    {
        IPolyMesh polymesh( parent, ohead.getName() );
        
        if(isVisibleForArnold(parent, &args)) // check if the object is invisible for arnold. It is there to avoid skipping the whole hierarchy.
            ProcessPolyMesh( polymesh, args, xformSamples);

        nextParentObject = polymesh; 
    }
    else if ( INuPatch::matches( ohead ) )
    {
        INuPatch patch( parent, ohead.getName() );
        // TODO ProcessNuPatch( patch, args );

        nextParentObject = patch;
    }
    else if ( IPoints::matches( ohead ) )
    {
        IPoints points( parent, ohead.getName() );

        if(isVisibleForArnold(parent, &args))
            ProcessPoint( points, args, xformSamples );

        nextParentObject = points;
    }
    else if ( ICurves::matches( ohead ) )
    {
        ICurves curves( parent, ohead.getName() );

        if(isVisibleForArnold(parent, &args))
            ProcessCurves( curves, args, xformSamples );

        nextParentObject = curves;
    }
    else if ( ICamera::matches( ohead ) )
    {
        ICamera camera( parent, ohead.getName() );

        nextParentObject = camera;
    }
    else if ( ILight::matches( ohead ) )
    {
        ILight light( parent, ohead.getName() );
        
        if(isVisibleForArnold(parent, &args)) // check if the object is invisible for arnold. It is there to avoid skipping the whole hierarchy.
            ProcessLight( light, args, xformSamples);

        nextParentObject = light;
    }
    else if ( IFaceSet::matches( ohead ) )
    {
        //don't complain about discovering a faceset upon traversal
    }
    else
    {

        AiMsgError(" Could not determine type of %s", ohead.getName().c_str());
        AiMsgError(" %s has MetaData: %s", ohead.getName().c_str(), ohead.getMetaData().serialize().c_str());
    }

    if ( nextParentObject.valid() )
    {
        if ( I == E )
        {
            for ( size_t i = 0; i < nextParentObject.getNumChildren() ; ++i )
            {
                
                WalkObject( nextParentObject,
                            nextParentObject.getChildHeader( i ),
                            args, I, E, xformSamples);
            }
        }
        else
        {
            const ObjectHeader *nextChildHeader =
                nextParentObject.getChildHeader( *I );
            
            if ( nextChildHeader != NULL )
            {
                WalkObject( nextParentObject, *nextChildHeader, args, I+1, E,
                    xformSamples);
            }
        }
    }
}

struct caches
{
    FileCache* g_fileCache;
    NodeCache* g_nodeCache;
    AtCritSec mycs;

};

node_plugin_initialize
{
    #ifdef WIN32
        // DIRTY FIX
        // magic static* used in the Alembic Schemas are not threadSafe in Visual Studio, so we need to initialized them first.
        IPolyMesh::getSchemaTitle();
        IPoints::getSchemaTitle();
        ICurves::getSchemaTitle();
        INuPatch::getSchemaTitle();
        IXform::getSchemaTitle();
        ISubD::getSchemaTitle();
    #endif


    caches *g_caches = new caches();
    AiCritSecInitRecursive(&g_caches->mycs);
    g_caches->g_fileCache = new FileCache(g_caches->mycs);
    g_caches->g_nodeCache = new NodeCache(g_caches->mycs);
    *plugin_data = g_caches;
    return true;
}

node_plugin_cleanup
{
    caches *g_caches = reinterpret_cast<caches*>(plugin_data);
    AiCritSecClose(&g_caches->mycs);
    delete g_caches->g_fileCache;
    delete g_caches->g_nodeCache;
    delete g_caches;
}

procedural_init
{
    bool skipJson = false;
    bool skipShaders = false;
    bool skipAttributes = false;
    bool skipDisplacement = false;
    bool skipLayers = false;

    bool customLayer = false;
    std::string layer = "";

    AtNode* options = AiUniverseGetOptions ();
    if (AiNodeLookUpUserParameter(options, "render_layer") != NULL )
    {
        layer = std::string(AiNodeGetStr(options, "render_layer"));
        if(layer != std::string("defaultRenderLayer"))
            customLayer = true;
    }

    skipJson = AiNodeGetBool(node, "skipJsonFile");
    skipShaders = AiNodeGetBool(node, "skipShaders");
    skipAttributes = AiNodeGetBool(node, "skipAttributes");
    skipDisplacement = AiNodeGetBool(node, "skipDisplacements");
    skipLayers = AiNodeGetBool(node, "skipLayers");

    ProcArgs * args = new ProcArgs(node);
    *user_ptr = args;

    caches *g_cache = reinterpret_cast<caches*>(AiNodeGetPluginData(node));
    
    args->proceduralNode = node;
    args->nodeCache = g_cache->g_nodeCache;
    args->lock = g_cache->mycs;
    args->createdNodes = new NodeCollector(args->lock, node);

    AtString abcfile = AiNodeGetStr(node, "abcShaders");
    if(abcfile.empty() == false)
    {
        Alembic::AbcCoreFactory::IFactory factory;
        IArchive archive = factory.getArchive(abcfile.c_str());
        if (!archive.valid())
        {
            AiMsgWarning(" Invalid alembic shaders file : %s", abcfile);
        }
        else
    {
  
            AiMsgDebug(" Loading alembic shaders file : %s", abcfile);
            Abc::IObject materialsObject(archive.getTop(), "materials");
            args->useAbcShaders = true;
            args->materialsObject = materialsObject;
            args->abcShaderFile = abcfile;
        }
    }

    // PARSING JSON DATA
    //-*****************************************************************************
    Json::Value jrootShaders;
    Json::Value jrootAttributes;
    Json::Value jrootDisplacements;
    Json::Value jrootLayers;

    AtString jsonFile = AiNodeGetStr(node, "jsonFile");
    AtString secondaryJsonFile = AiNodeGetStr(node, "secondaryJsonFile");
    AtString shadersNamespace = AiNodeGetStr(node, "shadersNamespace");
    AtString geometryNamespace = AiNodeGetStr(node, "geometryNamespace");    
    AtString shadersAttribute = AiNodeGetStr(node, "shadersAttribute");
    AtString shadersAssignation = AiNodeGetStr(node, "shadersAssignation");
    AtString attributes = AiNodeGetStr(node, "attributes");
    AtString displacementsAssignation = AiNodeGetStr(node, "displacementsAssignation");
    AtString layersOverride = AiNodeGetStr(node, "layersOverride");

    bool parsingSuccessful = false;

	args->useShaderAssignationAttribute = false;

    if (jsonFile.empty() == false && skipJson == false)
    {
        Json::Value jroot;
        Json::Reader reader;
        std::ifstream test(jsonFile.c_str(), std::ifstream::binary);
        parsingSuccessful = reader.parse( test, jroot, false );

        if (secondaryJsonFile.empty() == false)
        {
            std::ifstream test2(secondaryJsonFile.c_str(), std::ifstream::binary);
            Json::Value jroot2;
            if (reader.parse( test2, jroot2, false ))
                update(jroot, jroot2);
        }
        
        if ( parsingSuccessful )
        {
            if(skipShaders == false)
            {
                if(jroot["namespace"].isString())
                    args->ns = jroot["namespace"].asString() + ":";

				if(jroot["shadersAttribute"].isString())
				{
					args->shaderAssignationAttribute = jroot["shadersAttribute"].asString();
					args->useShaderAssignationAttribute = true;
				}

                jrootShaders = jroot["shaders"];
                if (shadersAssignation.empty() == false)
                {
                    Json::Reader readerOverride;
                    Json::Value jrootShadersOverrides;
                    std::vector<std::string> pathOverrides;
                    if(readerOverride.parse( shadersAssignation.c_str(), jrootShadersOverrides ))
                        if(jrootShadersOverrides.size() > 0)
                            jrootShaders = OverrideAssignations(jrootShaders, jrootShadersOverrides);
                }
            }

            if(skipAttributes == false)
            {
                jrootAttributes = jroot["attributes"];

                if (attributes.empty() == false)
                {
                    Json::Reader readerOverride;
                    Json::Value jrootAttributesOverrides;

                    if(readerOverride.parse( attributes.c_str(), jrootAttributesOverrides))
                        OverrideProperties(jrootAttributes, jrootAttributesOverrides);
                }
            }

            if(skipDisplacement == false)
            {
                jrootDisplacements = jroot["displacement"];
                if (displacementsAssignation.empty() == false)
                {
                    Json::Reader readerOverride;
                    Json::Value jrootDisplacementsOverrides;

                    if(readerOverride.parse( displacementsAssignation.c_str(), jrootDisplacementsOverrides ))
                        if(jrootDisplacementsOverrides.size() > 0)
                            jrootDisplacements = OverrideAssignations(jrootDisplacements, jrootDisplacementsOverrides);
                }
            }

            if(skipLayers == false && customLayer)
            {
                jrootLayers = jroot["layers"];
                if (layersOverride.empty() == false)
                {
                    Json::Reader readerOverride;
                    Json::Value jrootLayersOverrides;

                    if(readerOverride.parse( layersOverride.c_str(), jrootLayersOverrides ))
                    {
                        jrootLayers[layer]["removeShaders"] = jrootLayersOverrides[layer].get("removeShaders", skipShaders).asBool();
                        jrootLayers[layer]["removeDisplacements"] = jrootLayersOverrides[layer].get("removeDisplacements", skipDisplacement).asBool();
                        jrootLayers[layer]["removeProperties"] = jrootLayersOverrides[layer].get("removeProperties", skipAttributes).asBool();

                        if(jrootLayersOverrides[layer]["shaders"].size() > 0)
                            jrootLayers[layer]["shaders"] = OverrideAssignations(jrootLayers[layer]["shaders"], jrootLayersOverrides[layer]["shaders"]);

                        if(jrootLayersOverrides[layer]["displacements"].size() > 0)
                            jrootLayers[layer]["displacements"] = OverrideAssignations(jrootLayers[layer]["displacements"], jrootLayersOverrides[layer]["displacements"]);

                        if(jrootLayersOverrides[layer]["properties"].size() > 0)
                            OverrideProperties(jrootLayers[layer]["properties"], jrootLayersOverrides[layer]["properties"]);
                    }
                }
            }
        }
    }

    if(!parsingSuccessful)
    {
        if (customLayer && layersOverride.empty() == false)
        {
            Json::Reader reader;
            parsingSuccessful = reader.parse( layersOverride.c_str(), jrootLayers );
        }
        // Check if we have to skip something....
        if( jrootLayers[layer].size() > 0 && customLayer && parsingSuccessful)
        {
            skipShaders = jrootLayers[layer].get("removeShaders", skipShaders).asBool();
            skipDisplacement = jrootLayers[layer].get("removeDisplacements", skipDisplacement).asBool();
            skipAttributes =jrootLayers[layer].get("removeProperties", skipAttributes).asBool();
        }

        if (shadersAssignation.empty() == false && skipShaders == false)
        {
            Json::Reader reader;
            bool parsingSuccessful = reader.parse( shadersAssignation.c_str(), jrootShaders );
        }

        if (attributes.empty() == false && skipAttributes == false)
        {
            Json::Reader reader;
            bool parsingSuccessful = reader.parse( attributes.c_str(), jrootAttributes );
        }
        if (displacementsAssignation.empty() == false && skipDisplacement == false)
        {
            Json::Reader reader;
            bool parsingSuccessful = reader.parse( displacementsAssignation.c_str(), jrootDisplacements );
        }
    }

    if( jrootLayers[layer].size() > 0 && customLayer)
    {
        if(jrootLayers[layer]["shaders"].size() > 0)
        {
            if(jrootLayers[layer].get("removeShaders", skipShaders).asBool())
                jrootShaders = jrootLayers[layer]["shaders"];
            else
                jrootShaders = OverrideAssignations(jrootShaders, jrootLayers[layer]["shaders"]);
        }

        if(jrootLayers[layer]["displacements"].size() > 0)
        {
            if(jrootLayers[layer].get("removeDisplacements", skipDisplacement).asBool())
                jrootDisplacements = jrootLayers[layer]["displacements"];
            else
                jrootDisplacements = OverrideAssignations(jrootDisplacements, jrootLayers[layer]["displacements"]);
        }

        if(jrootLayers[layer]["properties"].size() > 0)
        {
            if(jrootLayers[layer].get("removeProperties", skipAttributes).asBool())
                jrootAttributes = jrootLayers[layer]["properties"];
            else
                OverrideProperties(jrootAttributes, jrootLayers[layer]["properties"]);
        }
    }

    // If shaderNamespace attribute is set it has priority
    if (shadersNamespace.empty() == false)
    {
        args->ns = std::string(shadersNamespace.c_str()) + ":";
    }

    if (geometryNamespace.empty() == false)
    {
        args->gns = std::string(geometryNamespace.c_str()) + ":";
    }    

    // If shaderAttributes attribute is set it has priority
    if (shadersAttribute.empty() == false)
    {
        args->useShaderAssignationAttribute = true;
        args->shaderAssignationAttribute = std::string(shadersAttribute.c_str());
    }

    //Check displacements
    if( jrootDisplacements.size() > 0 )
    {
        args->linkDisplacement = true;
        ParseShaders(jrootDisplacements, args->ns, args->nameprefix, args, 0);
    }

    // Check if we can link shaders or not.
    if( jrootShaders.size() > 0 )
    {
        args->linkShader = true;
        ParseShaders(jrootShaders, args->ns, args->nameprefix, args, 1);
    }

    if( jrootAttributes.size() > 0 )
    {
        args->linkAttributes = true;
        args->attributesRoot = jrootAttributes;
        for( Json::ValueIterator itr = jrootAttributes.begin() ; itr != jrootAttributes.end() ; itr++ )
        {
            std::string path = itr.key().asString();
            args->attributes.push_back(path);
        }
        std::sort(args->attributes.begin(), args->attributes.end());
    }

    // WE NEED TO WALK THE ALEMBIC AND CREATE THE ARNOLD NODES
    //-*****************************************************************************
    Alembic::AbcCoreFactory::IFactory factory;

    // TODO - expose this value to user? what is the sweet spot?
    factory.setOgawaNumStreams(8);
    IArchive archive = factory.getArchive(args->filenames);
    
    if (!archive.valid())
    {
        for(size_t i = 0; i < args->filenames.size(); i++)
            AiMsgError(" Invalid alembic file : %s", args->filenames[i].c_str());
        return 0;
    }
    else
    {
        for (size_t i = 0; i < args->filenames.size(); i++){
            AiMsgInfo("Alembic Node : %s >> %s", AiNodeGetName(node), args->filenames[i].c_str());
        }
    }

    IObject root = archive.getTop();
    PathList path;
    TokenizePath( args->objectpath, "/", path );

    //try
    {
        if ( path.empty() ) //walk the entire scene
        {
            for ( size_t i = 0; i < root.getNumChildren(); ++i )
            {
                WalkObject( root, root.getChildHeader(i), *args,
                            path.end(), path.end(), 0 );
            }
        }
        else //walk to a location + its children
        {
            PathList::const_iterator I = path.begin();

            const ObjectHeader *nextChildHeader =
                    root.getChildHeader( *I );
            if ( nextChildHeader != NULL )
            {
                WalkObject( root, *nextChildHeader, *args, I+1,
                        path.end(), 0);
            }
        }
    }
    return 1;
}

//-*************************************************************************

procedural_cleanup
{
    ProcArgs * args = reinterpret_cast<ProcArgs*>( user_ptr );
    if(args != NULL)
    {

        if(args->createdNodes->getNumNodes() > 0)
        {
            caches *g_cache = reinterpret_cast<caches*>(AiNodeGetPluginData(args->proceduralNode));
            std::string fileCacheId = g_cache->g_fileCache->getHash(args->filenames, args->shaders, args->displacements, args->attributesRoot, args->frame);
            g_cache->g_fileCache->addCache(fileCacheId, args->createdNodes);
        }

        args->shaders.clear();
        args->displacements.clear();
        args->attributes.clear();
        delete args->createdNodes;
        delete args;
    }
    return 1;
}

//-*************************************************************************

procedural_num_nodes
{
    ProcArgs * args = reinterpret_cast<ProcArgs*>( user_ptr );
    return args->createdNodes->getNumNodes();
}

//-*************************************************************************

procedural_get_node
{
    ProcArgs * args = reinterpret_cast<ProcArgs*>( user_ptr );
    return args->createdNodes->getNode(i);
}

  // DSO hook
#ifdef __cplusplus
extern "C"
{
#endif

    node_loader
    {
        if (i>0) return 0;
            node->methods = alembicProceduralMethods;
            node->output_type = AI_TYPE_NONE;
            node->name = "alembicHolderProcedural";
            node->node_type = AI_NODE_SHAPE_PROCEDURAL;
            strcpy(node->version, AI_VERSION);
            return true;
    }

#ifdef __cplusplus
}
#endif



