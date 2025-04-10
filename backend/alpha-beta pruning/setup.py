from setuptools import setup, Extension
import pybind11
import sys
import os

# Determine compiler arguments based on the platform
compiler_args = []
link_args = []

if sys.platform == 'darwin':  # macOS
    compiler_args = ['-std=c++14', '-stdlib=libc++']
    link_args = ['-stdlib=libc++']
elif sys.platform == 'win32':  # Windows
    compiler_args = ['/std:c++14']
else:  # Linux and others
    compiler_args = ['-std=c++14']

ext_modules = [
    Extension(
        'hex_cpp',
        ['alpha-beta-pruning.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=compiler_args,
        extra_link_args=link_args,
    ),
]

setup(
    name='hex_cpp',
    version='0.0.1',
    author='HEX Game',
    author_email='your.email@example.com',
    description='C++ implementation of Hex game with alpha-beta pruning',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    python_requires='>=3.6',
)
