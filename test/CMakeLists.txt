cmake_minimum_required(VERSION 3.4.1)

add_library(c_shared SHARED shared/shared.c)
add_library(cpp_shared SHARED shared/shared.cpp)
add_library(c_static STATIC static/static.c)
add_library(cpp_static STATIC static/static.cpp)

add_executable(c_exe exe.c)
target_link_libraries(c_exe c_shared c_static)

add_executable(cpp_exe exe.cpp)
target_link_libraries(cpp_exe c_shared c_static cpp_shared cpp_static)
