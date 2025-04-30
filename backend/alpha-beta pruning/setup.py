from setuptools import setup, Extension
import pybind11
import sysconfig
import os
import sys

# Get Python information for linking
python_include = sysconfig.get_path('include')
python_lib = sysconfig.get_config_var('LIBDIR')
python_version = sysconfig.get_config_var('VERSION')
python_framework = sysconfig.get_config_var('PYTHONFRAMEWORK')

# For macOS, we need to link against the Python framework
if sys.platform == 'darwin':
    extra_link_args = []
    if python_framework:
        # Framework path for macOS
        framework_path = os.path.dirname(os.path.dirname(python_lib))
        extra_link_args = [
            '-framework', python_framework,
            '-F', framework_path,
        ]
        if python_version:
            extra_link_args.extend([
                f'-L{python_lib}',
                f'-lpython{python_version}'
            ])
    else:
        # Non-framework Python (homebrew, etc.)
        extra_link_args = [
            f'-L{python_lib}',
            f'-lpython{python_version}'
        ]
else:
    # Linux/Windows
    extra_link_args = [
        f'-L{python_lib}',
        f'-lpython{python_version}'
    ]

setup(
    name='hex_cpp',
    version='0.2',
    ext_modules=[
        Extension(
            'hex_cpp',
            ['alpha-beta-pruning.cpp'],
            include_dirs=[
                pybind11.get_include(),
                python_include
            ],
            language='c++',
            extra_compile_args=['-std=c++17', '-O3', '-DNDEBUG'],
            extra_link_args=extra_link_args
        ),
    ],
    python_requires='>=3.6',
    description='Optimized Alpha-Beta Pruning for Hex Game',
)
