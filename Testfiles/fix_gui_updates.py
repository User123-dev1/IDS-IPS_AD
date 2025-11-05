import re

print("[*] Fixing GUI updates for parallel scanning...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the parallel scanning section and ensure proper GUI updates
pattern = r'(with ThreadPoolExecutor\(max_workers=max_workers\) as executor:.*?for future in as_completed\(future_to_ip\):)'

# Check if QApplication.processEvents() is being called frequently enough
if 'QApplication.processEvents()' in content:
    print("[*] Found QApplication.processEvents() - adjusting frequency...")
    
    # Make sure we call processEvents after EVERY result, not just every 10
    content = content.replace(
        "if completed % 10 == 0:\n                            QApplication.processEvents()",
        "# Update GUI after every device found\n                        QApplication.processEvents()"
    )
    
    # Also ensure it's called in the right place (outside the lock)
    content = re.sub(
        r'(\s+)QApplication\.processEvents\(\)\s+except Exception',
        r'\1    except Exception',
        content
    )

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] GUI update frequency increased")

