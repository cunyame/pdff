# Samsung Knox Portal Automator

A keyboard shortcut automation tool for navigating the Samsung Knox employee portal efficiently. This tool allows you to trigger common actions with custom keyboard shortcuts **after** you've manually logged in.

## 🎯 Features

- **Custom Keyboard Shortcuts**: Define your own key combinations
- **Multiple Action Types**: Navigate to URLs, click elements, type text, execute JavaScript
- **Cross-Platform**: Works on Windows, Linux, and Raspberry Pi OS
- **Easy Configuration**: Simple JSON config file
- **Standalone Executable**: Package as a single executable (no Python required)
- **Safe**: You login manually - no credential storage

## 📋 Requirements

### For Running from Source
- Python 3.8 or higher
- Google Chrome or Chromium browser
- ChromeDriver (installed automatically)

### For Standalone Executable
- Google Chrome or Chromium browser only

## 🚀 Quick Start

### Windows

1. **Setup** (first time only):
   ```batch
   setup_windows.bat
   ```

2. **Run**:
   ```batch
   run_windows.bat
   ```

### Raspberry Pi OS / Linux

1. **Setup** (first time only):
   ```bash
   chmod +x setup_linux.sh
   ./setup_linux.sh
   ```

2. **Run**:
   ```bash
   chmod +x run_linux.sh
   ./run_linux.sh
   ```

## 🎮 How to Use

1. **Start the Automator**:
   - Run the script using the method above
   - A browser window will open automatically

2. **Login Manually**:
   - Navigate to the Samsung Knox portal
   - Login with your credentials as you normally would

3. **Use Shortcuts**:
   - Once logged in, press any configured shortcut
   - Example: `Ctrl+X+C` opens the attendance portal

4. **Stop**:
   - Press `ESC` to stop the automator

## ⚙️ Default Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+X+C` | Open Attendance Portal |
| `Ctrl+X+T` | Open Time Off Request |
| `Ctrl+X+P` | Open Payroll |
| `Ctrl+X+B` | Open Benefits |
| `Ctrl+X+S` | Submit Quick Form |
| `Ctrl+X+O` | Open Profile |

## 🛠️ Customizing Shortcuts

Edit the `config.json` file that's created on first run:

### Navigate to a URL
```json
{
  "name": "Open My Dashboard",
  "keys": ["ctrl", "x", "d"],
  "action": "navigate",
  "url": "/dashboard"
}
```

### Click an Element
```json
{
  "name": "Click Submit Button",
  "keys": ["ctrl", "x", "s"],
  "action": "click",
  "selector": "#submit-btn",
  "selector_type": "css"
}
```

### Type Text
```json
{
  "name": "Fill Username",
  "keys": ["ctrl", "x", "u"],
  "action": "type",
  "selector": "#username",
  "text": "your-username",
  "selector_type": "css"
}
```

### Execute JavaScript
```json
{
  "name": "Scroll to Bottom",
  "keys": ["ctrl", "x", "b"],
  "action": "execute_js",
  "script": "window.scrollTo(0, document.body.scrollHeight);"
}
```

### Configuration Options

#### Selector Types
- `css`: CSS selector (default)
- `xpath`: XPath selector
- `id`: Element ID

#### Key Names
Use lowercase names:
- Modifiers: `ctrl`, `shift`, `alt`, `cmd` (Mac)
- Letters: `a`, `b`, `c`, etc.
- Numbers: `1`, `2`, `3`, etc.
- Special: `space`, `enter`, `tab`, `esc`, etc.

## 📦 Creating a Standalone Executable

To package the automator as a standalone application:

1. **Activate virtual environment**:
   - Windows: `venv\Scripts\activate.bat`
   - Linux: `source venv/bin/activate`

2. **Run packaging script**:
   ```bash
   python package.py
   ```

3. **Find your executable**:
   - Location: `distribution/` folder
   - Windows: `PortalAutomator_windows.exe`
   - Linux: `PortalAutomator_linux`

4. **Distribute**:
   - Share the entire `distribution` folder
   - Users don't need Python installed
   - They just need Chrome browser

## 🔧 Advanced Configuration

### Full config.json Example

```json
{
  "browser": "chrome",
  "headless": false,
  "base_url": "https://knox.samsung.com",
  "shortcuts": [
    {
      "name": "Open Attendance Portal",
      "keys": ["ctrl", "x", "c"],
      "action": "navigate",
      "url": "/attendance"
    },
    {
      "name": "Approve Timesheet",
      "keys": ["ctrl", "x", "a"],
      "action": "click",
      "selector": "//button[text()='Approve']",
      "selector_type": "xpath"
    },
    {
      "name": "Quick Search",
      "keys": ["ctrl", "x", "f"],
      "action": "type",
      "selector": "#search-box",
      "text": "vacation",
      "selector_type": "id"
    }
  ]
}
```

### Browser Options
- `"browser": "chrome"` - Use Chrome (default)
- `"headless": true` - Run browser in background (no window)
- `"headless": false` - Show browser window (default)

## 🐛 Troubleshooting

### Browser doesn't start
- **Solution**: Make sure Chrome is installed
- Windows: Install from https://www.google.com/chrome/
- Linux: `sudo apt install chromium-browser`

### Shortcuts don't work
- **Check**: JSON syntax in config.json
- **Verify**: Key names are lowercase
- **Test**: Run from terminal to see error messages

### Element not found
- **Solution**: Update selector in config.json
- Use Chrome DevTools (F12) to find correct selector
- Right-click element → Inspect → Copy selector

### ChromeDriver issues
- **Windows**: Run `setup_windows.bat` again
- **Linux**: `sudo apt install chromium-chromedriver`

## 📁 Project Structure

```
portal-automator/
├── portal_automator.py    # Main script
├── config.json             # Configuration file (created on first run)
├── requirements.txt        # Python dependencies
├── setup_windows.bat       # Windows setup script
├── setup_linux.sh          # Linux setup script
├── run_windows.bat         # Windows run script
├── run_linux.sh            # Linux run script
├── package.py              # Create standalone executable
└── README.md               # This file
```

## 🔒 Security Notes

- **No credentials stored**: You login manually every time
- **Local execution**: All actions run on your computer
- **Browser control only**: Script only controls your browser
- **Open source**: Inspect the code to verify safety

## 💡 Tips & Best Practices

1. **Start Simple**: Test with one shortcut first
2. **Use Unique Combinations**: Avoid conflicts with browser shortcuts
3. **Test Selectors**: Use browser console to verify selectors work
4. **Backup Config**: Save your config.json before major changes
5. **Window Focus**: Make sure browser window is focused when using shortcuts

## 📝 Example Use Cases

### Quick Attendance Check-in
```json
{
  "name": "Clock In",
  "keys": ["ctrl", "x", "i"],
  "action": "click",
  "selector": "#clock-in-button"
}
```

### Navigate to Multiple Pages
```json
{
  "keys": ["ctrl", "x", "1"],
  "action": "navigate",
  "url": "/page1"
},
{
  "keys": ["ctrl", "x", "2"],
  "action": "navigate",
  "url": "/page2"
}
```

### Fill and Submit Form
```json
{
  "keys": ["ctrl", "x", "f"],
  "action": "type",
  "selector": "#reason",
  "text": "Medical appointment"
},
{
  "keys": ["ctrl", "x", "s"],
  "action": "click",
  "selector": "#submit"
}
```

## 🤝 Contributing

Feel free to customize this tool for your needs:
1. Fork the repository
2. Add your improvements
3. Test thoroughly
4. Share with colleagues (if allowed by company policy)

## ⚠️ Disclaimer

This tool is for personal productivity enhancement. Ensure your use complies with:
- Samsung's IT policies
- Your employment agreement
- Company security guidelines

Always use responsibly and ethically.

## 📄 License

This is a personal productivity tool. Use at your own discretion.

## 🆘 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify your config.json syntax
3. Run from terminal to see detailed error messages
4. Ensure Chrome and Python are up to date

---

**Happy automating! 🚀**
