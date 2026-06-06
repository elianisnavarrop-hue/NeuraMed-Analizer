import subprocess
from pathlib import Path

ui_files = list(Path("view").glob("*.ui"))

for ui_file in ui_files:
    py_file = ui_file.with_name("ui_" + ui_file.stem + ".py")
    print(f"Converting {ui_file} -> {py_file}")
    subprocess.run(["pyuic6", str(ui_file), "-o", str(py_file)], check=True)

print("✅ All .ui files converted!")