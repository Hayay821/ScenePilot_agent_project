cmake_minimum_required(VERSION 3.20)
project(OpenVideVisionDeviceSDK VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(OVV_BUILD_EXAMPLES "构建SDK示例" OFF)
option(OVV_BUILD_TESTS "构建SDK测试" OFF)
option(OVV_ENABLE_X5_CAMERA "构建Insta360 X5 CameraSDK适配器" OFF)
option(OVV_ENABLE_LINK_UVC "构建Insta360 Link 2 UVC适配器" OFF)
option(OVV_ENABLE_MEDIA_SDK "构建Insta360 MediaSDK处理器" OFF)

add_library(ovv_device_sdk
    src/device_executor.cpp)
add_library(ovv::device_sdk ALIAS ovv_device_sdk)

target_include_directories(ovv_device_sdk PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
target_compile_features(ovv_device_sdk PUBLIC cxx_std_17)

if(MSVC)
    target_compile_options(ovv_device_sdk PRIVATE /W4 /permissive- /utf-8)
else()
    target_compile_options(ovv_device_sdk PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(OVV_ENABLE_X5_CAMERA)
    set(INSTA360_CAMERA_SDK_ROOT "" CACHE PATH "CameraSDK 2.2.0根目录")
    set(INSTA360_MEDIA_SDK_ROOT "" CACHE PATH "MediaSDK 3.1.7根目录（X5实时拼接需要）")
    foreach(path
        "${INSTA360_CAMERA_SDK_ROOT}/include"
        "${INSTA360_CAMERA_SDK_ROOT}/lib/CameraSDK.lib")
        if(NOT EXISTS "${path}")
            message(FATAL_ERROR "缺少CameraSDK依赖： ${path}")
        endif()
    endforeach()
    target_sources(ovv_device_sdk PRIVATE src/x5_camera_adapter.cpp)
    target_include_directories(ovv_device_sdk PRIVATE "${INSTA360_CAMERA_SDK_ROOT}/include")
    target_include_directories(ovv_device_sdk PRIVATE "${INSTA360_MEDIA_SDK_ROOT}/include" "${INSTA360_MEDIA_SDK_ROOT}/include/stitcher")
    target_link_libraries(ovv_device_sdk PRIVATE "${INSTA360_CAMERA_SDK_ROOT}/lib/CameraSDK.lib")
    target_compile_definitions(ovv_device_sdk PUBLIC OVV_ENABLE_X5_CAMERA PRIVATE WIN32)
endif()

if(OVV_ENABLE_LINK_UVC)
    set(INSTA360_LINK_SDK_ROOT "" CACHE PATH "Link 2 UVCCamera x64 SDK根目录")
    foreach(path
        "${INSTA360_LINK_SDK_ROOT}/include"
        "${INSTA360_LINK_SDK_ROOT}/lib/UVCCamera.lib"
        "${INSTA360_LINK_SDK_ROOT}/lib/llog.lib")
        if(NOT EXISTS "${path}")
            message(FATAL_ERROR "缺少Link UVC SDK依赖： ${path}")
        endif()
    endforeach()
    target_sources(ovv_device_sdk PRIVATE src/link2_camera_adapter.cpp)
    target_include_directories(ovv_device_sdk PRIVATE "${INSTA360_LINK_SDK_ROOT}/include")
    target_link_libraries(ovv_device_sdk PRIVATE
        "${INSTA360_LINK_SDK_ROOT}/lib/UVCCamera.lib"
        "${INSTA360_LINK_SDK_ROOT}/lib/llog.lib")
    target_compile_definitions(ovv_device_sdk PUBLIC OVV_ENABLE_LINK_UVC PRIVATE WIN32)
endif()


if(OVV_ENABLE_MEDIA_SDK)
    set(INSTA360_MEDIA_SDK_ROOT "" CACHE PATH "MediaSDK 3.1.7根目录")
    foreach(path "${INSTA360_MEDIA_SDK_ROOT}/include" "${INSTA360_MEDIA_SDK_ROOT}/lib/MediaSDK.lib")
        if(NOT EXISTS "${path}")
            message(FATAL_ERROR "缺少MediaSDK依赖： ${path}")
        endif()
    endforeach()
    target_sources(ovv_device_sdk PRIVATE src/insta360_media_processor.cpp)
    target_include_directories(ovv_device_sdk PRIVATE "${INSTA360_MEDIA_SDK_ROOT}/include")
    target_link_libraries(ovv_device_sdk PRIVATE "${INSTA360_MEDIA_SDK_ROOT}/lib/MediaSDK.lib")
    target_compile_definitions(ovv_device_sdk PUBLIC OVV_ENABLE_MEDIA_SDK PRIVATE WIN32)
endif()
if(OVV_BUILD_EXAMPLES)
    add_executable(ovv_device_demo examples/device_executor_demo.cpp src/mock_device_adapter.cpp)
    target_link_libraries(ovv_device_demo PRIVATE ovv::device_sdk)
    if(MSVC)
        target_compile_options(ovv_device_demo PRIVATE /utf-8)
    endif()
endif()

if(OVV_BUILD_TESTS)
    enable_testing()
    add_executable(ovv_device_tests tests/device_executor_test.cpp src/mock_device_adapter.cpp)
    target_link_libraries(ovv_device_tests PRIVATE ovv::device_sdk)
    if(MSVC)
        target_compile_options(ovv_device_tests PRIVATE /utf-8)
    endif()
    add_test(NAME ovv_device_tests COMMAND ovv_device_tests)
endif()



include(GNUInstallDirs)
install(TARGETS ovv_device_sdk EXPORT ovv_device_sdk_targets)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(EXPORT ovv_device_sdk_targets NAMESPACE ovv:: DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/ovv_device_sdk)


if(OVV_ENABLE_X5_CAMERA AND WIN32)
    add_executable(ovv_x5_device_service ../device_bridge/x5_service/main.cpp)
    target_link_libraries(ovv_x5_device_service PRIVATE ovv::device_sdk ws2_32)
    target_link_libraries(ovv_x5_device_service PRIVATE "${INSTA360_MEDIA_SDK_ROOT}/lib/MediaSDK.lib")
    target_include_directories(ovv_x5_device_service PRIVATE "${INSTA360_CAMERA_SDK_ROOT}/include")
    target_compile_options(ovv_x5_device_service PRIVATE /utf-8)
    add_custom_command(TARGET ovv_x5_device_service POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "$<TARGET_FILE:ovv_x5_device_service>" "${CMAKE_CURRENT_SOURCE_DIR}/../device_bridge/runtime/ovv_x5_device_service.exe")
endif()