cmake_minimum_required(VERSION 3.16)
project(unitree_sdk2_examples LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(UNITREE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")

if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64|arm64")
  set(UNITREE_ARCH "aarch64")
else()
  set(UNITREE_ARCH "x86_64")
endif()

set(UNITREE_LIB "${UNITREE_ROOT}/lib/${UNITREE_ARCH}/libunitree_sdk2.a")
set(THIRDPARTY_LIB_DIR "${UNITREE_ROOT}/thirdparty/lib/${UNITREE_ARCH}")

if(NOT EXISTS "${UNITREE_LIB}")
  message(FATAL_ERROR "Missing SDK library: ${UNITREE_LIB}")
endif()
if(NOT EXISTS "${THIRDPARTY_LIB_DIR}/libddsc.so")
  message(FATAL_ERROR "Missing CycloneDDS: ${THIRDPARTY_LIB_DIR}/libddsc.so")
endif()
if(NOT EXISTS "${THIRDPARTY_LIB_DIR}/libddscxx.so")
  message(FATAL_ERROR "Missing CycloneDDS C++: ${THIRDPARTY_LIB_DIR}/libddscxx.so")
endif()

find_package(Threads REQUIRED)

add_library(ddsc SHARED IMPORTED GLOBAL)
set_target_properties(ddsc PROPERTIES
  IMPORTED_LOCATION "${THIRDPARTY_LIB_DIR}/libddsc.so"
  INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_ROOT}/thirdparty/include"
  INTERFACE_LINK_LIBRARIES Threads::Threads
  IMPORTED_NO_SONAME TRUE
)

add_library(ddscxx SHARED IMPORTED GLOBAL)
set_target_properties(ddscxx PROPERTIES
  IMPORTED_LOCATION "${THIRDPARTY_LIB_DIR}/libddscxx.so"
  INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_ROOT}/thirdparty/include;${UNITREE_ROOT}/thirdparty/include/ddscxx"
  INTERFACE_LINK_LIBRARIES Threads::Threads
  IMPORTED_NO_SONAME TRUE
)

add_library(unitree_sdk2 STATIC IMPORTED GLOBAL)
set_target_properties(unitree_sdk2 PROPERTIES
  IMPORTED_LOCATION "${UNITREE_LIB}"
  INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_ROOT}/include;${UNITREE_ROOT}/thirdparty/include"
  INTERFACE_LINK_LIBRARIES "ddsc;ddscxx;Threads::Threads"
  LINKER_LANGUAGE CXX
)

add_subdirectory(example)
