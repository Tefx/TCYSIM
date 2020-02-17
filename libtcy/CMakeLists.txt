cmake_minimum_required(VERSION 3.14)
project(tcy C)

if (MSVC)
    set(CMAKE_C_FLAGS "/fp:fast /arch:AVX512 /favor:INTEL64 /O2 /Ob2 /GL")
    set(CMAKE_EXE_LINKER_FLAGS "/MACHINE:X64 /LTCG")
else (MSVC)
    set(CMAKE_C_FLAGS "-Ofast -Wall -Wextra -march=native -ffast-math -fforce-addr -fprefetch-loop-arrays -flto")
endif (MSVC)

set(CMAKE_C_STANDARD 11)

add_library(tcy SHARED src/core/define.h src/core/block.c src/core/block.h src/core/error.h src/core/box.c src/core/box.h src/core/path.c src/core/path.h src/core/cd.c src/core/cd.h src/core/define.c)