cmake_minimum_required(VERSION 3.12)

project(quantiv_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


find_package(Python COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)


include_directories(include)

set(SOURCE_FILES
    src/bindings.cpp
    src/binomial.cpp
    src/black_scholes.cpp
    src/merton_model.cpp 
)

pybind11_add_module(quantiv_engine ${SOURCE_FILES})

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(quantiv_engine PRIVATE -O3 -march=native -ffast-math)
elseif(MSVC)
    target_compile_options(quantiv_engine PRIVATE /O2 /fp:fast)
endif()