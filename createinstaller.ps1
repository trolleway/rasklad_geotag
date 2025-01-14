# Define the path to the Python script
$scriptPath = "c:/Users/troll/rasklad_geotag/main.py"

# Define the output directory for the build
$outputDir = "c:/Users/troll/rasklad_geotag/dist"

# Define the path to the Visual C++ runtime DLLs
$vcRuntimePath = "C:/Windows/System32"

# List of Visual C++ runtime DLLs to include
$vcRuntimeDlls = @(
    "msvcp140.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll"
)

# Copy Visual C++ runtime DLLs to the output directory
foreach ($dll in $vcRuntimeDlls) {
    $sourcePath = Join-Path -Path $vcRuntimePath -ChildPath $dll
    $destinationPath = Join-Path -Path $outputDir -ChildPath $dll
    Copy-Item -Path $sourcePath -Destination $destinationPath -Force
}

# Run pyinstaller with the necessary options
pyinstaller --onefile --add-data "$vcRuntimePath\msvcp140.dll;." --add-data "$vcRuntimePath\vcruntime140.dll;." --add-data "$vcRuntimePath\vcruntime140_1.dll;." --distpath $outputDir $scriptPath