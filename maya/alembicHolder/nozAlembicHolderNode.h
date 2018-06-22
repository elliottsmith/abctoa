/*Alembic Holder
Copyright (c) 2014, Ga�l Honorez, All rights reserved.
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


#ifndef _nozAlembicHolderNode
#define _nozAlembicHolderNode

#include "AlembicScene.h"
#include "RenderModules.h"
#include "Foundation.h"
#include "TextureLoader.h"

#include <maya/MPxSurfaceShape.h>
#include <maya/MPxSurfaceShapeUI.h>

#include <maya/MPxNode.h>
#include <maya/MFnNumericAttribute.h>
#include <maya/MFnData.h>
#include <maya/MFnDagNode.h>
#include <maya/MFnMessageAttribute.h>
#include <maya/MFnTypedAttribute.h>
#include <maya/MFnUnitAttribute.h>
#include <maya/MBoundingBox.h>
#include <maya/MString.h>
#include <maya/MStringArray.h>
#include <maya/MIntArray.h>
#include <maya/MDoubleArray.h>
#include <maya/MFnStringData.h>
#include <maya/MTypeId.h>
#include <maya/MFnDependencyNode.h>
#include <maya/MDagPath.h>
#include <maya/MNodeMessage.h>
#include <maya/MMatrix.h>
#include <maya/MFnCamera.h>
#include <maya/MFnRenderLayer.h>
#include <maya/MTime.h>

#include <json/json.h>
#include "parseJson.h"

#include <iostream>
#include <unordered_map>
#include <unordered_set>

namespace AlembicHolder {

struct MStringComp
{
    bool operator() (MString lhs, MString rhs) const
    {
        int res = strcmp(lhs.asChar(), rhs.asChar());
        if (res < 0) {
            return true;
        }
        else {
            return false;
        }
        return strcmp(lhs.asChar(), rhs.asChar()) <= 0;
    }
};

typedef HierarchyNodeCategories::DrawableID DrawableID;
struct DiffuseColorOverride {
    C3f diffuse_color;
    std::string diffuse_texture_path;
};
typedef std::unordered_map<DrawableID, DiffuseColorOverride> DiffuseColorOverrideMap;

class nozAlembicHolder : public MPxSurfaceShape
{
public:
    nozAlembicHolder();
    virtual ~nozAlembicHolder();

    virtual void postConstructor();
    virtual MStatus compute( const MPlug& plug, MDataBlock& data );

    virtual bool isBounded() const;
    virtual MBoundingBox boundingBox()const;

    virtual void copyInternalData( MPxNode* srcNode );

    static  void*       creator();
    static  MStatus     initialize();

    MSelectionMask getShapeSelectionMask() const override;

private:
    void updateCache() const { MPlug(thisMObject(), aUpdateCache).asInt(); }
    void updateAssign() const { MPlug(thisMObject(), aUpdateAssign).asInt(); }

public:
    const AlembicScenePtr& getScene() const;
    const AlembicSceneKey& getSceneKey() const;
    std::string getSelectionKey() const;
    chrono_t getTime() const;
    bool isBBExtendedMode() const;
    const DiffuseColorOverrideMap& getDiffuseColorOverrides() const;
    std::string getShaderAssignmentsJson() const;

    struct SceneSample {
        chrono_t time;
        DrawableSampleVector drawable_samples;
        HierarchyStat hierarchy_stat;
        std::vector<bool> selection_visibility;
        SceneSample() : time(-std::numeric_limits<chrono_t>::infinity()) {}
        bool empty() const { return drawable_samples.empty(); }
    };
    const SceneSample& getSample() const;

private:
    AlembicSceneKey m_scene_key;
    AlembicScenePtr m_scene;
    SceneSample m_sample;
    std::string m_selection_key;

    std::string m_shader_assignments;
    DiffuseColorOverrideMap m_diffuse_color_overrides;
    void updateDiffuseColorOverrides();

private:
    holderPrms m_params;
public:
    const holderPrms& params() const { return m_params; }

    static    MObject    aAbcFiles;
    static    MObject    aObjectPath;
    static    MObject    aBoundingExtended;
    static    MObject    aTime;
    static    MObject    aTimeOffset;
    static    MObject    aSelectionPath;
    static    MObject    aShaderPath;
    static    MObject    aForceReload;

	static    MObject    aJsonFile;
	static    MObject    aJsonFileSecondary;
	static    MObject    aShadersNamespace;
    static    MObject    aGeometryNamespace;    
	static    MObject    aShadersAttribute;
	static    MObject    aAbcShaders;
	static    MObject	 aUvsArchive;
	static    MObject	 aShadersAssignation;
	static    MObject	 aAttributes;
	static    MObject	 aDisplacementsAssignation;
	static    MObject	 aLayersOverride;
	static    MObject    aSkipJsonFile;
	static    MObject    aSkipShaders;
	static    MObject    aSkipAttributes;
	static    MObject    aSkipLayers;
	static    MObject    aSkipDisplacements;
	
	static    MObject	 aUpdateAssign;
	static    MObject    aUpdateCache;
    static    MObject    aUpdateTransforms;

    static    MObject    aBoundMin;
    static    MObject    aBoundMax;

    static    MObject    aUserOptions;
    static    MObject    aOpaque;
    static    MObject    aSelfShadows;
    static    MObject    aMatte; 
    static    MObject    aReceiveShadows;
    static    MObject    aTraceSets;
    static    MObject    aSssSetname;

    static    MCallbackId attrChangeCBID;            

public:
    static  MTypeId     id;
};


struct VP1DrawableItem {
    BufferObject buffer;
    M44f world_matrix;
    C3f diffuse_color;
    DrawableID drawable_id;
    VP1DrawableItem(MGLenum prim_type, MGLsizei prim_count)
    {
        buffer.setPrimType(prim_type);
        buffer.setPrimNum(prim_count);
    }
};
struct VP1PrimitiveFilter {
    enum { POINTS = 1, LINES = 2, TRIANGLES = 4, ALL = 7 };
    uint8_t mask;
    VP1PrimitiveFilter(uint8_t mask_=ALL) : mask(mask_) {}
    bool has(MGLenum gl_prim_type) const
    {
        uint8_t prim_type = 0;
        if (gl_prim_type == MGL_POINTS)
            prim_type = POINTS;
        else if (gl_prim_type == MGL_LINES)
            prim_type = LINES;
        else if (gl_prim_type == MGL_TRIANGLES)
            prim_type = TRIANGLES;
        return (mask & prim_type) != 0;
    }
};
struct VP1DrawSettings {
    bool override_color;
    bool use_texture;
    const DiffuseColorOverrideMap& color_overrides;
    // Only draw the types of primitives specified in the filter.
    VP1PrimitiveFilter primitive_filter;
    bool flip_normals;
    VP1DrawSettings(bool override_color_, bool use_texture_ = false,
                 const DiffuseColorOverrideMap& color_overrides_ = DiffuseColorOverrideMap(),
                 VP1PrimitiveFilter primitive_filter_ = VP1PrimitiveFilter(),
                 bool flip_normals_=false)
        : override_color(override_color_), use_texture(use_texture_)
        , color_overrides(color_overrides_)
        , primitive_filter(primitive_filter_)
        , flip_normals(flip_normals_)
    {}
};
struct VP1DrawableContainer {
    std::vector<VP1DrawableItem> drawables;
    std::vector<std::pair<std::string, VP1TexturePtr>> textures;
    void draw(const VP1DrawSettings& draw_settings) const;
};

// UI class    - defines the UI part of a shape node
class CAlembicHolderUI: public MPxSurfaceShapeUI {
public:
    CAlembicHolderUI();
    virtual ~CAlembicHolderUI();
    virtual void getDrawRequests(const MDrawInfo & info,
            bool objectAndActiveOnly, MDrawRequestQueue & requests);
    virtual void draw(const MDrawRequest & request, M3dView & view) const;

    void drawBoundingBox( const MDrawRequest & request, M3dView & view ) const;

    MPoint getPointAtDepth(MSelectInfo &selectInfo, double    depth) const;

    virtual bool select(MSelectInfo &selectInfo, MSelectionList &selectionList,
            MPointArray &worldSpaceSelectPts) const;

    void getDrawRequestsWireFrame(MDrawRequest&, const MDrawInfo&);
    void getDrawRequestsBoundingBox(MDrawRequest&, const MDrawInfo&);
    void            getDrawRequestsShaded(      MDrawRequest&,
                                              const MDrawInfo&,
                                              MDrawRequestQueue&,
                                              MDrawData& data );


    static void * creator();
    // Draw Tokens
    //
    enum {
        kDrawWireframe,
        kDrawWireframeOnShaded,
        kDrawSmoothShaded,
        kDrawFlatShaded,
        kDrawBoundingBox,
        kLastToken
    };

private:
    VP1DrawableContainer m_vp1drawables;
    void updateVP1Drawables(const nozAlembicHolder::SceneSample& scene_sample, const DiffuseColorOverrideMap& color_overrides, const StaticMaterialVector& static_materials);
    void drawWithTwoSidedLightingSupport(const VP1DrawableContainer& drawable_container, VP1DrawSettings draw_settings) const;
}; // class CAlembicHolderUI

} // namespace AlembicHolder

#endif // header guard
