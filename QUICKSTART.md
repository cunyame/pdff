# Quick Start Guide

## Windows Users

1. Double-click `setup_windows.bat` and wait for it to finish
2. Double-click `run_windows.bat`
3. Login to Samsung Knox portal manually in the browser that opens
4. Press keyboard shortcuts to automate actions!

Default shortcuts:
- Ctrl+X+C → Attendance
- Ctrl+X+T → Time Off
- Ctrl+X+P → Payroll
- Ctrl+X+B → Benefits

Press ESC to stop.

## Raspberry Pi / Linux Users

1. Open terminal in this folder
2. Run: `chmod +x setup_linux.sh && ./setup_linux.sh`
3. Run: `chmod +x run_linux.sh && ./run_linux.sh`
4. Login to Samsung Knox portal manually in the browser that opens
5. Press keyboard shortcuts to automate actions!

Press ESC to stop.

## Customize

Edit `config.json` to change shortcuts or add new ones.
See `README.md` for full documentation.

## Create Standalone App

1. Activate environment:
   - Windows: `venv\Scripts\activate.bat`
   - Linux: `source venv/bin/activate`
2. Run: `python package.py`
3. Find executable in `distribution/` folder

Share the distribution folder - users won't need Python!
