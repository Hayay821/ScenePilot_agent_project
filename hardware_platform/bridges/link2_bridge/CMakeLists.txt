cmake_minimum_required(VERSION 3.20)
project(link2_bridge VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# === 依赖库路径 ===

# Link-SDK 路径（从环境变量或命令行参数）
if(NOT DEFINED LINK_SDK_PATH)
    if(DEFINED ENV{LINK_SDK_PATH})
        set(LINK_SDK_PATH $ENV{LINK_SDK_PATH})
    else()
        message(FATAL_ERROR "LINK_SDK_PATH not set. Set it via -DLINK_SDK_PATH=... or environment variable")
    endif()
endif()

message(STATUS "Link-SDK path: ${LINK_SDK_PATH}")

# 查找 Link-SDK 库
find_library(LINK_SDK_LIB
    NAMES UVCCameraSDK libUVCCameraSDK
    PATHS ${LINK_SDK_PATH}/lib
    NO_DEFAULT_PATH
)

if(NOT LINK_SDK_LIB)
    message(FATAL_ERROR "Link-SDK library not found in ${LINK_SDK_PATH}/lib")
endif()

message(STATUS "Link-SDK library: ${LINK_SDK_LIB}")

# === 第三方依赖 ===

# httplib (header-only)
find_path(HTTPLIB_INCLUDE_DIR httplib.h
    PATHS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/httplib
)

# websocketpp (header-only)
find_path(WEBSOCKETPP_INCLUDE_DIR websocketpp/server.hpp
    PATHS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/websocketpp
)

# nlohmann/json (header-only)
find_path(NLOHMANN_JSON_INCLUDE_DIR nlohmann/json.hpp
    PATHS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/json/include
)

# === 源文件 ===

set(SOURCES
    src/main.cpp
    src/device_manager.cpp
    src/http_server.cpp
    src/websocket_server.cpp
    src/command_executor.cpp
)

set(HEADERS
    include/device_manager.h
    include/http_server.h
    include/websocket_server.h
    include/command_executor.h
    include/protocol.h
)

# === 可执行文件 ===

add_executable(link2_bridge ${SOURCES} ${HEADERS})

target_include_directories(link2_bridge PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${LINK_SDK_PATH}/include
    ${HTTPLIB_INCLUDE_DIR}
    ${WEBSOCKETPP_INCLUDE_DIR}
    ${NLOHMANN_JSON_INCLUDE_DIR}
)

target_link_libraries(link2_bridge PRIVATE
    ${LINK_SDK_LIB}
)

# === 平台特定设置 ===

if(WIN32)
    # Windows: 链接 WinSock
    target_link_libraries(link2_bridge PRIVATE ws2_32)

    # 复制 DLL 到输出目录
    if(EXISTS ${LINK_SDK_PATH}/bin)
        add_custom_command(TARGET link2_bridge POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_directory
            ${LINK_SDK_PATH}/bin $<TARGET_FILE_DIR:link2_bridge>
        )
    endif()

elseif(UNIX)
    # Linux: 链接 pthread
    find_package(Threads REQUIRED)
    target_link_libraries(link2_bridge PRIVATE Threads::Threads)

    # 设置 RPATH
    set_target_properties(link2_bridge PROPERTIES
        INSTALL_RPATH "${LINK_SDK_PATH}/lib"
        BUILD_WITH_INSTALL_RPATH TRUE
    )
endif()

# === 编译选项 ===

if(MSVC)
    target_compile_options(link2_bridge PRIVATE /W4)
else()
    target_compile_options(link2_bridge PRIVATE -Wall -Wextra -Wpedantic)
endif()

# === 安装 ===

install(TARGETS link2_bridge
    RUNTIME DESTINATION bin
)

# === 提示信息 ===

message(STATUS "")
message(STATUS "Link2 Bridge Configuration:")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Link-SDK: ${LINK_SDK_PATH}")
message(STATUS "")
message(STATUS "Build commands:")
message(STATUS "  mkdir build && cd build")
message(STATUS "  cmake ..")
message(STATUS "  cmake --build . --config Release")
message(STATUS "")
