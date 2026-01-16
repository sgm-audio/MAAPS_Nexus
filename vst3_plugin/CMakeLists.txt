cmake_minimum_required(VERSION 3.14)

project(MAAPSNexusVST3 VERSION 1.0.0)

# C++17 required
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# VST3 SDK path (set this to your VST3 SDK location)
set(VST3_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../vst3sdk" CACHE PATH "Path to VST3 SDK")

if(NOT EXISTS "${VST3_SDK_PATH}")
    message(FATAL_ERROR "VST3 SDK not found at ${VST3_SDK_PATH}. Please set VST3_SDK_PATH.")
endif()

# Add VST3 SDK
add_subdirectory(${VST3_SDK_PATH} ${CMAKE_CURRENT_BINARY_DIR}/vst3sdk)

# Plugin target
set(TARGET maaps_nexus_vst3)

set(SOURCES
    maaps_nexus_vst3.cpp
    maaps_nexus_vst3.h
)

# Create VST3 plugin
smtg_add_vst3plugin(${TARGET} ${SOURCES})

# Plugin properties
set_target_properties(${TARGET} PROPERTIES
    BUNDLE TRUE
    OUTPUT_NAME "MAAPS_Nexus"
)

# Link against VST3 SDK
target_link_libraries(${TARGET} PRIVATE
    sdk
    pluginterfaces
)

# Platform-specific settings
if(UNIX AND NOT APPLE)
    # Linux
    target_link_libraries(${TARGET} PRIVATE
        pthread
        rt  # For shared memory
    )
elseif(APPLE)
    # macOS
    target_link_libraries(${TARGET} PRIVATE
        "-framework CoreFoundation"
    )
elseif(WIN32)
    # Windows
    # Will need to implement named pipes for Windows
endif()

# Include directories
target_include_directories(${TARGET} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${VST3_SDK_PATH}
)

# Compiler warnings
if(MSVC)
    target_compile_options(${TARGET} PRIVATE /W4)
else()
    target_compile_options(${TARGET} PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Installation
install(TARGETS ${TARGET}
    DESTINATION "$ENV{HOME}/.vst3"  # Linux/macOS
    # DESTINATION "C:/Program Files/Common Files/VST3"  # Windows
)

# Build information
message(STATUS "Building MAAPS Nexus VST3 Plugin")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  VST3 SDK: ${VST3_SDK_PATH}")
message(STATUS "  Install path: $ENV{HOME}/.vst3")
