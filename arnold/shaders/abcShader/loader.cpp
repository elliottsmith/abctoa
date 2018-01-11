/*Alembic Arnold Shader
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

#include <ai.h>
#include <stdio.h>

extern AtNodeMethods* ABCShaderMethods;
//extern AtNodeMethods* ShaderAssignMethods;


enum SHADERS
{
   ABCSHADER
   //ASSIGNSHADER
};

node_loader
{
   sprintf(node->version, AI_VERSION);

   switch (i)
   {
   case ABCSHADER :
      node->methods     = (AtNodeMethods*) ABCShaderMethods;
      node->output_type = AI_TYPE_CLOSURE;
      node->name        = "AbcShader";
      node->node_type   = AI_NODE_SHADER;
      break;/*
   case ASSIGNSHADER :
      node->methods     = (AtNodeMethods*) ShaderAssignMethods;
      node->output_type = AI_TYPE_RGB;
      node->name        = "AssignShader";
      node->node_type   = AI_NODE_SHADER;
      break;   */
   default:
      return false;
   }

   return true;
}
