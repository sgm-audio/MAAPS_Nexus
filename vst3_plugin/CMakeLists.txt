cmake_minimum_required(VERSION 3.15)
project(MAAPSNexusVST3)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# VST3 SDK path - adjust this to your VST3 SDK location
if(NOT DEFINED VST3_SDK_ROOT)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../vst3sdk")
        set(VST3_SDK_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../vst3sdk")
    elseif(EXISTS "$ENV{VST3_SDK_ROOT}")
        set(VST3_SDK_ROOT "$ENV{VST3_SDK_ROOT}")
    else()
        message(FATAL_ERROR "VST3 SDK not found. Set VST3_SDK_ROOT environment variable or place SDK in ../vst3sdk")
    endif()
endif()

message(STATUS "Using VST3 SDK: ${VST3_SDK_ROOT}")

# Add VST3 SDK
add_subdirectory(${VST3_SDK_ROOT} ${CMAKE_CURRENT_BINARY_DIR}/vst3sdk)

# MAAPS Nexus VST3 Plugin
set(PLUGIN_NAME "MAAPSNexus")

# Plugin sources
set(plugin_sources
    maaps_nexus_vst3.h
    # Add .cpp file when created
)

# Create VST3 plugin target
smtg_add_vst3plugin(${PLUGIN_NAME}
    ${plugin_sources}
)

# Plugin identifiers (generate your own unique IDs)
target_compile_definitions(${PLUGIN_NAME} PRIVATE
    $<$<CONFIG:Debug>:DEBUG=1>
    $<$<CONFIG:Release>:RELEASE=1>
)

# Include directories
target_include_directories(${PLUGIN_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${VST3_SDK_ROOT}
)

# Platform-specific settings
if(WIN32)
    # Windows: No additional libraries needed for shared memory
    target_compile_definitions(${PLUGIN_NAME} PRIVATE _WIN32)
elseif(APPLE)
    # macOS: Add CoreFoundation and other system frameworks
    target_link_libraries(${PLUGIN_NAME} PRIVATE
        "-framework CoreFoundation"
        "-framework CoreAudio"
        "-framework AudioUnit"
        "-framework AudioToolbox"
    )
elseif(UNIX)
    # Linux: Add real-time library for shared memory
    target_link_libraries(${PLUGIN_NAME} PRIVATE
        rt
        pthread
    )
endif()

# Set output directory
set_target_properties(${PLUGIN_NAME} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/VST3"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/VST3"
)

# Installation
if(WIN32)
    set(VST3_INSTALL_DIR "$ENV{CommonProgramFiles}/VST3")
elseif(APPLE)
    set(VST3_INSTALL_DIR "~/Library/Audio/Plug-Ins/VST3")
else()
    set(VST3_INSTALL_DIR "~/.vst3")
endif()

install(TARGETS ${PLUGIN_NAME}
    DESTINATION ${VST3_INSTALL_DIR}
)

message(STATUS "VST3 plugin will be installed to: ${VST3_INSTALL_DIR}")

# Build instructions
message(STATUS "")
message(STATUS "========================================")
message(STATUS "MAAPS Nexus VST3 Build Configuration")
message(STATUS "========================================")
message(STATUS "Plugin Name: ${PLUGIN_NAME}")
message(STATUS "VST3 SDK: ${VST3_SDK_ROOT}")
message(STATUS "Install Directory: ${VST3_INSTALL_DIR}")
message(STATUS "")
message(STATUS "To build:")
message(STATUS "  mkdir build && cd build")
message(STATUS "  cmake ..")
message(STATUS "  cmake --build .")
message(STATUS "")
message(STATUS "To install:")
message(STATUS "  cmake --install .")
message(STATUS "========================================")
