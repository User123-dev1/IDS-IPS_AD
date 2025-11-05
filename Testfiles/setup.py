"""
Setup script for building C++ extensions
Run: python setup.py build_ext --inplace
"""
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension
import pybind11

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "scanner_module",
        [
            "cpp_scanner/bindings/pybind11_wrapper.cpp",
            "cpp_scanner/bindings/scanner_interface.cpp",
            "cpp_scanner/src/network_scanner.cpp",
            "cpp_scanner/src/modbus_scanner.cpp",
            "cpp_scanner/src/opcua_scanner.cpp",
            "cpp_scanner/src/vulnerability_scanner.cpp",
            "cpp_scanner/src/security_manager.cpp",
        ],
        include_dirs=[
            "cpp_scanner/include",
            pybind11.get_cmake_dir() + "/../../../include",
        ],
        language='c++',
        cxx_std=17,
    ),
]

setup(
    name="ot-asset-manager",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
)
