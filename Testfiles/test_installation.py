#!/usr/bin/env python3
"""Test OT Asset Manager Dependencies"""

import sys
import importlib.util


def test_import(package_name, import_statement, required_version=None):
    try:
        # Execute the import
        exec(import_statement)

        # Check version if specified
        if required_version and '.' in import_statement:
            module_name = import_statement.split()[-1]
            module = sys.modules.get(module_name) or importlib.import_module(module_name)
            if hasattr(module, '__version__'):
                version = module.__version__
                print(f"✅ {package_name} {version} - OK")
            else:
                print(f"✅ {package_name} - OK")
        else:
            print(f"✅ {package_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name} - FAILED: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {package_name} - Warning: {e}")
        return True  # Still count as success for optional features


def main():
    print("🔍 Testing OT Asset Manager Dependencies")
    print("=" * 60)

    # Core GUI Framework
    print("\n🖥️  GUI Framework:")
    gui_tests = [
        ("PyQt6 Core", "from PyQt6.QtCore import QObject"),
        ("PyQt6 Widgets", "from PyQt6.QtWidgets import QApplication, QMainWindow"),
        ("PyQt6 GUI", "from PyQt6.QtGui import QFont, QPalette"),
    ]

    gui_passed = 0
    for name, import_stmt in gui_tests:
        if test_import(name, import_stmt):
            gui_passed += 1

    # Data Processing
    print("\n📊 Data Processing:")
    data_tests = [
        ("Pandas", "import pandas"),
        ("NumPy", "import numpy"),
        ("Matplotlib", "import matplotlib.pyplot"),
        ("NetworkX", "import networkx"),
    ]

    data_passed = 0
    for name, import_stmt in data_tests:
        if test_import(name, import_stmt):
            data_passed += 1

    # Database & Security
    print("\n🔐 Database & Security:")
    db_tests = [
        ("SQLAlchemy", "import sqlalchemy"),
        ("Cryptography", "import cryptography"),
        ("SQLite3", "import sqlite3"),
    ]

    db_passed = 0
    for name, import_stmt in db_tests:
        if test_import(name, import_stmt):
            db_passed += 1

    # C++ Integration
    print("\n⚙️  C++ Integration:")
    cpp_tests = [
        ("pybind11", "import pybind11"),
    ]

    cpp_passed = 0
    for name, import_stmt in cpp_tests:
        if test_import(name, import_stmt):
            cpp_passed += 1

    # Network Tools
    print("\n🌐 Network Tools:")
    network_tests = [
        ("Scapy", "import scapy"),
    ]

    network_passed = 0
    for name, import_stmt in network_tests:
        if test_import(name, import_stmt):
            network_passed += 1

    # Development Tools
    print("\n🛠️  Development Tools:")
    dev_tests = [
        ("Rich (CLI)", "import rich"),
        ("Pytest", "import pytest"),
        ("Black (Formatter)", "import black"),
    ]

    dev_passed = 0
    for name, import_stmt in dev_tests:
        if test_import(name, import_stmt):
            dev_passed += 1

    # Summary
    total_passed = gui_passed + data_passed + db_passed + cpp_passed + network_passed + dev_passed
    total_tests = len(gui_tests) + len(data_tests) + len(db_tests) + len(cpp_tests) + len(network_tests) + len(
        dev_tests)

    print("\n" + "=" * 60)
    print(f"📋 Summary: {total_passed}/{total_tests} packages working")
    print(f"🖥️  GUI Framework: {gui_passed}/{len(gui_tests)}")
    print(f"📊 Data Processing: {data_passed}/{len(data_tests)}")
    print(f"🔐 Database & Security: {db_passed}/{len(db_tests)}")
    print(f"⚙️  C++ Integration: {cpp_passed}/{len(cpp_tests)}")
    print(f"🌐 Network Tools: {network_passed}/{len(network_tests)}")
    print(f"🛠️  Development Tools: {dev_passed}/{len(dev_tests)}")

    if total_passed >= total_tests - 1:  # Allow for 1 optional failure
        print("\n🚀 READY TO BUILD OT ASSET MANAGER! 🚀")
        print("\nNext steps:")
        print("1. Create project structure")
        print("2. Build C++ scanner module")
        print("3. Run the application")
    else:
        print(f"\n⚠️  Need to fix {total_tests - total_passed} package(s)")

    return total_passed >= total_tests - 1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
