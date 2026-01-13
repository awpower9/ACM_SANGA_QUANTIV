cmake_minimum_required(VERSION 3.12)
project(binomial_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python and pybind11
find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

# Create the Python module
pybind11_add_module(binomial_engine binomial_engine.cpp)

# Set output directory
set_target_properties(binomial_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Optimization flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(binomial_engine PRIVATE -O3 -march=native -ffast-math)
elseif(MSVC)
    target_compile_options(binomial_engine PRIVATE /O2 /fp:fast)
endif()

# Installation
install(TARGETS binomial_engine
    LIBRARY DESTINATION ${Python_SITEARCH}
)