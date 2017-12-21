set(MAYAPLUGIN abcMayaShader)

file(GLOB SRC "*.cpp" "*h")

link_directories(${ARNOLD_LIBRARY_DIR})
add_library(${MAYAPLUGIN} SHARED ${SRC})

MAYA_SET_PLUGIN_PROPERTIES(${MAYAPLUGIN})

include_directories(${MTOA_INCLUDE_DIR})
include_directories(${ARNOLD_INCLUDE_DIR})

target_link_libraries(${MAYAPLUGIN} Alembic pystring ${MTOA_LIBRARY} ${MAYA_LIBRARIES} ai Iex Half)

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${MAYAPLUGIN} RUNTIME DESTINATION ${PLUGINS_INSTALL_DIR})
else()
	install(TARGETS ${MAYAPLUGIN} DESTINATION ${PLUGINS_INSTALL_DIR})
endif()
