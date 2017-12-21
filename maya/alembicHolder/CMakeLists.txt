set(MAYAPLUGIN alembicHolder)

file(GLOB SRC "*.cpp" "*h" "cmds/*.cpp" "cmds/*.h" "../../common/PathUtil.cpp" "../../common/PathUtil.h")

find_package(Boost)

add_library(${MAYAPLUGIN} SHARED ${SRC})

target_link_libraries(${MAYAPLUGIN} ${MAYA_LIBRARIES} ${MAYA_LIBRARY_DIRS}/tbb.lib Alembic jsoncpp pystring Iex Half ${Boost_REGEX_LIBRARY} ${Boost_SYSTEM_LIBRARY} ${Boost_CHRONO_LIBRARY} ${Boost_DATE_TIME_LIBRARY} ${Boost_THREAD_LIBRARY})


MAYA_SET_PLUGIN_PROPERTIES(${MAYAPLUGIN})

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	target_link_libraries(${MAYAPLUGIN} OpenGl32 wbemuuid)
endif()

if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
	set(new_link_flags "-framework OpenGL -framework AGL")
	get_target_property(existing_link_flags ${MAYAPLUGIN} LINK_FLAGS)
	if(existing_link_flags)
		set(new_link_flags "${existing_link_flags} ${new_link_flags}")
	endif()
	set_target_properties(${MAYAPLUGIN} PROPERTIES LINK_FLAGS ${new_link_flags})
endif()

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${MAYAPLUGIN} RUNTIME DESTINATION ${PLUGINS_INSTALL_DIR})
else()
	install(TARGETS ${MAYAPLUGIN} DESTINATION ${PLUGINS_INSTALL_DIR})
endif()
