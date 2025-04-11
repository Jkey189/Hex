from setuptools import setup, Extension
import pybind11

setup(
    name='hex_cpp',
    version='0.2',
    ext_modules=[
        Extension(
            'hex_cpp',
            ['alpha-beta-pruning.cpp'],
            include_dirs=[pybind11.get_include()],
            language='c++',
            extra_compile_args=['-std=c++14', '-O3', '-DNDEBUG'],  # Changed from c++11 to c++14
            extra_link_args=['-O3']
        ),
    ],
    python_requires='>=3.6',
    description='Optimized Alpha-Beta Pruning for Hex Game',
)
