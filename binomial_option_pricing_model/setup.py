"""
Setup script for building the C++ options engine extension
"""
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import pybind11

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path"""
    def __str__(self):
        return pybind11.get_include()

if sys.platform == 'win32':
    extra_compile_args = ['/std:c++17', '/O2']
else:
    extra_compile_args = ['-std=c++17', '-O3', '-march=native']

ext_modules = [
    Extension(
        'binomial_engine',
        ['binomial_engine.cpp'],
        include_dirs=[
            get_pybind_include(),
        ],
        language='c++',
        extra_compile_args=extra_compile_args,
    ),
]

setup(
    name='binomial_engine',
    version='1.0.0',
    author='Abstract Quantiv Team',
    description='High-performance options pricing engine',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    zip_safe=False,
)