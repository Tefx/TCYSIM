cmake_minimum_required(VERSION 3.14)
project(tcy C)

if (MSVC)
    set(CMAKE_C_FLAGS "/fp:fast /arch:AVX512 /favor:INTEL64 /O2 /Ob2 /GL")
    set(CMAKE_EXE_LINKER_FLAGS "/MACHINE:X64 /LTCG")
else (MSVC)
    set(CMAKE_C_FLAGS "-Ofast -Wall -Wextra -march=native -ffast-math -fforce-addr -fprefetch-loop-arrays -flto")
endif (MSVC)

set(CMAKE_C_STANDARD 11)

add_library(tcy
        include/define.h include/error.h include/block.h include/box.h include/path.h include/cd.h include/idx_set.h
        src/define.c src/block.c src/box.c src/path.c src/cd.c src/idx_set.c)