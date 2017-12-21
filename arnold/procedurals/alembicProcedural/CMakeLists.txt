set(PROC arnoldAlembicProcedural)

file(GLOB SRC "*.cpp" "*h" "../../../common/abcshaderutils.h" "../../../common/abcshaderutils.cpp" "../../../common/PathUtil.h" "../../../common/PathUtil.cpp")

include_directories(${ARNOLD_INCLUDE_DIR})
include_directories(${CMAKE_SOURCE_DIR}/common)
include_directories(${ALEMBIC_ILMBASE_INCLUDE_DIRECTORY})

link_directories(${ARNOLD_LIBRARY_DIR})

add_library(${PROC} SHARED ${SRC})
target_link_libraries(${PROC} ai Alembic jsoncpp pystring Iex Half)
set_target_properties(${PROC} PROPERTIES PREFIX "")

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${PROC} RUNTIME DESTINATION ${DSO_INSTALL_DIR})
else()
	

install(TARGETS ${PROC} DESTINATION ${DSO_INSTALL_DIR})
endif()

