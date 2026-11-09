# There is no cmake_language(DEFER ...) here, unlike the other spl-core extensions.
# The dependency sources must exist before variants/${VARIANT}/parts.cmake calls
# spl_add_component(), so this runs while it is being included, not at the end of
# the CMake configuration. Include it before the variant parts.

set(WEST_DEPS_RUNNER spl_west_deps)
set(WEST_DEPS_CMAKE_FILE ${CMAKE_BINARY_DIR}/spl_west_deps.cmake)

# Workspace for west install.
# Project-relative or absolute; set via -D or set() before inclusion.
# Empty: use environment variable SPL_WEST_DEPS_WORKSPACE_DIR, then build/modules.
# Cache only if undefined to preserve normal variables regardless of CMP0126.
if(NOT DEFINED SPL_WEST_DEPS_WORKSPACE_DIR)
    set(SPL_WEST_DEPS_WORKSPACE_DIR "" CACHE STRING
        "Where west installs the dependencies (relative to the project root, or absolute). Empty: environment variable SPL_WEST_DEPS_WORKSPACE_DIR, else build/modules.")
endif()

set(WEST_DEPS_ARGS generate --project-root-dir ${CMAKE_SOURCE_DIR} --variant ${VARIANT} --output-file ${WEST_DEPS_CMAKE_FILE})
if(NOT SPL_WEST_DEPS_WORKSPACE_DIR STREQUAL "")
    list(APPEND WEST_DEPS_ARGS --workspace-dir "${SPL_WEST_DEPS_WORKSPACE_DIR}")
endif()

execute_process(
    COMMAND ${WEST_DEPS_RUNNER} ${WEST_DEPS_ARGS}
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    OUTPUT_VARIABLE output
    ERROR_VARIABLE error
    RESULT_VARIABLE result
)

# print stdout/stderr
message(STATUS "STDERR: ${error}")
message(STATUS "STDOUT: ${output}")

# check if the command succeeded
if(result)
    message(FATAL_ERROR "Installation of the West Dependencies extension failed.")
else()
    message(STATUS "Installation of the West Dependencies extension was successful.")
endif()

# include the generated cmake file
include(${WEST_DEPS_CMAKE_FILE})
