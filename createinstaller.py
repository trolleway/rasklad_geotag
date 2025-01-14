import os
import shutil
import subprocess
import sys

# Define the path to the Python script
script_path = "c:/Users/troll/rasklad_geotag/main.py"

# Define the output directory for the build
output_dir = "c:/Users/troll/rasklad_geotag/dist"

# Define the path to the Visual C++ runtime DLLs
vc_runtime_path = "C:/Windows/System32"

# List of Visual C++ runtime DLLs to include
vc_runtime_dlls = ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"]

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Copy Visual C++ runtime DLLs to the output directory
for dll in vc_runtime_dlls:
    source_path = os.path.join(vc_runtime_path, dll)
    destination_path = os.path.join(output_dir, dll)
    shutil.copy(source_path, destination_path)

# Run pyinstaller with the necessary options
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--add-data",
        f"{os.path.join(vc_runtime_path, 'msvcp140.dll')};.",
        "--add-data",
        f"{os.path.join(vc_runtime_path, 'vcruntime140.dll')};.",
        "--add-data",
        f"{os.path.join(vc_runtime_path, 'vcruntime140_1.dll')};.",
        "--distpath",
        output_dir,
        script_path,
    ]
)
