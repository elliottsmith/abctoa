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


#include "abcCacheExportCmd.h"
#include "abcExporterUtils.h"

namespace Abc =  Alembic::Abc;
namespace Mat = Alembic::AbcMaterial;


MStatus abcCacheExportCmd::doIt( const MArgList &args)
{
  MStatus stat = MStatus::kSuccess;
  MArgDatabase argData( syntax(), args);

  if(!argData.isFlagSet( "-f"))
  {
      MGlobal::displayError("no output file!");
      return MStatus::kFailure;

  }
  MString filename("");
  argData.getFlagArgument( "-f", 0, filename);

  // create materials archive
  Abc::OArchive archive(Alembic::AbcCoreOgawa::WriteArchive(), filename.asChar() );
  Abc::OObject root(archive, Abc::kTop);
  Abc::OObject materials(root, "materials");

    MSelectionList list;
    if(argData.isFlagSet( "-sl"))
    {
        MGlobal::getActiveSelectionList (list);
    }
    else if (argData.isFlagSet( "-node"))
    {
        MString node("");
        argData.getFlagArgument( "-node", 0, node);
        if (list.add(node) != MS::kSuccess)
        {
            MString warn = node;
            warn += " could not be select, skipping.";
            MGlobal::displayWarning(warn);
            return MStatus::kFailure;
        }
    }
    else
    {
         MItDependencyNodes nodeIt;
         for (; !nodeIt.isDone(); nodeIt.next())
         {
            MObject node = nodeIt.item();
            if (node.isNull())
                continue;
            list.add (node);
         }
    }

    CMayaScene::Begin(MTOA_SESSION_ASS);
    CArnoldSession* arnoldSession = CMayaScene::GetArnoldSession();
    CRenderSession* renderSession = CMayaScene::GetRenderSession();

    renderSession->SetOutputAssMask(16);
    arnoldSession->SetExportFilterMask(16);
    renderSession->SetForceTranslateShadingEngines(false);

    CMayaScene::Export(NULL);
    AiASSWrite(pystring::replace(filename.asChar(), ".abc", ".ass").c_str(), AI_NODE_SHADER, false);

    MItSelectionList iter(list, MFn::kPluginShape);
     for (; !iter.isDone(); iter.next())
     {
         MObject dependNode;
         iter.getDependNode(dependNode);
         MFnDagNode dagNode(dependNode);

         AiMsgDebug("[abcCacheExportCmd] alembicHolder: %s", dagNode.name().asChar());
         MPlug shaders = dagNode.findPlug("shaders");

         std::vector<MPlug> shaderToExport;

          for (unsigned int i=0;i<shaders.numElements();++i)
          {
             MPlug plug = shaders.elementByPhysicalIndex(i);
             AiMsgDebug("[abcCacheExportCmd] alembicHolder connected shader: %s", plug.name().asChar());
             MPlugArray connections;
             plug.connectedTo(connections, true, false);
             for (unsigned int k=0; k<connections.length(); ++k)
             {
                MPlug sgPlug = connections[k];
                shaderToExport.push_back(sgPlug);
             }
          }


        for (std::vector<MPlug>::iterator it = shaderToExport.begin() ; it != shaderToExport.end(); ++it)
        {
            AtNodeSet* exportedNodes = new AtNodeSet;


            MPlug toExport = *it;

            // create the material
            MFnDependencyNode container(toExport.node());

            AiMsgDebug("[abcCacheExportCmd] creating container: %s", container.name().asChar());
            Mat::OMaterial matObj(materials, container.name().asChar());

            CNodeTranslator* translator = arnoldSession->ExportNode(toExport);
            if(true)
             {
                 AtNode* root = translator->GetArnoldNode();
                 AiMsgDebug("[abcCacheExportCmd] container root: %s", AiNodeGetStr(root, "name").c_str());

                 exportedNodes->insert(root);
                 // We need to traverse the tree again...
                 getAllArnoldNodes(root, exportedNodes);

                 std::unordered_set<AtNode*>::const_iterator sit (exportedNodes->begin()), send(exportedNodes->end());
                 for(;sit!=send;++sit)
                 {
                     // adding the node to the network
                     MString nodeName(container.name());
                     nodeName = nodeName + ":" + MString(AiNodeGetName(*sit));

                     nodeName = MString(pystring::replace(pystring::replace(std::string(nodeName.asChar()), ".message", ""), ".", "_").c_str());

                     AiMsgDebug("[abcCacheExportCmd] node added: %s", nodeName.asChar());
                     matObj.getSchema().addNetworkNode(nodeName.asChar(), "arnold", AiNodeEntryGetName(AiNodeGetNodeEntry(*sit)));

                     if(root == *sit)
                     {
                         AiMsgDebug("[abcCacheExportCmd] node: %s", nodeName.asChar());
                         //TODO : get if it's a volume, eventually
                        matObj.getSchema().setNetworkTerminal(
                        "arnold",
                        "surface",
                        nodeName.asChar(),
                        "out");
                     }

                     ////////////////////////////////////////////////////////////////////////////////////////////
                     //export parameters
                     AiMsgDebug("[abcCacheExportCmd] node added: %s", nodeName.asChar());
                     AtParamIterator* nodeParam = AiNodeEntryGetParamIterator(AiNodeGetNodeEntry(*sit));
                     int outputType = AiNodeEntryGetOutputType(AiNodeGetNodeEntry(*sit));

                     while (!AiParamIteratorFinished(nodeParam))
                     {
                         const AtParamEntry *paramEntry = AiParamIteratorGetNext(nodeParam);
                         const char* paramName = AiParamGetName(paramEntry);

                         if(AiParamGetType(paramEntry) == AI_TYPE_ARRAY)
                         {

                            AtArray* paramArray = AiNodeGetArray(*sit, paramName);

                            processArrayValues(*sit, paramName, paramArray, outputType, matObj, nodeName, container.name());
                            for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
                            {
                                processArrayParam(*sit, paramName, paramArray, i, outputType, matObj, nodeName, container.name());
                            }


                         }
                         else
                         {
                            processLinkedParam(*sit, AiParamGetType(paramEntry), outputType, matObj, nodeName, paramName, container.name(), true);
                         }
                     }
                     AiParamIteratorDestroy(nodeParam);

                     ////////////////////////////////////////////////////////////////////////////////////////////
                     //export user parameters
                     AtUserParamIterator *nodeUserParam = AiNodeGetUserParamIterator(*sit);

                     while (!AiUserParamIteratorFinished(nodeUserParam))
                     {
                         const AtUserParamEntry *paramEntry = AiUserParamIteratorGetNext(nodeUserParam);
                         const char* paramName = AiUserParamGetName(paramEntry);

                         if(AiUserParamGetType(paramEntry) == AI_TYPE_ARRAY)
                         {

                            AtArray* paramArray = AiNodeGetArray(*sit, paramName);

                            processArrayValues(*sit, paramName, paramArray, outputType, matObj, nodeName, container.name());
                            for(unsigned int i=0; i < AiArrayGetNumElements(paramArray); i++)
                            {
                                processArrayParam(*sit, paramName, paramArray, i, outputType, matObj, nodeName, container.name());
                            }


                         }
                         else
                         {
                            processLinkedParam(*sit, AiUserParamGetType(paramEntry),outputType, matObj, nodeName, paramName, container.name(), true);
                         }
                     }
                     AiUserParamIteratorDestroy(nodeUserParam);
                 }
            }
            AiMsgTab(-2);
        }

    }
    AiMsgDebug("[abcCacheExportCmd] Success!");
    CMayaScene::End();
    return MStatus::kSuccess;
}


//  There is never anything to undo.
//////////////////////////////////////////////////////////////////////
MStatus abcCacheExportCmd::undoIt(){
  return MStatus::kSuccess;
}

//
//  There is never really anything to redo.
//////////////////////////////////////////////////////////////////////
MStatus abcCacheExportCmd::redoIt(){
  return MStatus::kSuccess;
}

//
//
//////////////////////////////////////////////////////////////////////
bool abcCacheExportCmd::isUndoable() const{
  return false;
}

//
//
//////////////////////////////////////////////////////////////////////
bool abcCacheExportCmd::hasSyntax() const {
  return true;
}

//
//
//////////////////////////////////////////////////////////////////////
MSyntax abcCacheExportCmd::mySyntax() {
  MSyntax syntax;

  syntax.addFlag( "-sl", "-selection", MSyntax::kString);
  syntax.addFlag( "-f", "-file", MSyntax::kString);
  syntax.addFlag( "-n", "-node", MSyntax::kString);

  return syntax;
}

//
//
//////////////////////////////////////////////////////////////////////
bool abcCacheExportCmd::isHistoryOn() const {
  //what is this supposed to do?
  return false;
}

MString abcCacheExportCmd::commandString() const {
  return MString();
}


MStatus abcCacheExportCmd::setHistoryOn( bool state ){
  //ignore it for now
  return MStatus::kSuccess;
}

MStatus abcCacheExportCmd::setCommandString( const MString &str) {
  //ignore it for now
  return MStatus::kSuccess;
}