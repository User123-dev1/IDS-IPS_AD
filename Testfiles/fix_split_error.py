print("[*] Fixing line 1337 - empty separator error...")

with open("../src/gui/main_window.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the broken split - use Python's splitlines() instead
content = content.replace("subnet_lines = subnet_text.split('')", "subnet_lines = subnet_text.splitlines()")

# Also fix if it appears elsewhere
content = content.replace("subnet_text.split('')", "subnet_text.splitlines()")
content = content.replace("subnet_text.split('\\')", "subnet_text.splitlines()")

with open("../src/gui/main_window.py", "w", encoding="utf-8") as f:
    f.write(content)

print("[OK] Fixed! Changed to: subnet_lines = subnet_text.splitlines()")
print("[*] This properly splits by newlines without escaping issues")

