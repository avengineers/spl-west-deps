# There is no cmake_language(DEFER ...) here, unlike the other spl-core extensions.
# The dependency sources must exist before variants/${VARIANT}/parts.cmake calls
# spl_add_component(), so this runs while it is being included, not at the end of
# the CMake configuration. Include it before the variant parts.

set(WEST_DEPS_RUNNER spl_west_deps)
set(WEST_DEPS_CMAKE_FILE ${CMAKE_BINARY_DIR}/spl_west_deps.cmake)

execute_process(
    COMMAND ${WEST_DEPS_RUNNER} generate --project-root-dir ${CMAKE_SOURCE_DIR} --variant ${VARIANT} --output-file ${WEST_DEPS_CMAKE_FILE}
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
