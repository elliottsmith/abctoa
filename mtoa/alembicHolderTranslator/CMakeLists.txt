set(MTOATRANSLATOR alembicHolderTranslator)

file(GLOB SRC "*.cpp" "*h")
include_directories(${MTOA_INCLUDE_DIR})
include_directories(${ARNOLD_INCLUDE_DIR})

add_library(${MTOATRANSLATOR} SHARED ${SRC})
link_directories(${ARNOLD_LIBRARY_DIR})

MAYA_SET_TRANSLATOR_PROPERTIES(${MTOATRANSLATOR})

target_link_libraries(${MTOATRANSLATOR} ${MTOA_LIBRARY} ${MAYA_LIBRARIES} ai pystring)
set_target_properties(${MTOATRANSLATOR} PROPERTIES PREFIX "")

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${MTOATRANSLATOR} RUNTIME DESTINATION ${TRANSLATOR_INSTALL_DIR})
else()
	install(TARGETS ${MTOATRANSLATOR} DESTINATION ${TRANSLATOR_INSTALL_DIR})
endif()
