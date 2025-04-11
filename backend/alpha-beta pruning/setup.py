from setuptools import setup, Extension
import pybind11

setup(
    name='hex_cpp',
    version='0.1',
    ext_modules=[
        Extension(
            'hex_cpp',
            ['alpha-beta-pruning.cpp'],
            include_dirs=[pybind11.get_include()],
            language='c++',
            extra_compile_args=['-std=c++11', '-O3'],
        ),
    ]
)
