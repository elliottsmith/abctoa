set(UTIL assShadersToAbc)

file(GLOB SRC "*.cpp" "*h" "../../../common/abc*.h" "../../../common/abc*.cpp")

include_directories(${CMAKE_SOURCE_DIR}/common)
include_directories(${CMAKE_SOURCE_DIR}/thirdparty/ezOptionParser)
include_directories(${ARNOLD_INCLUDE_DIR})
link_directories(${ARNOLD_LIBRARY_DIR})

add_executable(${UTIL} ${SRC})
target_link_libraries(${UTIL} ai Alembic jsoncpp pystring Iex Half)
set_target_properties(${UTIL} PROPERTIES PREFIX "")

if (${CMAKE_SYSTEM_NAME} MATCHES "Windows")
	install(TARGETS ${UTIL} RUNTIME DESTINATION ${DSO_INSTALL_DIR})
else()
	

install(TARGETS ${UTIL} DESTINATION ${DSO_INSTALL_DIR})
endif()

