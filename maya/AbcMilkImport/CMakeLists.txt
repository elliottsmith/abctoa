set(MAYAPLUGIN AbcMilkImport)

file(GLOB SRC "*.cpp" "*h")

# link_directories(${ARNOLD_LIBRARY_DIR})
add_library(${MAYAPLUGIN} SHARED ${SRC})

MAYA_SET_PLUGIN_PROPERTIES(${MAYAPLUGIN})

# include_directories(${MTOA_INCLUDE_DIR})
# include_directories(${ARNOLD_INCLUDE_DIR})

# target_link_libraries(${MAYAPLUGIN} Alembic ${MAYA_LIBRARIES} Iex Half)
target_link_libraries(${MAYAPLUGIN} AlembicAbcCoreFactory ${MAYA_LIBRARIES} Iex Half)
# target_link_libraries(${MAYAPLUGIN} ${MAYA_LIBRARIES} AlembicAbcCoreFactory AlembicAbcCoreHDF5 AlembicAbcCoreOgawa AlembicAbcGeom AlembicAbc AlembicAbcCoreAbstract AlembicAbcMaterial AlembicAbcCollection AlembicOgawa AlembicUtil hdf5_hl hdf5 AlembicIex AlembicHalf AlembicImath z)
set_target_properties(${MAYAPLUGIN} PROPERTIES PREFIX "")

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${MAYAPLUGIN} RUNTIME DESTINATION ${PLUGINS_INSTALL_DIR})
else()
	install(TARGETS ${MAYAPLUGIN} DESTINATION ${PLUGINS_INSTALL_DIR})
endif()
