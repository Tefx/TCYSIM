from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
from platform import system
import os
import shutil


if os.path.exists("tcysim/include"):
    shutil.rmtree("tcysim/include")
shutil.copytree("libtcy/include", "tcysim/include")

if system() == "Windows":
    extra_compile_args = [
        "/fp:fast",
        "/arch:AVX512",
        "/favor:INTEL64",
        "/O2", "/Ob2", "/GL",
        ]
    extra_link_args = [
        "/MACHINE:X64",
        "/LTCG",
        ]
    library_dir = "libtcy/msvc/Release"
else:
    extra_compile_args = [
        '-Ofast',
        '-march=native',
        '-ffast-math',
        '-fforce-addr',
        '-fprefetch-loop-arrays',
        "-flto",
        ]
    extra_link_args = []
    library_dir = "libtcy/cmake-build-debug"

extensions = [
    Extension(
        name="tcysim.libc.*",
        sources=["tcysim/libc/*.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        libraries=["tcy"],
        library_dirs=[os.path.abspath(library_dir)],
        include_dirs=[os.path.abspath("libtcy/include")]
        ),
    Extension(
        name="tcysim.framework.motion.*",
        sources=["tcysim/framework/motion/*.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        ),
    Extension(
        name="tcysim.framework.operation.*",
        sources=["tcysim/framework/operation/*.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        ),
    Extension(
        name="tcysim.framework.probe.*",
        sources=["tcysim/framework/probe/*.pyx",
                 ],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        ),
    Extension(
        name="tcysim.utils.*",
        sources=["tcysim/utils/*.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        ),
    Extension(
        name="tcysim.utils.set.*",
        sources=["tcysim/utils/set/*.pyx"],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        libraries=["tcy"],
        library_dirs=[os.path.abspath(library_dir)],
        include_dirs=[os.path.abspath("libtcy/include")]
        ),
    ]

setup(name="tcysim",
      packages=find_packages() + ["tcysim.include"],
      version=0.5,
      setup_requires=["Cython"],
      author="Tefx",
      author_email="zhaomeng.zhu@gmail.com",
      ext_modules=cythonize(extensions,
                            compiler_directives={
                                "profile":          False,
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
          "": ["*.pxd"],
          "tcysim.include": ["*.h"],
          },
      install_requires=["pesim>=0.9"],
      extras_require={
          "analysis": ["msgpack>=1", "plotly>=4.5"],
          }
      )
