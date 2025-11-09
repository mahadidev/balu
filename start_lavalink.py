#!/usr/bin/env python3
"""
Lavalink Auto-Setup and Startup Script
Downloads and starts Lavalink server automatically
"""

import os
import sys
import asyncio
import subprocess
import platform
import urllib.request
import shutil
from pathlib import Path

LAVALINK_VERSION = "4.0.7"
LAVALINK_JAR_URL = f"https://github.com/lavalink-devs/Lavalink/releases/download/{LAVALINK_VERSION}/Lavalink.jar"
LAVALINK_JAR_PATH = "Lavalink.jar"

def check_java():
    """Check if Java is installed"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Java is installed")
            return True
        else:
            print("❌ Java is not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ Java is not installed")
        return False

def download_lavalink():
    """Download Lavalink if it doesn't exist"""
    if os.path.exists(LAVALINK_JAR_PATH):
        print(f"✅ Lavalink JAR already exists: {LAVALINK_JAR_PATH}")
        return True
    
    print(f"📥 Downloading Lavalink {LAVALINK_VERSION}...")
    try:
        urllib.request.urlretrieve(LAVALINK_JAR_URL, LAVALINK_JAR_PATH)
        print(f"✅ Downloaded Lavalink to {LAVALINK_JAR_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to download Lavalink: {e}")
        return False

def start_lavalink():
    """Start Lavalink server"""
    if not os.path.exists("application.yml"):
        print("❌ application.yml not found!")
        return False
    
    print("🚀 Starting Lavalink server...")
    try:
        # Start Lavalink as a subprocess
        process = subprocess.Popen([
            'java', '-jar', LAVALINK_JAR_PATH
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        print(f"✅ Lavalink started with PID: {process.pid}")
        print("🎵 Lavalink is running on http://127.0.0.1:2333")
        print("🔑 Password: youshallnotpass")
        print("\n📋 To stop Lavalink, press Ctrl+C or kill the process")
        
        # Monitor the process
        try:
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    print("❌ Lavalink process has stopped")
                    break
                
                # Print any output
                import select
                if select.select([process.stdout], [], [], 0.1)[0]:
                    line = process.stdout.readline()
                    if line:
                        print(f"[LAVALINK] {line.strip()}")
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping Lavalink...")
            process.terminate()
            process.wait()
            print("✅ Lavalink stopped")
            
    except Exception as e:
        print(f"❌ Failed to start Lavalink: {e}")
        return False

def install_java_instructions():
    """Print Java installation instructions"""
    system = platform.system().lower()
    
    print("\n📦 Java Installation Instructions:")
    print("=" * 50)
    
    if system == "darwin":  # macOS
        print("For macOS:")
        print("1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. Install Java: brew install openjdk@17")
        print("3. Set JAVA_HOME: echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@17' >> ~/.zshrc")
    elif system == "linux":
        print("For Ubuntu/Debian:")
        print("sudo apt update && sudo apt install openjdk-17-jdk")
        print("\nFor CentOS/RHEL:")
        print("sudo yum install java-17-openjdk-devel")
    elif system == "windows":
        print("For Windows:")
        print("1. Download Java from: https://adoptium.net/")
        print("2. Install the downloaded .msi file")
        print("3. Add Java to PATH environment variable")
    
    print("\n🔄 After installing Java, run this script again")

def main():
    """Main function"""
    print("🎵 Lavalink Auto-Setup")
    print("=" * 30)
    
    # Check Java
    if not check_java():
        install_java_instructions()
        return 1
    
    # Download Lavalink
    if not download_lavalink():
        return 1
    
    # Start Lavalink
    if not start_lavalink():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())