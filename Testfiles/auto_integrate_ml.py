"""Auto-integrate ML Widget into existing GUI"""
import os
import re
from pathlib import Path

def find_main_gui():
    """Find the main GUI file"""
    gui_path = Path("../src/gui")
    candidates = [
        "main_window.py", "main.py", "app.py", 
        "network_monitor.py", "monitor.py", "gui.py"
    ]
    
    for candidate in candidates:
        file_path = gui_path / candidate
        if file_path.exists():
            return file_path
    
    # Search for any file with QMainWindow or QTabWidget
    for py_file in gui_path.glob("*.py"):
        content = py_file.read_text(encoding='utf-8')
        if 'QMainWindow' in content or 'QTabWidget' in content:
            return py_file
    
    return None

def backup_file(file_path):
    """Create backup of original file"""
    backup_path = file_path.with_suffix('.py.backup')
    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"[BACKUP] Created: {backup_path}")
    return backup_path

def integrate_ml_widget(gui_file):
    """Add ML widget to GUI file"""
    print(f"\n[INTEGRATE] Processing: {gui_file}")
    
    content = gui_file.read_text(encoding='utf-8')
    original_content = content
    
    # Check if already integrated
    if 'MLAnomalyWidget' in content or 'ml_anomaly_widget' in content:
        print("[SKIP] ML widget already integrated!")
        return False
    
    # Add import
    import_line = "from gui.ml_anomaly_widget import MLAnomalyWidget\n"
    
    # Find import section
    if 'from PyQt6.QtWidgets import' in content or 'from PyQt5.QtWidgets import' in content:
        # Add after last PyQt import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from PyQt') and 'import' in line:
                last_import_idx = i
        lines.insert(last_import_idx + 1, import_line.strip())
        content = '\n'.join(lines)
        print("[OK] Added import")
    
    # Find tab widget creation and add ML tab
    if 'QTabWidget' in content:
        # Find addTab calls
        pattern = r'(self\.\w+\.addTab\([^)]+\))'
        matches = list(re.finditer(pattern, content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            
            ml_tab_code = """
        
        # ML Anomaly Detection Tab
        self.ml_tab = MLAnomalyWidget(self)
        self.tabs.addTab(self.ml_tab, "🧠 ML Detection")"""
            
            content = content[:insert_pos] + ml_tab_code + content[insert_pos:]
            print("[OK] Added ML tab")
    
    if content != original_content:
        backup_file(gui_file)
        gui_file.write_text(content, encoding='utf-8')
        print("[SUCCESS] Integration complete!")
        return True
    else:
        print("[WARNING] Could not find integration point")
        return False

def main():
    print("\n" + "="*70)
    print("  ML Widget Auto-Integration")
    print("="*70)
    
    # Find GUI file
    print("\n[1/3] Finding main GUI file...")
    gui_file = find_main_gui()
    
    if not gui_file:
        print("[ERROR] Could not find main GUI file!")
        print("\nPlease manually integrate using ML_WIDGET_INTEGRATION.txt")
        return
    
    print(f"[OK] Found: {gui_file}")
    
    # Integrate
    print("\n[2/3] Integrating ML widget...")
    success = integrate_ml_widget(gui_file)
    
    if success:
        print("\n[3/3] Testing...")
        print("\n" + "="*70)
        print("  ✓ INTEGRATION COMPLETE!")
        print("="*70)
        print(f"\nML widget added to: {gui_file}")
        print(f"Backup saved as: {gui_file.with_suffix('.py.backup')}")
        print("\nTo test:")
        print(f"  python {gui_file}")
        print("\nLook for the '🧠 ML Detection' tab!")
    else:
        print("\n" + "="*70)
        print("  MANUAL INTEGRATION REQUIRED")
        print("="*70)
        print("\nSee ML_WIDGET_INTEGRATION.txt for instructions")
        print("\nYour GUI structure:")
        content = gui_file.read_text(encoding='utf-8')
        
        if 'QTabWidget' in content:
            print("  • Uses QTabWidget - Add as new tab")
        if 'QMainWindow' in content:
            print("  • Uses QMainWindow - Add to central widget")
        if 'QDockWidget' in content:
            print("  • Uses dock widgets - Add as new dock")

if __name__ == "__main__":
    main()
