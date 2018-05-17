#include "parseAttributes.h"
#include "abcshaderutils.h"
#include "../../common/PathUtil.h"

#include <pystring.h>

namespace
{
    using namespace Alembic::AbcGeom;
    using namespace Alembic::AbcMaterial;
}

void getTags(IObject iObj, std::vector<std::string> & tags, ProcArgs* args)
{
    //const MetaData &md = iObj.getMetaData();
	const ObjectHeader ohead = iObj.getHeader();
	if(!iObj.valid())
		return;

    ICompoundProperty arbGeomParams;

    if ( IXform::matches( ohead ) )
    {
        IXform xform( iObj, kWrapExisting );
        IXformSchema ms = xform.getSchema();
        arbGeomParams = ms.getArbGeomParams();
    }
    else if ( IPolyMesh::matches( ohead ))
    {
        IPolyMesh mesh( iObj, kWrapExisting );
        IPolyMeshSchema ms = mesh.getSchema();
        arbGeomParams = ms.getArbGeomParams();
    }
    else if ( ISubD::matches( ohead ))
    {
        ISubD mesh( iObj, kWrapExisting );
        ISubDSchema ms = mesh.getSchema();
        arbGeomParams = ms.getArbGeomParams();
    }

    else if ( IPoints::matches( ohead ) )
    {
        IPoints points( iObj, kWrapExisting );
        IPointsSchema ms = points.getSchema();
        arbGeomParams = ms.getArbGeomParams();

    }
    else if ( ICurves::matches( ohead ) )
    {
        ICurves curves( iObj, kWrapExisting );
        ICurvesSchema ms = curves.getSchema();
        arbGeomParams = ms.getArbGeomParams();
    }
    else if ( ILight::matches( ohead ) )
    {
        ILight lights( iObj, kWrapExisting );
        ILightSchema ms = lights.getSchema();
        arbGeomParams = ms.getArbGeomParams();
    }

    if ( arbGeomParams != NULL && arbGeomParams.valid() )
    {
        std::vector<std::string> tagsString;
        tagsString.push_back("mtoa_constant_tags");
        tagsString.push_back("tags");
        if(args->useShaderAssignationAttribute)
            tagsString.push_back(args->shaderAssignationAttribute);

        for (std::vector<std::string>::iterator it = tagsString.begin() ; it != tagsString.end(); ++it)
        {
            if (arbGeomParams.getPropertyHeader(*it) != NULL)
            {
                const PropertyHeader * tagsHeader = arbGeomParams.getPropertyHeader(*it);
                if (IStringGeomParam::matches( *tagsHeader ))
                {
                    IStringGeomParam param( arbGeomParams,  *it );
                    if ( param.valid() )
                    {
                        IStringGeomParam::prop_type::sample_ptr_type valueSample = param.getExpandedValue().getVals();
                        if ( param.getScope() == kConstantScope || param.getScope() == kUnknownScope)
                        {
                            Json::Value jtags;
                            Json::Reader reader;
                            if(reader.parse(valueSample->get()[0], jtags))
                            {
                                for( Json::ValueIterator itr = jtags.begin() ; itr != jtags.end() ; itr++ )
                                {
                                    std::string tag = jtags[itr.key().asUInt()].asString();
                                    tags.push_back(tag);
                                }
                            }
                            else
                                tags.push_back(valueSample->get()[0]);
                        }
                    }
                }
            }
        }
    }
}


void getAllTags(IObject iObj, std::vector<std::string> & tags, ProcArgs* args)
{
	
	getTags(iObj, tags, args);
	Alembic::Abc::IObject parent = iObj.getParent();
	if (parent.valid() && Alembic::AbcGeom::IXform::matches(parent.getMetaData())) // our parent is an xform no matter what.
		getAllTags( parent, tags, args);

}


bool isVisible(IObject child, IXformSchema xs, ProcArgs* args)
{
    if(GetVisibility( child, ISampleSelector( args->frame / args->fps ) ) == kVisibilityHidden)
    {
        // check if the object is not forced to be visible
        std::string name = args->nameprefix + child.getFullName();

        if(args->linkAttributes)
        {
            for(std::vector<std::string>::iterator it=args->attributes.begin(); it!=args->attributes.end(); ++it)
            {
                    Json::Value attributes;
                    if(it->find("/") != string::npos)
                        if(name.find(*it) != string::npos)
                            attributes = args->attributesRoot[*it];


                    if(attributes.size() > 0)
                    {
                        for( Json::ValueIterator itr = attributes.begin() ; itr != attributes.end() ; itr++ )
                        {
                            std::string attribute = itr.key().asString();
                            if (attribute == "forceVisible")
                            {

                                bool vis = args->attributesRoot[*it][itr.key().asString()].asBool();
                                if(vis)
                                    return true;
                                else
                                    return false;
                            }

                        }

                    }
            }
        }
        return false;
    }

    // Check it's a xform and that xform has a tag "DISPLAY" to skip it.
    ICompoundProperty prop = xs.getArbGeomParams();
    if ( prop != NULL && prop.valid() )
    {
        if (prop.getPropertyHeader("mtoa_constant_tags") != NULL)
        {
            const PropertyHeader * tagsHeader = prop.getPropertyHeader("mtoa_constant_tags");
            if (IStringGeomParam::matches( *tagsHeader ))
            {
                IStringGeomParam param( prop,  "mtoa_constant_tags" );
                if ( param.valid() )
                {
                    IStringGeomParam::prop_type::sample_ptr_type valueSample =
                                    param.getExpandedValue( ISampleSelector( args->frame / args->fps ) ).getVals();

                    if ( param.getScope() == kConstantScope || param.getScope() == kUnknownScope)
                    {
                        Json::Value jtags;
                        Json::Reader reader;
                        if(reader.parse(valueSample->get()[0], jtags))
                            for( Json::ValueIterator itr = jtags.begin() ; itr != jtags.end() ; itr++ )
                            {

                                if (jtags[itr.key().asUInt()].asString() == "DISPLAY" )
                                    return false;
                            }
                    }
                }
            }
        }
    }

    return true;
}


bool isVisibleForArnold(IObject child, ProcArgs* args)
{
    uint16_t minVis = AI_RAY_ALL & ~(AI_RAY_SUBSURFACE | AI_RAY_SPECULAR_REFLECT | AI_RAY_DIFFUSE_REFLECT | AI_RAY_VOLUME | AI_RAY_SPECULAR_TRANSMIT | AI_RAY_DIFFUSE_TRANSMIT |AI_RAY_SHADOW|AI_RAY_CAMERA);
    std::string name = child.getFullName();
    int pathSize = 0;
    if(args->linkAttributes)
    {
        for(std::vector<std::string>::iterator it=args->attributes.begin(); it!=args->attributes.end(); ++it)
        {
                Json::Value attributes;
                if(it->find("/") != string::npos)
                {
                    if(pathContainsOtherPath(name, *it))
					{
                        std::string overridePath = *it;
                        if(overridePath.length() > pathSize)
                        {
                            pathSize = overridePath.length();
                            attributes = args->attributesRoot[*it];
                        }
					}
                }
                else if(matchPattern(name,*it)) // based on wildcard expression
                {
                    std::string overridePath = *it;
                    if(overridePath.length() > pathSize)
                    {   
                        pathSize = overridePath.length();
                        attributes = args->attributesRoot[*it];
                    }
            
                }

                if(attributes.size() > 0)
                {
                    for( Json::ValueIterator itr = attributes.begin() ; itr != attributes.end() ; itr++ )
                    {
                        std::string attribute = itr.key().asString();
                        if (attribute == "visibility")
                        {

                            uint16_t vis = args->attributesRoot[*it][itr.key().asString()].asInt();
                            if(vis <= minVis)
                            {
                                AiMsgDebug("    [parseAttributes][isVisibleForArnold] Object %s is invisible", name.c_str());
                                return false;
                            }

                            break;
                        }

                    }
                }
        }
    }
    return true;

}


void OverrideProperties(Json::Value & jroot, Json::Value jrootAttributes)
{
    for( Json::ValueIterator itr = jrootAttributes.begin() ; itr != jrootAttributes.end() ; itr++ )
    {
        Json::Value paths = jrootAttributes[itr.key().asString()];
        for( Json::ValueIterator overPath = paths.begin() ; overPath != paths.end() ; overPath++ )
        {
            Json::Value attr = paths[overPath.key().asString()];
            jroot[itr.key().asString()][overPath.key().asString()] = attr;
        }
    }
}

Json::Value OverrideAssignations(Json::Value jroot, Json::Value jrootOverrides)
{
    std::vector<std::string> pathOverrides;

    Json::Value newJroot;
    // concatenate both json string.
    for( Json::ValueIterator itr = jrootOverrides.begin() ; itr != jrootOverrides.end() ; itr++ )
    {
        Json::Value tmp = jroot[itr.key().asString()];
        Json::Value paths = jrootOverrides[itr.key().asString()];
        for( Json::ValueIterator shaderPath = paths.begin() ; shaderPath != paths.end() ; shaderPath++ )
        {
            Json::Value val = paths[shaderPath.key().asUInt()];
            pathOverrides.push_back(val.asString());
        }
        if(tmp.size() == 0)
        {
            newJroot[itr.key().asString()] = jrootOverrides[itr.key().asString()];
        }
        else
        {
            Json::Value shaderPaths = jrootOverrides[itr.key().asString()];
            for( Json::ValueIterator itr2 = shaderPaths.begin() ; itr2 != shaderPaths.end() ; itr2++ )
            {
                newJroot[itr.key().asString()].append(jrootOverrides[itr.key().asString()][itr2.key().asUInt()]);
            }
        }
    }
    // Now adding back the original shaders without the ones overriden
    for( Json::ValueIterator itr = jroot.begin() ; itr != jroot.end() ; itr++ )
    {
        Json::Value pathsShader = jroot[itr.key().asString()];
        const Json::Value curval = newJroot[itr.key().asString()];
        for( Json::ValueIterator shaderPathOrig = pathsShader.begin() ; shaderPathOrig != pathsShader.end() ; shaderPathOrig++ )
        {
            Json::Value val = pathsShader[shaderPathOrig.key().asUInt()];
            bool isPresent = (std::find(pathOverrides.begin(), pathOverrides.end(), val.asCString())  != pathOverrides.end());
            if (!isPresent)
                newJroot[itr.key().asString()].append(val);
        }
    }


    return newJroot;
}

AtNode* createNetwork(IObject object, std::string prefix, ProcArgs & args)
{
    std::map<std::string,AtNode*> aShaders;
    Mat::IMaterial matObj(object, kWrapExisting);
    for (size_t i = 0, e = matObj.getSchema().getNumNetworkNodes(); i < e; ++i)
    {
        Mat::IMaterialSchema::NetworkNode abcnode = matObj.getSchema().getNetworkNode(i);
        std::string target = "<undefined>";
        abcnode.getTarget(target);
        if(target == "arnold")
        {
            std::string nodeType = "<undefined>";
            abcnode.getNodeType(nodeType);
            AiMsgDebug("    [parseAttributes][createNetwork] Creating %s node named %s", nodeType.c_str(), abcnode.getName().c_str());
            AtNode* aShader = AiNode (nodeType.c_str());

            std::string name = prefix + "_" + abcnode.getName();

            AiNodeSetStr (aShader, "name", name.c_str());
            aShaders[abcnode.getName()] = aShader;

            args.createdNodes->addNode(aShader);

            // We set the default attributes
            ICompoundProperty parameters = abcnode.getParameters();
            if (parameters.valid())
            {
                for (size_t i = 0, e = parameters.getNumProperties(); i < e; ++i)
                {
                    const PropertyHeader & header = parameters.getPropertyHeader(i);

                    if (header.getName() == "name")
                        continue;

                    if (header.isArray())
                        setArrayParameter(parameters, header, aShader, args.pathRemapping);

                    else
                        setParameter(parameters, header, aShader, args.pathRemapping);
                }
            }
        }
    }

    // once every node is created, we can set the connections...
    for (size_t i = 0, e = matObj.getSchema().getNumNetworkNodes(); i < e; ++i)
    {
        Mat::IMaterialSchema::NetworkNode abcnode = matObj.getSchema().getNetworkNode(i);

        std::string target = "<undefined>";
        std::string nodeType = "<undefined>";
        bool nodeArray = false;
        
        std::regex expr ("(.*)\\[([\\d]+)\\]");
        std::smatch what;
        abcnode.getTarget(target);

        std::map<std::string, std::vector<AtNode*> > nodeArrayConnections;
        std::map<std::string, std::vector<AtNode*> >::iterator nodeArrayConnectionsIterator;

        if(target == "arnold")
        {
            size_t numConnections = abcnode.getNumConnections();
            if(numConnections)
            {
                AiMsgDebug("[parseAttributes][createNetwork] Linking nodes");
                std::string inputName, connectedNodeName, connectedOutputName;
                for (size_t j = 0; j < numConnections; ++j)
                {
                    if (abcnode.getConnection(j, inputName, connectedNodeName, connectedOutputName))
                    {
                        nodeArray = false;
                        if (std::regex_search(inputName, what, expr))
                        {
                            std::string realInputName = what[1];
                            
                            int inputIndex = std::stoi(what[2]);
                            abcnode.getNodeType(nodeType);
                            const AtNodeEntry * nentry = AiNodeEntryLookUp(nodeType.c_str());
                            const AtParamEntry * pentry = AiNodeEntryLookUpParameter(nentry, realInputName.c_str());
                            if(AiParamGetType(pentry) == AI_TYPE_ARRAY)
                            {
                                AtArray* parray = AiNodeGetArray(aShaders[abcnode.getName().c_str()], realInputName.c_str());
                                
                                if(AiArrayGetType(parray) == AI_TYPE_NODE)
                                {
                                    nodeArray = true;
                                    std::vector<AtNode*> connArray;
                                    nodeArrayConnectionsIterator = nodeArrayConnections.find(realInputName);
                                    if(nodeArrayConnectionsIterator != nodeArrayConnections.end())
                                        connArray = nodeArrayConnectionsIterator->second;
                                    
                                    if(connArray.size() < inputIndex+1)
                                        connArray.resize(inputIndex+1);

                                    connArray[inputIndex] = aShaders[connectedNodeName.c_str()];
                                    nodeArrayConnections[realInputName] = connArray;

                                }
                            }
                        }

                        if(!nodeArray)
                        {
                            if(connectedOutputName.length() == 0)
                            {
                                AiMsgDebug("    [parseAttributes][createNetwork] Linking %s to %s.%s", connectedNodeName.c_str(), abcnode.getName().c_str(), inputName.c_str());
                                AiNodeLink(aShaders[connectedNodeName.c_str()], inputName.c_str(), aShaders[abcnode.getName().c_str()]);
                            }
                            else
                            {
                                AiMsgDebug("    [parseAttributes][createNetwork] Linking %s.%s to %s.%s", connectedNodeName.c_str(), connectedOutputName.c_str(), abcnode.getName().c_str(), inputName.c_str());
                                AiNodeLinkOutput(aShaders[connectedNodeName.c_str()], connectedOutputName.c_str(), aShaders[abcnode.getName().c_str()], inputName.c_str());
                            }
                        }
                    }
                }

                for (nodeArrayConnectionsIterator=nodeArrayConnections.begin(); nodeArrayConnectionsIterator!=nodeArrayConnections.end(); ++nodeArrayConnectionsIterator)
                {
                    AtArray* a = AiArray (nodeArrayConnectionsIterator->second.size(), 1, AI_TYPE_NODE);
                    for(int n = 0; n < nodeArrayConnectionsIterator->second.size(); n++)
                    {
                        AiArraySetPtr(a, n, nodeArrayConnectionsIterator->second[n]);

                    }
                    AiNodeSetArray(aShaders[abcnode.getName().c_str()], nodeArrayConnectionsIterator->first.c_str(), a);

                    nodeArrayConnectionsIterator->second.clear();
                }
                nodeArrayConnections.clear();
            }
        }
    }

    // Getting the root node now ...
    std::string connectedNodeName = "<undefined>";
    std::string connectedOutputName = "<undefined>";
    if (matObj.getSchema().getNetworkTerminal(
                "arnold", "surface", connectedNodeName, connectedOutputName))
    {
        AtNode *root = aShaders[connectedNodeName.c_str()];
        if(root)
            AiNodeSetStr(root, "name", prefix.c_str());

        return root;
    }

    return NULL;

}

void ParseShaders(Json::Value jroot, const std::string& ns, const std::string& nameprefix, ProcArgs* args, uint8_t type)
{
    // We have to lock here as we need to be sure that another thread is not checking the root while we are creating it here.
    AtScopedLock sc(args->lock);
    for( Json::ValueIterator itr = jroot.begin() ; itr != jroot.end() ; itr++ )
    {
        
        AiMsgDebug( "    [parseAttributes][ParseShaders] Parsing shader %s", itr.key().asCString());
        std::string shaderName = ns + itr.key().asString();
        AtNode* shaderNode = AiNodeLookUpByName(shaderName.c_str());
        if(shaderNode == NULL)
        {
            if(args->useAbcShaders)
            {
                std::string originalName = itr.key().asString();
                // we must get rid of .message if it's there
                if(pystring::endswith(originalName, ".message"))
                {
                    originalName = pystring::replace(originalName, ".message", "");
                }

                AiMsgDebug( "    [parseAttributes][ParseShaders] Create shader %s from ABC", originalName.c_str());

                IObject object = args->materialsObject.getChild(originalName);
                if (IMaterial::matches(object.getHeader()))
                    shaderNode = createNetwork(object, shaderName, *args);

            }
            if(shaderNode == NULL)
            {
                // search without custom namespace
                shaderName = itr.key().asString();
                shaderNode = AiNodeLookUpByName(shaderName.c_str());
                if(shaderNode == NULL)
                {
                    AiMsgDebug( "    [parseAttributes][ParseShaders] Searching shader %s deeper underground...", itr.key().asCString());
                    // look for the same namespace for shaders...
                    std::vector<std::string> strs;
                    pystring::split(nameprefix, strs, ":");
                    if(strs.size() > 1)
                    {
                        strs.pop_back();
                        strs.push_back(itr.key().asString());
                        shaderNode = AiNodeLookUpByName(pystring::join(":", strs).c_str());
                    }
                }
            }
        }
        if(shaderNode != NULL)
        {
            Json::Value paths = jroot[itr.key().asString()];
            AiMsgDebug("    [parseAttributes][ParseShaders] Shader exists, checking paths. size = %d", paths.size());
            for( Json::ValueIterator itr2 = paths.begin() ; itr2 != paths.end() ; itr2++ )
            {
                Json::Value val = paths[itr2.key().asUInt()];
                AiMsgDebug("    [parseAttributes][ParseShaders] Adding path %s", val.asCString());
                if(type == 0)
                    args->displacements[val.asString().c_str()] = shaderNode;
                else if(type == 1)
                    args->shaders.push_back(std::pair<std::string, AtNode*>(val.asString().c_str(), shaderNode));

            }
        }
        else
        {
            AiMsgWarning("    [parseAttributes][ParseShaders] Can't find shader %s", shaderName.c_str());
        }
    }
}
