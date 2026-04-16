#!/usr/bin/env python3
"""
Samsung Knox Portal Keyboard Automation
Listens for keyboard shortcuts and performs browser actions
"""

import json
import time
import sys
from pathlib import Path
from pynput import keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import threading

class PortalAutomator:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.load_config()
        self.driver = None
        self.current_keys = set()
        self.listener = None
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            print(f"✓ Loaded configuration from {self.config_file}")
        except FileNotFoundError:
            print(f"✗ Config file not found: {self.config_file}")
            print("Creating default config...")
            self.create_default_config()
            
    def create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            "browser": "chrome",
            "headless": False,
            "base_url": "https://knox.samsung.com",
            "shortcuts": [
                {
                    "name": "Open Attendance Portal",
                    "keys": ["ctrl", "x", "c"],
                    "action": "navigate",
                    "url": "/attendance"
                },
                {
                    "name": "Open Time Off Request",
                    "keys": ["ctrl", "x", "t"],
                    "action": "navigate",
                    "url": "/timeoff"
                },
                {
                    "name": "Open Payroll",
                    "keys": ["ctrl", "x", "p"],
                    "action": "navigate",
                    "url": "/payroll"
                },
                {
                    "name": "Open Benefits",
                    "keys": ["ctrl", "x", "b"],
                    "action": "navigate",
                    "url": "/benefits"
                },
                {
                    "name": "Submit Quick Form",
                    "keys": ["ctrl", "x", "s"],
                    "action": "click",
                    "selector": "#submit-button",
                    "selector_type": "css"
                },
                {
                    "name": "Open Profile",
                    "keys": ["ctrl", "x", "o"],
                    "action": "navigate",
                    "url": "/profile"
                }
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.config = default_config
        print(f"✓ Created default config at {self.config_file}")
        print("Edit this file to customize your shortcuts!")
        
    def init_browser(self):
        """Initialize the browser driver"""
        if self.driver:
            return
            
        print("Initializing browser...")
        
        options = Options()
        if self.config.get("headless", False):
            options.add_argument("--headless")
        
        # Additional options for better compatibility
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            print("✓ Browser initialized")
        except Exception as e:
            print(f"✗ Failed to initialize browser: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            sys.exit(1)
    
    def perform_action(self, shortcut):
        """Perform the action associated with a shortcut"""
        action = shortcut.get("action")
        name = shortcut.get("name", "Unknown Action")
        
        print(f"\n🚀 Executing: {name}")
        
        try:
            if not self.driver:
                print("✗ Browser not initialized. Please open a browser window first.")
                return
                
            if action == "navigate":
                url = shortcut.get("url")
                if url.startswith("http"):
                    full_url = url
                else:
                    base_url = self.config.get("base_url", "")
                    full_url = base_url + url
                
                print(f"  → Navigating to: {full_url}")
                self.driver.get(full_url)
                
            elif action == "click":
                selector = shortcut.get("selector")
                selector_type = shortcut.get("selector_type", "css")
                
                print(f"  → Clicking element: {selector}")
                
                if selector_type == "css":
                    by = By.CSS_SELECTOR
                elif selector_type == "xpath":
                    by = By.XPATH
                elif selector_type == "id":
                    by = By.ID
                else:
                    by = By.CSS_SELECTOR
                
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, selector))
                )
                element.click()
                
            elif action == "type":
                selector = shortcut.get("selector")
                text = shortcut.get("text", "")
                selector_type = shortcut.get("selector_type", "css")
                
                print(f"  → Typing into element: {selector}")
                
                if selector_type == "css":
                    by = By.CSS_SELECTOR
                elif selector_type == "xpath":
                    by = By.XPATH
                elif selector_type == "id":
                    by = By.ID
                else:
                    by = By.CSS_SELECTOR
                
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                element.clear()
                element.send_keys(text)
                
            elif action == "execute_js":
                script = shortcut.get("script")
                print(f"  → Executing JavaScript")
                self.driver.execute_script(script)
                
            print("✓ Action completed successfully")
            
        except Exception as e:
            print(f"✗ Error executing action: {e}")
    
    def on_press(self, key):
        """Handle key press events"""
        try:
            # Convert key to string
            if hasattr(key, 'char') and key.char:
                key_str = key.char.lower()
            elif hasattr(key, 'name'):
                key_str = key.name.lower()
            else:
                key_str = str(key).replace("Key.", "").lower()
            
            self.current_keys.add(key_str)
            
            # Check if any shortcut matches
            for shortcut in self.config.get("shortcuts", []):
                shortcut_keys = [k.lower() for k in shortcut.get("keys", [])]
                
                if set(shortcut_keys) == self.current_keys:
                    # Execute action in a separate thread to avoid blocking
                    threading.Thread(target=self.perform_action, args=(shortcut,)).start()
                    
        except Exception as e:
            pass
    
    def on_release(self, key):
        """Handle key release events"""
        try:
            if hasattr(key, 'char') and key.char:
                key_str = key.char.lower()
            elif hasattr(key, 'name'):
                key_str = key.name.lower()
            else:
                key_str = str(key).replace("Key.", "").lower()
            
            self.current_keys.discard(key_str)
            
            # Stop listener if ESC is pressed
            if key == keyboard.Key.esc:
                print("\n🛑 ESC pressed - stopping automator...")
                return False
                
        except Exception as e:
            pass
    
    def start(self):
        """Start the keyboard listener"""
        print("=" * 60)
        print("Samsung Knox Portal Automator")
        print("=" * 60)
        print("\nConfigured Shortcuts:")
        for i, shortcut in enumerate(self.config.get("shortcuts", []), 1):
            keys = " + ".join([k.upper() for k in shortcut.get("keys", [])])
            name = shortcut.get("name", "Unknown")
            print(f"  {i}. {keys:<20} → {name}")
        
        print("\n" + "=" * 60)
        print("Instructions:")
        print("  1. Manually login to the Samsung Knox portal in Chrome")
        print("  2. Press any configured shortcut to perform actions")
        print("  3. Press ESC to stop the automator")
        print("=" * 60)
        
        # Initialize browser
        self.init_browser()
        
        # Start keyboard listener
        print("\n⌨️  Listening for keyboard shortcuts...")
        print("(Browser window has been opened - login manually)")
        
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        ) as self.listener:
            self.listener.join()
        
        # Cleanup
        if self.driver:
            print("\n🧹 Closing browser...")
            self.driver.quit()
        
        print("👋 Automator stopped. Goodbye!")

def main():
    automator = PortalAutomator()
    automator.start()

if __name__ == "__main__":
    main()
