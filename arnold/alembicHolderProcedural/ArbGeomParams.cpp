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


#include "ArbGeomParams.h"
#include <sstream>


#define   AI_TYPE_DOUBLE   0x10

std::string CleanAttributeName(std::string str)
{
    pystring::replace(str, "mtoa_constant_", "");
    return str;
}



std::string GetArnoldTypeString( GeometryScope scope, int arnoldAPIType, AtNode *primNode, bool indexed)
{
    std::ostringstream buffer;
    switch (scope)
    {

    case kUniformScope:
        buffer << "uniform";
        break;
    case kVaryingScope:
        if(AiNodeIs(primNode, AtString("points")))
            buffer << "uniform";
        else
            buffer << "varying";
        break;
    case kVertexScope:
        buffer << "varying";
        break;
    case kFacevaryingScope:
		if (indexed)
			buffer << "indexed";
		else
			buffer << "varying";
        break;
    case kConstantScope:
		if(AiNodeIs(primNode, AtString("points")))
		{
			buffer << "uniform";
			break;
		}
		
    default:
        buffer << "constant";
    }

    buffer << " ";

    switch ( arnoldAPIType )
    {
        case AI_TYPE_BOOLEAN:
            buffer << "BOOL";
            break;
        case AI_TYPE_INT:
            buffer << "INT";
            break;
        case AI_TYPE_FLOAT:
            buffer << "FLOAT";
            break;
        case AI_TYPE_DOUBLE:
            buffer << "FLOAT";
            break;
        case AI_TYPE_STRING:
            buffer << "STRING";
            break;
        case AI_TYPE_RGB:
            buffer << "RGB";
            break;
        case AI_TYPE_RGBA:
            buffer << "RGBA";
            break;
        case AI_TYPE_VECTOR:
            buffer << "VECTOR";
            break;
        case AI_TYPE_VECTOR2:
            buffer << "VECTOR2";
            break;
        case AI_TYPE_MATRIX:
            buffer << "MATRIX";
            break;
        default:
            // For now, only support the above types
            return "";
    }


    return buffer.str();
}

template <typename T>
void SetArrayByArnoldType(AtArray* array, int idx, int arnoldAPIType, typename T::prop_type::sample_ptr_type valueSample, int idxSample)
{
	switch ( arnoldAPIType )
	{
		case AI_TYPE_INT:
			AiArraySetInt( array, idx,
					reinterpret_cast<const Alembic::Util::int32_t *>(
							valueSample->get() )[idxSample] );

			break;
		case AI_TYPE_DOUBLE:
			AiArraySetFlt( array, idx,
					reinterpret_cast<const float64_t *>(
							valueSample->get() )[idxSample] );
			break;

		case AI_TYPE_FLOAT:
			AiArraySetFlt( array, idx,
					reinterpret_cast<const float32_t *>(
							valueSample->get() )[idxSample] );
			break;
		case AI_TYPE_STRING:

			AiArraySetStr( array, idx,
					reinterpret_cast<const std::string *>(
							valueSample->get() )[idxSample].c_str() );

			break;
		case AI_TYPE_RGB:
		{
			const float32_t * data =
					reinterpret_cast<const float32_t *>(
							valueSample->get() );

			AiArraySetRGB( array, idx,
					AtRGB(data[idxSample*3], data[idxSample*3+1], data[idxSample*3+2]) );

			break;
		}
		case AI_TYPE_RGBA:
		{
			const float32_t * data =
					reinterpret_cast<const float32_t *>(
							valueSample->get() );
			AiArraySetRGBA( array, idx,
					AtRGBA(data[idxSample*3], data[idxSample*3+1], data[idxSample*3+2],  data[idxSample*3+3]));

			break;
		}
		case AI_TYPE_VECTOR:
		{
			const float32_t * data =
					reinterpret_cast<const float32_t *>(
							valueSample->get() );

			

			AiArraySetVec( array, idx,
					 AtVector(data[idxSample*3], data[idxSample*3+1], data[idxSample*3+2]));

			break;
		}
		case AI_TYPE_VECTOR2:
		{
			const float32_t * data =
					reinterpret_cast<const float32_t *>(
							valueSample->get() );

			AiArraySetVec2( array, idx,
					AtVector2(data[idxSample*3], data[idxSample*3+1]) );
			break;
		}
		case AI_TYPE_MATRIX:
		{
			const float32_t * data =
					reinterpret_cast<const float32_t *>(
							valueSample->get() );

			AtMatrix m;
			for ( size_t i = 0; i < 16; ++i )
			{
				*((&m[0][0])+i) = data[idxSample*16+i];
			}
			AiArraySetMtx( array, idx, m);


			break;
		}
		default:
			// For now, only support the above types
			break;
	}

}

//-*****************************************************************************

template <typename T>
void AddArbitraryGeomParam( ICompoundProperty & parent,
                            const PropertyHeader &propHeader,
                            ISampleSelector &sampleSelector,
                            AtNode * primNode,
                            int arnoldAPIType)
{

    T param( parent, propHeader.getName() );

    if ( !param.valid() )
    {
        //TODO error message?
        return;
    }

    std::string declStr = GetArnoldTypeString( param.getScope(),
            arnoldAPIType, primNode, param.isIndexed() );



    if ( declStr.empty() )
    {
        return;
    }

    // TODO For now, don't support user-defined arrays.
    // It's reasonable to support these for kConstantScope
    if ( param.getArrayExtent() > 1 )
    {
        return;
    }

    // Varying and faceVarying attributes are not supported on instance!
    if((param.getScope() == kVaryingScope || param.getScope() == kFacevaryingScope ) && AiNodeIs(primNode, AtString("ginstance")))
        return;

    // Check if that attribute is not existing already as a standard attribute.

    std::string cleanAttributeName = CleanAttributeName(param.getName());
    bool paramExists = false;

    const AtNodeEntry *nentry = AiNodeGetNodeEntry(primNode);
    AtParamIterator *iter = AiNodeEntryGetParamIterator(nentry);
    while (!AiParamIteratorFinished(iter))
    {
        const AtParamEntry *pentry = AiParamIteratorGetNext(iter);
        
        if (strcmp(cleanAttributeName.c_str(), AiParamGetName(pentry)) == 0)
        {
            paramExists = true;
            break;
        }

        
    }
    AiParamIteratorDestroy(iter);

	if ( AiNodeIs(primNode, AtString("points")))
	{
        typename T::prop_type::sample_ptr_type valueSample =
                param.getExpandedValue( sampleSelector ).getVals();

		if(valueSample->size() == 0)
			return;

	    if(!paramExists)
			if ( !AiNodeDeclare( primNode, cleanAttributeName.c_str(), declStr.c_str() ) )
			{
				//TODO, AiWarning
				return;
			}

            AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(),
                    AiArrayConvert( valueSample->size(), 1, arnoldAPIType,
                            (void *) valueSample->get() ) );

	}

    else if ( (param.getScope() == kConstantScope ||
            param.getScope() == kUnknownScope) 

			)
    {

        //Set scalars directly based on arnoldAPIType since we're
        //not yet support array types here

        typename T::prop_type::sample_ptr_type valueSample =
                param.getExpandedValue( sampleSelector ).getVals();

		if(valueSample->size() == 0)
			return;

	    if(!paramExists)
			if ( !AiNodeDeclare( primNode, cleanAttributeName.c_str(), declStr.c_str() ) )
			{
				//TODO, AiWarning
				return;
			}

        switch ( arnoldAPIType )
        {
            case AI_TYPE_INT:
                AiNodeSetInt( primNode, CleanAttributeName(param.getName()).c_str(),
                        reinterpret_cast<const Alembic::Util::int32_t *>(
                                valueSample->get() )[0] );

                break;
            case AI_TYPE_DOUBLE:
                AiNodeSetFlt( primNode, CleanAttributeName(param.getName()).c_str(),
                        reinterpret_cast<const float64_t *>(
                                valueSample->get() )[0] );
                break;

            case AI_TYPE_FLOAT:
                AiNodeSetFlt( primNode, CleanAttributeName(param.getName()).c_str(),
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() )[0] );
                break;
            case AI_TYPE_STRING:

                AiNodeSetStr( primNode, CleanAttributeName(param.getName()).c_str(),
                        reinterpret_cast<const std::string *>(
                                valueSample->get() )[0].c_str() );

                break;
            case AI_TYPE_RGB:
            {
                const float32_t * data =
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() );

                AiNodeSetRGB( primNode, CleanAttributeName(param.getName()).c_str(),
                        data[0], data[1], data[2]);

                break;
            }
            case AI_TYPE_RGBA:
            {
                const float32_t * data =
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() );
                AiNodeSetRGBA( primNode, CleanAttributeName(param.getName()).c_str(),
                        data[0], data[1], data[2], data[3]);

                break;
            }
            case AI_TYPE_VECTOR:
            {
                const float32_t * data =
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() );

                AiNodeSetVec( primNode, CleanAttributeName(param.getName()).c_str(),
                        data[0], data[1], data[2]);

                break;
            }
            case AI_TYPE_VECTOR2:
            {
                const float32_t * data =
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() );

                AiNodeSetVec2( primNode, CleanAttributeName(param.getName()).c_str(),
                        data[0], data[1] );
                break;
            }
            case AI_TYPE_MATRIX:
            {
                const float32_t * data =
                        reinterpret_cast<const float32_t *>(
                                valueSample->get() );

                AtMatrix m;
                for ( size_t i = 0; i < 16; ++i )
                {
                    *((&m[0][0])+i) = data[i];
                }
                AiNodeSetMatrix( primNode, CleanAttributeName(param.getName()).c_str(), m);


                break;
            }
            default:
                // For now, only support the above types
                break;
        }
    }
    else
    {
        // Always set arrays for other scopes

        if ( param.getScope() == kFacevaryingScope)
        {
            if (param.isIndexed ())
            {
                // if we are not indexed, arnold can't do it.
                typename T::prop_type::sample_ptr_type valueSample =
                        param.getIndexedValue( sampleSelector ).getVals();

				if(!paramExists)
					if ( !AiNodeDeclare( primNode, cleanAttributeName.c_str(), declStr.c_str() ) )
					{
						//TODO, AiWarning
						return;
					}

                AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(),
                    AiArrayConvert( valueSample->size(), 1, arnoldAPIType,
                            (void *) valueSample->get() ) );

                //get the indices
                Alembic::Abc::UInt32ArraySamplePtr idxSample = param.getIndexedValue( sampleSelector ).getIndices();

                std::vector<unsigned int> idxs;
                idxs.reserve( idxSample->size() );
                idxs.insert( idxs.end(),
                        idxSample->get(),
                        idxSample->get() +
                                idxSample->size() );

               // we must invert the idxs
               unsigned int base = 0;
               AtArray* nsides = AiNodeGetArray(primNode, "nsides");
               std::vector<unsigned int> nvidxReversed;
               for (unsigned int i = 0; i < AiArrayGetNumElements(nsides) / AiArrayGetNumKeys(nsides); ++i)
               {
                  int curNum = AiArrayGetUInt(nsides ,i);

                  for (int j = 0; j < curNum; ++j)
                  {
                      nvidxReversed.push_back(idxs[base+curNum-j-1]);
                  }
                  base += curNum;
               }
                AiNodeSetArray(primNode, CleanAttributeName(param.getName() + "idxs").c_str(), AiArrayConvert(nvidxReversed.size(), 1, AI_TYPE_UINT, (void*)&nvidxReversed[0]));
            }
			else
			{
				// Not indexed, probably a curve ?
				if(!AiNodeIs(primNode, AtString("curves")))
					return;

                typename T::prop_type::sample_ptr_type valueSample =
                        param.getIndexedValue( sampleSelector ).getVals();
				
				if(!paramExists)
					if ( !AiNodeDeclare( primNode, cleanAttributeName.c_str(), declStr.c_str() ) )
						return;

				int basis = AiNodeGetInt(primNode, AtString("basis"));

				if(basis != 3)
				{
					AtArray* curveNumPoints = AiNodeGetArray( primNode , "num_points"); 
					AtArray* radius = AiNodeGetArray( primNode, "radius");
					AtArray* finalValues = AiArrayAllocate( AiArrayGetNumElements(radius), 1, arnoldAPIType);

					unsigned int c_verts = 0;
					unsigned int w_start = 0; 
					unsigned int w_end = 0;
					int idxArray = 0;
					for ( int curCurve = 0; curCurve < AiArrayGetNumElements(curveNumPoints); curCurve++)
					{
						c_verts = AiArrayGetUInt(curveNumPoints, curCurve);
						unsigned int w_start = w_end;
						w_end += c_verts;
						if ( basis == 1 || basis == 2 )
						{
							for ( int r = w_start; r < w_end; r++ )
							{
								if ( r != w_start+1 && r != w_end-2 )
								{
									SetArrayByArnoldType<T>(finalValues, idxArray, arnoldAPIType, valueSample, r);
									idxArray++;
								}
							}
						}
						else if ( basis == 0 /* for bezier */ )
						{
							//  skip the control points.
							for ( int r = w_start; r < w_end; r+=3 )
							{
								SetArrayByArnoldType<T>(finalValues, idxArray, arnoldAPIType, valueSample, r);
								idxArray++;
							}
						}
					}
					AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(), finalValues );
				}
				else
				{
					AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(),
						AiArrayConvert( valueSample->size(), 1, arnoldAPIType,
								(void *) valueSample->get() ) );
				}

			}
        }
        else
        {
            typename T::prop_type::sample_ptr_type valueSample =
                    param.getExpandedValue( sampleSelector ).getVals();

			if(!paramExists)
				if ( !AiNodeDeclare( primNode, cleanAttributeName.c_str(), declStr.c_str() ) )
				{
					//TODO, AiWarning
					return;
				}

            AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(),
                    AiArrayConvert( valueSample->size(), 1, arnoldAPIType,
                            (void *) valueSample->get() ) );

        }
}


}


//-*****************************************************************************

void AddArbitraryStringGeomParam( ICompoundProperty & parent,
                            const PropertyHeader &propHeader,
                            ISampleSelector &sampleSelector,
                            AtNode * primNode)
{
    IStringGeomParam param( parent, propHeader.getName() );

    if ( !param.valid() )
    {
        //TODO error message?
        return;
    }

    std::string declStr = GetArnoldTypeString( param.getScope(),
            AI_TYPE_STRING, primNode, param.isIndexed() );
    if ( declStr.empty() )
    {
        return;
    }


    // TODO, remove this restriction and support arrays for constant values
    if ( param.getArrayExtent() > 1 )
    {
        return;
    }

    std::string cleanAttributeName = CleanAttributeName(param.getName());
    bool paramExists = false;

    const AtNodeEntry *nentry = AiNodeGetNodeEntry(primNode);
    AtParamIterator *iter = AiNodeEntryGetParamIterator(nentry);
    while (!AiParamIteratorFinished(iter))
    {
        const AtParamEntry *pentry = AiParamIteratorGetNext(iter);
        
        if (strcmp(cleanAttributeName.c_str(), AiParamGetName(pentry)) == 0)
        {
            paramExists = true;
            break;
        }

        
    }
    AiParamIteratorDestroy(iter);

    if(!paramExists)
        if ( !AiNodeDeclare( primNode, CleanAttributeName(param.getName()).c_str(), declStr.c_str() ) )
        {
            //TODO, AiWarning
            return;
        }

    IStringGeomParam::prop_type::sample_ptr_type valueSample =
                param.getExpandedValue( sampleSelector ).getVals();

    if ( param.getScope() == kConstantScope ||
            param.getScope() == kUnknownScope)
    {
        AiNodeSetStr( primNode, CleanAttributeName(param.getName()).c_str(),
                        reinterpret_cast<const std::string *>(
                                valueSample->get() )[0].c_str() );
    }
    else
    {
        std::vector<const char *> strPtrs;
        strPtrs.reserve( valueSample->size() );
        for ( size_t i = 0; i < valueSample->size(); ++i )
        {
            strPtrs.push_back( valueSample->get()[i].c_str() );
        }

        AiNodeSetArray( primNode, CleanAttributeName(param.getName()).c_str(),
                AiArrayConvert( valueSample->size(), 1, AI_TYPE_STRING,
                        (void *) &strPtrs[0] ) );


    }

}

//-*****************************************************************************

//UserDefDeclare(node, name.c_str(), userType.c_str())) continue;
//SetUserData(node, name.c_str(), dataSize, apiType, dataStart);


void AddArbitraryGeomParams( ICompoundProperty &parent,
                             ISampleSelector &sampleSelector,
                             AtNode * primNode,
                             const std::set<std::string> * excludeNames
                           )
{



    if ( primNode == NULL || !parent.valid() )
    {
        return;
    }

    for ( size_t i = 0; i < parent.getNumProperties(); ++i )
    {
        const PropertyHeader &propHeader = parent.getPropertyHeader( i );
        const std::string &propName = propHeader.getName();

        if (propName.empty()
            || ( excludeNames
                 && excludeNames->find( propName ) != excludeNames->end() ) )
        {
            continue;
        }

        if ( IDoubleGeomParam::matches( propHeader ) )
        {
           AddArbitraryGeomParam<IDoubleGeomParam>(
                   parent,
                   propHeader,
                   sampleSelector,
                   primNode,
                   AI_TYPE_DOUBLE);
        }
        if ( IFloatGeomParam::matches( propHeader ) )
        {

            AddArbitraryGeomParam<IFloatGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_FLOAT);
        }
        else if ( IBoolGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IBoolGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_BOOLEAN);
        }
        else if ( IInt32GeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IInt32GeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_INT);
        }
        else if ( IStringGeomParam::matches( propHeader ) )
        {
            AddArbitraryStringGeomParam(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode);
        }
        else if ( IV2fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IV2fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_VECTOR2);
        }
        else if ( IV3fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IV3fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_VECTOR);
        }
        else if ( IP3fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IP3fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_VECTOR);
        }
        else if ( IN3fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IN3fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_VECTOR);
        }
        else if ( IC3fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IC3fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_RGB);
        }
        else if ( IC4fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IC4fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_RGBA);
        }
        if ( IM44fGeomParam::matches( propHeader ) )
        {
            AddArbitraryGeomParam<IM44fGeomParam>(
                    parent,
                    propHeader,
                    sampleSelector,
                    primNode,
                    AI_TYPE_MATRIX);
        }


    }
}



void AddArbitraryProceduralParams(AtNode* proc, AtNode * primNode)
{
    AtUserParamIterator *iter = AiNodeGetUserParamIterator(proc);
    while (!AiUserParamIteratorFinished(iter))
    {
        const AtUserParamEntry *upentry = AiUserParamIteratorGetNext(iter);
        //printf("%s\n", AiUserParamGetName(upentry));
        const char* paramName = AiUserParamGetName(upentry);

        GeometryScope toAbcCategory = kConstantScope;

        int category  = AiUserParamGetCategory (upentry);
        if(category == 2)
            toAbcCategory = kUniformScope;
        else if(category == 3)
            toAbcCategory = kVertexScope;

        int arnoldAPIType = AiUserParamGetType (upentry);

        // bypass overrides
        if(arnoldAPIType == AI_TYPE_STRING)
        {
            if (strcmp(paramName, "assShaders") == 0 ||
                strcmp(paramName, "abcShaders") == 0 ||
                strcmp(paramName, "uvsArchive") == 0 ||
                strcmp(paramName, "overridefile") == 0 ||
                strcmp(paramName, "layerOverrides") == 0 ||
                strcmp(paramName, "displacementAssignation") == 0 ||
                strcmp(paramName, "shaderAssignation") == 0
                )
                continue;
        }
        else if(arnoldAPIType == AI_TYPE_BOOLEAN)
        {
            if (strcmp(paramName, "skipJson") == 0 ||
                strcmp(paramName, "skipShaders") == 0 ||
                strcmp(paramName, "skipAttributes") == 0 ||
                strcmp(paramName, "skipDisplacements") == 0 ||
                strcmp(paramName, "skipLayers") == 0
                )
                continue;
        }



        std::string declStr = GetArnoldTypeString( toAbcCategory, arnoldAPIType, primNode, false );
        if ( declStr.empty() )
        {
            continue;
        }

        // Check if that attribute is not existing already as a standard attribute.

        bool paramExists = false;

        const AtNodeEntry *nentry = AiNodeGetNodeEntry(primNode);
        AtParamIterator *piter = AiNodeEntryGetParamIterator(nentry);
        while (!AiParamIteratorFinished(piter))
        {
            const AtParamEntry *pentry = AiParamIteratorGetNext(piter);
            if (strcmp(paramName, AiParamGetName(pentry)) == 0)
            {
                paramExists = true;
                break;
            }

        
        }
        AiParamIteratorDestroy(piter);

        if(!paramExists)
            if ( !AiNodeDeclare( primNode, paramName, declStr.c_str() ) )
            {
                //TODO, AiWarning
                continue;
            }

        switch ( arnoldAPIType )
        {
            case AI_TYPE_BOOLEAN:
                AiNodeSetBool( primNode, paramName, AiNodeGetBool(proc, paramName)  );
                break;

            case AI_TYPE_INT:
                AiNodeSetInt( primNode, paramName, AiNodeGetInt(proc, paramName)  );

                break;
            case AI_TYPE_DOUBLE:
                AiNodeSetFlt( primNode, paramName, AiNodeGetFlt(proc, paramName)  );
                break;

            case AI_TYPE_FLOAT:
                AiNodeSetFlt( primNode, paramName, AiNodeGetFlt(proc, paramName)  );
                break;
            case AI_TYPE_STRING:
                AiNodeSetStr( primNode, paramName, AiNodeGetStr(proc, paramName)  );
                break;
            case AI_TYPE_RGB:
            {
                AtRGB val = AiNodeGetRGB(proc, paramName);
                AiNodeSetRGB( primNode, paramName, val.r, val.b, val.g);
                break;
            }
            case AI_TYPE_RGBA:
            {
                AtRGBA val = AiNodeGetRGBA(proc, paramName);
                AiNodeSetRGBA( primNode, paramName, val.r, val.b, val.g, val.a);
                break;
            }
            case AI_TYPE_VECTOR:
            {
                AtVector val = AiNodeGetVec(proc, paramName);
                AiNodeSetVec( primNode, paramName, val.x, val.y, val.z);
                break;
            }
            case AI_TYPE_VECTOR2:
            {
                AtVector2 val = AiNodeGetVec2(proc, paramName);
                AiNodeSetVec2( primNode, paramName, val.x, val.y);
                break;
            }
            case AI_TYPE_MATRIX:
            {
                AtMatrix m = AiNodeGetMatrix(proc, paramName);
                AiNodeSetMatrix( primNode, paramName, m);
                break;
            }
            default:
                // For now, only support the above types
                break;
        }

    }

    AiUserParamIteratorDestroy(iter);

}
