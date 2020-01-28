from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy
import os
from platform import system

if system() == "Windows":
    extra_compile_args = [
        "-fp:fast",
        "/arch:AVX2",
        "/favor:INTEL64",
        "/Ox", "/Ob2", "/Oi", "/Ot", "/Oy", "/GL", "/GT",
        ]
    library_dir = "libtcy/msvc/Release"
else:
    extra_compile_args = [
        '-Ofast',
        '-march=native',
        '-ffast-math',
        '-funroll-loops',
        ]
    library_dir = "libtcy/cmake-build-debug"

extensions = [
    Extension(
        name="tcysim.libc.*",
        sources=["tcysim/libc/*.pyx"],
        extra_compile_args=extra_compile_args,
        libraries=["tcy"],
        library_dirs=[os.path.abspath(library_dir)],
        include_dirs=[os.path.abspath("libtcy/src/core")]
        ),
    Extension(
        name="tcysim.framework.motion.*",
        sources=["tcysim/framework/motion/*.pyx"],
        extra_compile_args=extra_compile_args,
        ),
    Extension(
        name="tcysim.framework.operation.*",
        sources=["tcysim/framework/operation/*.pyx"],
        extra_compile_args=extra_compile_args,
        ),
    Extension(
        name="tcysim.framework.probe.*",
        sources=["tcysim/framework/probe/*.pyx"],
        extra_compile_args=extra_compile_args,
        ),
    Extension(
        name="tcysim.utils.*",
        sources=["tcysim/utils/*.pyx"],
        extra_compile_args=extra_compile_args,
        ),
    ]

setup(ext_modules=cythonize(extensions,
                            compiler_directives={
                                "profile":          True,
                                "linetrace":        False,
                                "cdivision":        True,
                                "boundscheck":      False,
                                "wraparound":       False,
                                "initializedcheck": False,
                                "language_level":   3,
                                },
                            annotate=True,
                            ),
      package_data={
          "tcysim.libc.*":                ["tcysim/libc/*.pyx"],
          "tcysim.framework.motion.*":    ["tcysim/framework/motion/*.pyx"],
          "tcysim.framework.operation.*": ["tcysim/framework/operation/*.pyx"],
          "tcysim.framework.probe.*":     ["tcysim/framework/probe/*.pyx"],
          "tcysim.utils.*":               ["tcysim/utils/*.pyx"],
          }
      )
