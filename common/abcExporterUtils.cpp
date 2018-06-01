/*Abc Shader Exporter
Copyright (c) 2014, Gaël Honorez, All rights reserved.
This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public
License along with this library.*/

#include "abcExporterUtils.h"
#include "to_string_patch.h"

namespace // <anonymous>
{
static std::string RGB_COMPONENTS[] = {"r", "g", "b"};
static std::string RGBA_COMPONENTS[] = {"r", "g", "b", "a"};
static std::string POINT2_COMPONENTS[] = {"x", "y"};
static std::string VECTOR_COMPONENTS[] = {"x", "y", "z"};
}


const std::vector< std::string > GetComponentNames(int arnoldParamType)
{
   switch (arnoldParamType)
   {
   case AI_TYPE_RGB:
      return  std::vector<std::string> (RGB_COMPONENTS , RGB_COMPONENTS +2);
   case AI_TYPE_RGBA:
      return std::vector<std::string> (RGBA_COMPONENTS , RGBA_COMPONENTS + 3);
   case AI_TYPE_VECTOR:
      return std::vector<std::string> (VECTOR_COMPONENTS , VECTOR_COMPONENTS + 2);
   case AI_TYPE_VECTOR2:
      return std::vector<std::string> (POINT2_COMPONENTS , POINT2_COMPONENTS + 1);
   default:
      return std::vector<std::string> ();
   }
}


void getAllArnoldNodes(AtNode* node, AtNodeSet* nodes)
{
    AtParamIterator* iter = AiNodeEntryGetParamIterator(AiNodeGetNodeEntry(node));
    while (!AiParamIteratorFinished(iter))
    {
        const AtParamEntry *pentry = AiParamIteratorGetNext(iter);
        const char* paramName = AiParamGetName(pentry);


        int inputType = AiParamGetType(pentry);
        if(inputType == AI_TYPE_ARRAY)
        {
            AtArray* paramArray = AiNodeGetArray(node, paramName);
            if(AiArrayGetType(paramArray) == AI_TYPE_NODE || AiArrayGetType(paramArray) == AI_TYPE_POINTER)
            {
                for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
                {
                    AtNode* linkedNode = (AtNode*)AiArrayGetPtr(paramArray, i);
                    if(linkedNode != NULL)
                    {
                        nodes->insert(linkedNode);
                        getAllArnoldNodes(linkedNode, nodes);
                    }
                }

            }
            else
            {
                if(AiNodeIsLinked(node, paramName))
                {
                    int comp;
                    for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
                    {

                        std::string paramNameArray = std::string(paramName) + "[" + to_string(i) +"]";
						if (AiNodeIsLinked(node, paramNameArray.c_str()))
                        {
                            AtNode* linkedNode = NULL;
                            linkedNode = AiNodeGetLink(node, paramNameArray.c_str(), &comp);
                            if(linkedNode)
                            {
                                nodes->insert(linkedNode);
                                getAllArnoldNodes(linkedNode, nodes);
                            }
                            else
                            {
                                std::vector<std::string> componentNames = GetComponentNames(inputType);

                                unsigned int numComponents = componentNames.size();
                                for (unsigned int i=0; i < numComponents; i++)
                                {
                                    std::string compAttrName = paramNameArray + "." + componentNames[i];

                                    if(AiNodeIsLinked(node, compAttrName.c_str()))
                                    {
                                        linkedNode = AiNodeGetLink(node, compAttrName.c_str(), &comp);
                                        if(linkedNode)
                                        {
                                            nodes->insert(linkedNode);
                                            getAllArnoldNodes(linkedNode, nodes);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        else if(AiNodeIsLinked(node, paramName))
        {

            {
                AtNode* linkedNode = NULL;
                int comp;
                linkedNode = AiNodeGetLink(node, paramName, &comp);
                if(linkedNode)
                {
                    nodes->insert(linkedNode);
                    getAllArnoldNodes(linkedNode, nodes);
                }
                else
                {
                    std::vector<std::string> componentNames = GetComponentNames(inputType);

                    unsigned int numComponents = componentNames.size();
                    for (unsigned int i=0; i < numComponents; i++)
                    {
                        std::string compAttrName = std::string(paramName) + "." + componentNames[i];

                        if(AiNodeIsLinked(node, compAttrName.c_str()))
                        {
                            linkedNode = AiNodeGetLink(node, compAttrName.c_str(), &comp);
                            if(linkedNode)
                            {
                                nodes->insert(linkedNode);
                                getAllArnoldNodes(linkedNode, nodes);
                            }
                        }
                    }
                }
            }
        }
    }

    AiParamIteratorDestroy(iter);

}


void processArrayValues(AtNode* sit, const char *paramName, AtArray* paramArray, int outputType, Mat::OMaterial matObj, std::string nodeName)
{
    int typeArray = AiArrayGetType(paramArray);
    if (typeArray == AI_TYPE_INT ||  typeArray == AI_TYPE_ENUM)
    {
        //type int
        Abc::OInt32ArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<int> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetInt(paramArray, i));

        prop.set(vals);

    }
    else if (typeArray == AI_TYPE_UINT)
    {
        //type int
        Abc::OUInt32ArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<unsigned int> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetUInt(paramArray, i));

        prop.set(vals);

    }
    else if (typeArray == AI_TYPE_BYTE)
    {
        Alembic::AbcCoreAbstract::MetaData md;
        md.set("type", std::string("byte"));
        //type int
        Abc::OUInt32ArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName, md);
        std::vector<unsigned int> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetByte(paramArray, i));

        prop.set(vals);

    }
    else if (typeArray == AI_TYPE_FLOAT)
    {
        // type float
        Abc::OFloatArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<float> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetFlt(paramArray, i));
        prop.set(vals);

    }
    else if (typeArray == AI_TYPE_BOOLEAN)
    {
        // type bool
        Abc::OBoolArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<Abc::bool_t> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetBool(paramArray, i));

        prop.set(vals);

    }
    else if (typeArray == AI_TYPE_RGB)
    {
        // type rgb
        Abc::OC3fArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<Imath::C3f> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
        {
            AtRGB a_val = AiArrayGetRGB(paramArray, i);
            Imath::C3f color_val( a_val.r, a_val.g, a_val.b );
            vals.push_back(color_val);
        }
        prop.set(vals);
    }
    else if (typeArray == AI_TYPE_RGBA)
    {
        // type rgba
        Abc::OC4fArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<Imath::C4f> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
        {
            AtRGBA a_val = AiArrayGetRGBA(paramArray, i);
            Imath::C4f color_val( a_val.r, a_val.g, a_val.b, a_val.a );
            vals.push_back(color_val);
        }
        prop.set(vals);
    }
    else if (typeArray == AI_TYPE_VECTOR2)
    {
        // type point2
        Abc::OP2fArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<Imath::V2f> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
        {
            AtVector2 a_val = AiArrayGetVec2(paramArray, i);
            Imath::V2f vec_val( a_val.x, a_val.y );
            vals.push_back(vec_val);
        }
        prop.set(vals);
    }

    else if (typeArray == AI_TYPE_VECTOR)
    {
        Abc::OV3fArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<Imath::V3f> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
        {
            AtVector a_val = AiArrayGetVec(paramArray, i);
            Imath::V3f vec_val( a_val.x, a_val.y, a_val.z );
            vals.push_back(vec_val);
        }
        prop.set(vals);
    }
    else if (typeArray == AI_TYPE_STRING)
    {
        // type string
        Abc::OStringArrayProperty prop(matObj.getSchema().getNetworkNodeParameters(nodeName.c_str()), paramName);
        std::vector<std::string> vals;
        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
            vals.push_back(AiArrayGetStr(paramArray, i).c_str());
        prop.set(vals);
    }

   // cout << "exported " << AiArrayGetNumElements(paramArray) << " array values of type " << typeArray << " for " << nodeName.c_str() << "." << paramName << endl;
}


void processArrayParam(AtNode* sit, const char *paramName, AtArray* paramArray, int index, int outputType, Mat::OMaterial matObj, std::string nodeName, std::string containerName)
{
    //first, test if the entry is linked
    //Build the paramname...
	AiMsgTab (+2);
    int typeArray = AiArrayGetType(paramArray);

    if(typeArray == AI_TYPE_NODE || typeArray == AI_TYPE_POINTER)
    {

        for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
        {
            AtNode* linkedNode = (AtNode*)AiArrayGetPtr(paramArray, i);
            if(linkedNode != NULL)
            {
                std::string nodeNameLinked = containerName + ":" + std::string(AiNodeGetName(linkedNode));
                std::string paramNameArray = std::string(paramName) + "[" + to_string(i) +"]";
                matObj.getSchema().setNetworkNodeConnection(nodeName.c_str(), paramNameArray.c_str(), nodeNameLinked.c_str(), "");
            }
        }
    }
    else
    {
        std::string paramNameArray = std::string(paramName) + "[" + to_string(index) +"]";
        if (!AiNodeGetLink(sit, paramNameArray.c_str()) == NULL)
            processLinkedParam(sit, typeArray, outputType, matObj, nodeName, paramNameArray, containerName);
    }
	AiMsgTab (-2);
}


void processLinkedParam(AtNode* sit, int inputType, int outputType,  Mat::OMaterial matObj,  std::string nodeName, std::string paramName, std::string containerName)
{
    AiMsgTab (+2);
    if (AiNodeIsLinked(sit, paramName.c_str()))
    {
        // check what is linked exactly
        if(AiNodeGetLink(sit, paramName.c_str()))
        {
            exportLink(sit, matObj, nodeName, paramName, containerName);
        }
        else
        {
			const std::vector<std::string> componentNames = GetComponentNames(inputType);
			unsigned int numComponents = componentNames.size();

            for (unsigned int i=0; i < numComponents; i++)
            {
                std::string compAttrName = paramName + "." + componentNames[i];
                if(AiNodeIsLinked(sit, compAttrName.c_str()))
                {
                    exportLink(sit, matObj, nodeName, compAttrName, containerName);
                }
            }
        }
    }
    else
        exportParameter(sit, matObj, inputType, nodeName, paramName);

    AiMsgTab (-2);
}

void exportLink(AtNode* sit, Mat::OMaterial matObj, std::string nodeName, std::string paramName, std::string containerName)
{
    AiMsgTab (+2);
    int comp;
    AiMsgDebug(" Checking link %s.%s", nodeName.c_str(), paramName.c_str());

    AtNode* linked = AiNodeGetLink(sit, paramName.c_str(), &comp);
    int outputType = AiNodeEntryGetOutputType(AiNodeGetNodeEntry(linked));

    std::string nodeNameLinked = containerName + ":" + std::string(AiNodeGetName(linked));

    //We need to replace the "." stuff from the name as we does it from the exporter.
    nodeNameLinked = pystring::replace(nodeNameLinked, ".message", "");
    nodeNameLinked = pystring::replace(nodeNameLinked, ".", "_");

    std::string outPlug;

    if(comp == -1)
        outPlug = "";
    else
    {
        if(outputType == AI_TYPE_RGB || outputType == AI_TYPE_RGBA)
        {
            if(comp == 0)
                outPlug = "r";
            else if(comp == 1)
                outPlug = "g";
            else if(comp == 2)
                outPlug = "b";
            else if(comp == 3)
                outPlug = "a";
        }
        else if(outputType == AI_TYPE_VECTOR || outputType == AI_TYPE_VECTOR2)
        {
            if(comp == 0)
                outPlug = "x";
            else if(comp == 1)
                outPlug = "y";
            else if(comp == 2)
                outPlug = "z";
        }

    }
    matObj.getSchema().setNetworkNodeConnection(nodeName.c_str(), paramName, nodeNameLinked.c_str(), outPlug);
    AiMsgTab (-2);
}


void exportParameter(AtNode* sit, Mat::OMaterial matObj, int type, std::string nodeName, std::string paramName)
{
	const char* c_paramName = paramName.c_str();
	const char* c_nodeName = nodeName.c_str();

    if (type == AI_TYPE_INT || type == AI_TYPE_ENUM)
    {
        //type int
        Abc::OInt32Property prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        prop.set(AiNodeGetInt(sit, c_paramName));
    }
    else if (type == AI_TYPE_UINT)
    {
        //type int
        Abc::OUInt32Property prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        prop.set(AiNodeGetUInt(sit, c_paramName));
    }
    else if (type == AI_TYPE_BYTE)
    {
        Alembic::AbcCoreAbstract::MetaData md;
        md.set("type", std::string("byte"));

        //type Byte
        Abc::OUInt32Property prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName, md);
        prop.set(AiNodeGetByte(sit, c_paramName));
    }
    else if (type == AI_TYPE_FLOAT)
    {
        // type float
        Alembic::AbcCoreAbstract::MetaData md;
        const AtNodeEntry* arnoldNodeEntry = AiNodeGetNodeEntry(sit);
        float val;
        bool success = AiMetaDataGetFlt(arnoldNodeEntry, c_paramName, "min", &val);
        if(success)
            md.set("min", std::to_string(val));

        success = AiMetaDataGetFlt(arnoldNodeEntry, c_paramName, "max", &val);
        if(success)
            md.set("max", std::to_string(val));

        success = AiMetaDataGetFlt(arnoldNodeEntry, c_paramName, "softmin", &val);
        if(success)
            md.set("softmin", std::to_string(val));

        success = AiMetaDataGetFlt(arnoldNodeEntry, c_paramName, "softmax", &val);
        if(success)
            md.set("softmax", std::to_string(val));

        Abc::OFloatProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName, md);
        prop.set(AiNodeGetFlt(sit, c_paramName));
    }
    else if (type == AI_TYPE_BOOLEAN)
    {
        // type bool
        Abc::OBoolProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        prop.set(AiNodeGetBool(sit, c_paramName));
    }
    else if (type == AI_TYPE_RGB)
    {
        // type rgb
        Abc::OC3fProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        AtRGB a_val = AiNodeGetRGB(sit, c_paramName);
        Imath::C3f color_val( a_val.r, a_val.g, a_val.b );
        prop.set(color_val);
    }
    else if (type == AI_TYPE_RGBA)
    {
        // type rgb
        Abc::OC4fProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        AtRGBA a_val = AiNodeGetRGBA(sit, c_paramName);
        Imath::C4f color_val( a_val.r, a_val.g, a_val.b, a_val.a );
        prop.set(color_val);
    }
    else if (type == AI_TYPE_VECTOR2)
    {
        // type point
        Abc::OP2fProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        AtVector2 a_val = AiNodeGetVec2(sit, c_paramName);
        Imath::V2f vec_val( a_val.x, a_val.y);
        prop.set(vec_val);
    }
    else if (type == AI_TYPE_VECTOR)
    {
        // type vector
        Abc::OV3fProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        AtVector a_val = AiNodeGetVec(sit, c_paramName);
        Imath::V3f vec_val( a_val.x, a_val.y, a_val.z );
        prop.set(vec_val);
    }
    else if (type == AI_TYPE_STRING)
    {
        // type string
        Abc::OStringProperty prop(matObj.getSchema().getNetworkNodeParameters(c_nodeName), c_paramName);
        prop.set(AiNodeGetStr(sit, c_paramName).c_str());
    }

    if(strcmp(c_paramName,"name") != 0 && isDefaultValue(sit, c_paramName) == false)
        if (type == AI_TYPE_BYTE || type == AI_TYPE_INT || type == AI_TYPE_UINT || type == AI_TYPE_ENUM || type == AI_TYPE_FLOAT || type == AI_TYPE_BOOLEAN || type == AI_TYPE_RGB ||type == AI_TYPE_STRING)
        {
            std::string interfaceName = std::string(AiNodeGetName(sit)) + ":" + paramName;
            matObj.getSchema().setNetworkInterfaceParameterMapping(interfaceName.c_str(), c_nodeName, c_paramName);
        }
}


bool isDefaultValue(AtNode* node, const char* paramName)
{
    const AtParamEntry* pentry = AiNodeEntryLookUpParameter (AiNodeGetNodeEntry(node), paramName);
    if(pentry == NULL)
        return false;

    const AtParamValue * pdefaultvalue = AiParamGetDefault (pentry);

    switch(AiParamGetType(pentry))
    {
        case AI_TYPE_BYTE:
            if (AiNodeGetByte(node, paramName) == pdefaultvalue->BYTE())
                return true;
            break;
        case AI_TYPE_INT:
            if (AiNodeGetInt(node, paramName) == pdefaultvalue->INT())
                return true;
            break;
        case AI_TYPE_UINT:
            if (AiNodeGetUInt(node, paramName) == pdefaultvalue->UINT())
                return true;
            break;
        case AI_TYPE_BOOLEAN:
            if (AiNodeGetBool (node, paramName) == pdefaultvalue->BOOL())
                return true;
            break;
        case AI_TYPE_FLOAT:
            if (AiNodeGetFlt (node, paramName) == pdefaultvalue->FLT())
                return true;
            break;
        case AI_TYPE_RGB:
            if (AiNodeGetRGB (node, paramName) == pdefaultvalue->RGB())
                return true;
            break;
        case AI_TYPE_RGBA:
            if (AiNodeGetRGBA (node, paramName) == pdefaultvalue->RGBA())
                return true;
            break;
        case AI_TYPE_VECTOR:
            if (AiNodeGetVec (node, paramName) == pdefaultvalue->VEC())
                return true;
            break;
        case AI_TYPE_VECTOR2:
            if (AiNodeGetVec2 (node, paramName) == pdefaultvalue->VEC2())
                return true;
            break;
        case AI_TYPE_STRING:
            if (AiNodeGetStr(node, paramName) == pdefaultvalue->STR())
                return true;
            break;
        default:
            return false;
    }
    return false;
}
