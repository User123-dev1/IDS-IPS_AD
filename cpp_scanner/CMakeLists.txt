cmake_minimum_required(VERSION 3.18)
project(ot_scanner)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Security flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fstack-protector-strong -D_FORTIFY_SOURCE=2")

# Find Python and pybind11
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 REQUIRED)

# Find Qt for Modbus support
find_package(Qt6 COMPONENTS Core Network SerialBus QUIET)

# Include directories
include_directories(include)

# Source files
set(SCANNER_SOURCES
    src/network_scanner.cpp
    src/modbus_scanner.cpp
    src/opcua_scanner.cpp
    src/vulnerability_scanner.cpp
    src/security_manager.cpp
)

# Create shared library
add_library(scanner_core SHARED ${SCANNER_SOURCES})

# Create Python module
pybind11_add_module(scanner_module
    bindings/pybind11_wrapper.cpp
    bindings/scanner_interface.cpp
    ${SCANNER_SOURCES}
)

# Link libraries
if(Qt6_FOUND)
    target_link_libraries(scanner_core Qt6::Core Qt6::Network Qt6::SerialBus)
    target_link_libraries(scanner_module Qt6::Core Qt6::Network Qt6::SerialBus)
endif()

target_compile_definitions(scanner_module PRIVATE VERSION_INFO=${VERSION_INFO})
