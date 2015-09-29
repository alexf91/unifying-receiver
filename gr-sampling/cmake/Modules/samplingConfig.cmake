INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_SAMPLING sampling)

FIND_PATH(
    SAMPLING_INCLUDE_DIRS
    NAMES sampling/api.h
    HINTS $ENV{SAMPLING_DIR}/include
        ${PC_SAMPLING_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    SAMPLING_LIBRARIES
    NAMES gnuradio-sampling
    HINTS $ENV{SAMPLING_DIR}/lib
        ${PC_SAMPLING_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(SAMPLING DEFAULT_MSG SAMPLING_LIBRARIES SAMPLING_INCLUDE_DIRS)
MARK_AS_ADVANCED(SAMPLING_LIBRARIES SAMPLING_INCLUDE_DIRS)

