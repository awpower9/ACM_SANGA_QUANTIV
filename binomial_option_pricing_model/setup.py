from setuptools import setup, Extension
import sys
import setuptools

# 1. Helper class to find the pybind11 include path
class get_pybind_include(object):
    def __str__(self):
        import pybind11
        return pybind11.get_include()
    
c_args = ['-std=c++17', '-O3']
if sys.platform == 'darwin':
    c_args += ['-mmacosx-version-min=10.15']

ext_modules = [Extension(
        'quantiv_engine', 
        ['src/bindings.cpp','src/black_scholes.cpp','src/binomial.cpp','src/merton_model.cpp' ],
        include_dirs=['include',get_pybind_include(),get_pybind_include()],
        language='c++'
    ),
]

setup(
    name='quantiv_engine',
    version='1.0.0',
    author='Quantiv Team',
    description='High-Performance Option Pricing Engine (Binomial + Black-Scholes)',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0', 'dash', 'pandas', 'yfinance'],
    setup_requires=['pybind11>=2.6.0'],
    zip_safe=False,
)