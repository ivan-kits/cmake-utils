cmake_minimum_required(VERSION 3.4.1)

add_library(c_shared SHARED shared/shared.c)
add_library(c_static STATIC static/static.c)
set(C_LIBRARIES c_shared c_static)

if(ANDROID_STL STREQUAL none)
	add_definitions(-DNONE)
elseif(ANDROID_STL STREQUAL system)
	add_definitions(-DSYSTEM)
else()
	add_library(cpp_shared SHARED shared/shared.cpp)
	add_library(cpp_static STATIC static/static.cpp)
	set(CPP_LIBRARIES cpp_shared cpp_static)
endif()

add_executable(c_exe exe.c)
target_link_libraries(c_exe ${C_LIBRARIES})

add_executable(cpp_exe exe.cpp)
target_link_libraries(cpp_exe ${C_LIBRARIES} ${CPP_LIBRARIES})
