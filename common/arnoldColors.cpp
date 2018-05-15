//-*****************************************************************************
//
// Copyright (c) 2009-2010,
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
#include "arnoldColors.h"
#include <vector>

//-*****************************************************************************

double CalculateTriangleArea(const AtVector& p0, const AtVector& p1, const AtVector& p2)
{
   const AtVector t0(p1.x - p0.x, p1.y - p0.y, p1.z - p0.z);
   const AtVector t1(p2.x - p0.x, p2.y - p0.y, p2.z - p0.z);
   return double(AiV3Length(AiV3Cross(t0, t1)) * 0.5f);
}

//-*****************************************************************************

void NormalizeRGB(AtNode* mesh, AtRGB &colorMultiplier){

    AtNode *poly = (AtNode*)AiNodeGetPtr(mesh, "node");
    AtString name = AiNodeGetStr(poly, "name");
    AiMsgDebug("  [arnoldColors][_NormalizeRGB] Normalise RGB");

    double surfaceArea = 0.f;
    int counter = 0;

    // VLIST
    std::vector<AtVector> vlist; 
    for(unsigned int i=0; i < AiArrayGetNumElements(AiNodeGetArray(poly, "vlist")); i++){
        AtVector vec = AiArrayGetVec(AiNodeGetArray(poly, "vlist"), i);
        vlist.push_back(vec);
    }

    // AiMsgDebug("  [WriteGeo][doNormalize] Number of Polygons: %d", AiArrayGetNumElements(AiNodeGetArray(poly, "nsides")));

    for(unsigned int i=0; i < AiArrayGetNumElements(AiNodeGetArray(poly, "nsides")); i++){
        int num_vertices = AiArrayGetUInt(AiNodeGetArray(poly, "nsides"), i);
        // AiMsgDebug("  [WriteGeo][doNormalize] Polygon %d has %d vertices", i, num_vertices);

        std::vector<int> vidxs;
        for(unsigned int i=0; i < num_vertices; i++){
            vidxs.push_back(counter);
            counter += 1;
        }

        std::vector<int> proper_vidx;     
        for(unsigned int v=0; v < vidxs.size(); v++){
            uint vx = AiArrayGetUInt(AiNodeGetArray(poly, "vidxs"), v);
            proper_vidx.push_back(vx);
        }

        const int vertexCount = proper_vidx.size();

        if (vertexCount){

            const AtVector vector0 = AtVector(vlist[proper_vidx[0]].x, vlist[proper_vidx[0]].y, vlist[proper_vidx[0]].z);
            // AiMsgDebug("  [WriteGeo][doNormalize] Vector0: %d, %d, %d", vector0.x, vector0.y, vector0.z);

            for (int j = 1; j < vertexCount - 1; ++j) {

                const AtVector vector1 = AtVector(vlist[proper_vidx[j]].x, vlist[proper_vidx[j]].y, vlist[proper_vidx[j]].z);
                const AtVector vector2 = AtVector(vlist[proper_vidx[j + 1]].x, vlist[proper_vidx[j + 1]].y, vlist[proper_vidx[j + 1]].z);

                // AiMsgDebug("  [WriteGeo][doNormalize] Vector1: %d, %d, %d", vector1.x, vector1.y, vector1.z);
                // AiMsgDebug("  [WriteGeo][doNormalize] Vector2: %d, %d, %d", vector2.x, vector2.y, vector2.z);                                
                surfaceArea += CalculateTriangleArea(vector0, vector1, vector2);

            }
        }
    }

    colorMultiplier = colorMultiplier / float(surfaceArea);
    AiMsgDebug("  [arnoldColors][_NormalizeRGB] surface  area : %f", float(surfaceArea));
}