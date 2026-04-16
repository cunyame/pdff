#!/usr/bin/env python3
"""
Package the portal automator into a standalone executable
Works on both Windows and Linux
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    print("Checking for PyInstaller...")
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")

def create_executable():
    """Create standalone executable using PyInstaller"""
    print("\n" + "="*60)
    print("Building Standalone Executable")
    print("="*60 + "\n")
    
    # Determine platform
    if sys.platform.startswith('win'):
        platform = "windows"
        ext = ".exe"
    elif sys.platform.startswith('linux'):
        platform = "linux"
        ext = ""
    else:
        platform = "macos"
        ext = ""
    
    output_name = f"PortalAutomator_{platform}"
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable
        "--name", output_name,          # Output name
        "--clean",                      # Clean cache
        "--noconfirm",                  # Overwrite without asking
        "portal_automator.py"
    ]
    
    # Add icon if available
    if os.path.exists("icon.ico") and platform == "windows":
        cmd.extend(["--icon", "icon.ico"])
    
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ Executable created successfully!")
        
        # Show location
        exe_path = Path("dist") / (output_name + ext)
        if exe_path.exists():
            print(f"\nExecutable location: {exe_path.absolute()}")
            print(f"Size: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            # Create distribution folder
            dist_folder = Path("distribution")
            dist_folder.mkdir(exist_ok=True)
            
            # Copy executable
            shutil.copy2(exe_path, dist_folder / (output_name + ext))
            
            # Copy config file if it exists
            if Path("config.json").exists():
                shutil.copy2("config.json", dist_folder / "config.json")
            else:
                print("\nNote: config.json will be created on first run")
            
            # Create README for distribution
            readme_content = f"""
# Portal Automator - Standalone Version

## How to Use

1. **First Run**:
   - Double-click `{output_name}{ext}` to start the application
   - A default `config.json` will be created
   - A browser window will open

2. **Login**:
   - Manually login to your Samsung Knox portal
   - The automator is now ready to use

3. **Use Shortcuts**:
   - Press configured keyboard shortcuts to perform actions
   - Default shortcuts:
     - Ctrl+X+C → Open Attendance Portal
     - Ctrl+X+T → Open Time Off Request
     - Ctrl+X+P → Open Payroll
     - Ctrl+X+B → Open Benefits
     - Ctrl+X+S → Submit Quick Form
     - Ctrl+X+O → Open Profile

4. **Customize**:
   - Edit `config.json` to add/modify shortcuts
   - See documentation for advanced configuration

5. **Stop**:
   - Press ESC to stop the automator

## Requirements

- Google Chrome browser must be installed
- ChromeDriver will be downloaded automatically on first run

## Customizing Shortcuts

Edit `config.json`:

```json
{{
  "shortcuts": [
    {{
      "name": "Your Action Name",
      "keys": ["ctrl", "x", "yourkey"],
      "action": "navigate",
      "url": "/your-path"
    }}
  ]
}}
```

Action types:
- `navigate`: Go to a URL
- `click`: Click an element
- `type`: Type text into a field
- `execute_js`: Run JavaScript code

## Troubleshooting

- If browser doesn't start, ensure Chrome is installed
- If shortcuts don't work, check that config.json is valid JSON
- Run from terminal/command prompt to see error messages
"""
            
            with open(dist_folder / "README.txt", "w") as f:
                f.write(readme_content)
            
            print(f"\n✓ Distribution package created in: {dist_folder.absolute()}")
            print("\nPackage contents:")
            for item in dist_folder.iterdir():
                print(f"  - {item.name}")
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error creating executable: {e}")
        sys.exit(1)

def main():
    print("Portal Automator - Packaging Tool")
    print("="*60 + "\n")
    
    # Check if in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
    
    install_pyinstaller()
    create_executable()
    
    print("\n" + "="*60)
    print("Packaging Complete!")
    print("="*60)
    print("\nYou can now distribute the 'distribution' folder")
    print("Users won't need Python installed to run the executable!")

if __name__ == "__main__":
    main()
