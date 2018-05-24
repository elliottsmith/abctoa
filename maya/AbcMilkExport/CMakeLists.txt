set(MAYAPLUGIN AbcMilkExport)

file(GLOB SRC "*.cpp" "*h")

link_directories(${ARNOLD_LIBRARY_DIR})
add_library(${MAYAPLUGIN} SHARED ${SRC})

MAYA_SET_PLUGIN_PROPERTIES(${MAYAPLUGIN})

target_link_libraries(${MAYAPLUGIN} Alembic ${MAYA_LIBRARIES} Iex Half)
set_target_properties(${MAYAPLUGIN} PROPERTIES PREFIX "")

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${MAYAPLUGIN} RUNTIME DESTINATION ${PLUGINS_INSTALL_DIR})
else()
	install(TARGETS ${MAYAPLUGIN} DESTINATION ${PLUGINS_INSTALL_DIR})
endif()
