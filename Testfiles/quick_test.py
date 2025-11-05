"""Quick dependency check"""

print("🔍 Testing OT Asset Manager Dependencies...")

try:
    from PyQt6.QtWidgets import QApplication
    print("✅ PyQt6 - OK")
except ImportError as e:
    print(f"❌ PyQt6 - FAILED: {e}")

try:
    import pandas
    print(f"✅ Pandas {pandas.__version__} - OK")
except ImportError as e:
    print(f"❌ Pandas - FAILED: {e}")

try:
    import numpy
    print(f"✅ NumPy {numpy.__version__} - OK")
except ImportError as e:
    print(f"❌ NumPy - FAILED: {e}")

try:
    import matplotlib
    print(f"✅ Matplotlib {matplotlib.__version__} - OK")
except ImportError as e:
    print(f"❌ Matplotlib - FAILED: {e}")

try:
    import networkx
    print(f"✅ NetworkX {networkx.__version__} - OK")
except ImportError as e:
    print(f"❌ NetworkX - FAILED: {e}")

try:
    import pybind11
    print(f"✅ pybind11 {pybind11.__version__} - OK")
except ImportError as e:
    print(f"❌ pybind11 - FAILED: {e}")

print("\n🚀 Ready to build OT Asset Manager!")
