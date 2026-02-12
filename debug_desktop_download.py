#!/usr/bin/env python3
"""
Debug script to test desktop app download with maximum logging
"""

import sys
import os

# Add the desktop src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'desktop', 'src'))

from hidock_device import HiDockJensen
from config_and_logger import Logger

def test_download():
    """Test downloading a file with debug logging"""
    
    # Create logger with DEBUG level
    debug_config = {
        "log_level": "DEBUG",
        "console_log_level": "DEBUG",
        "enable_console_logging": True,
        "enable_file_logging": False
    }
    
    logger = Logger(debug_config)
    
    # Create device instance
    device = HiDockJensen()
    
    try:
        print("🔌 Connecting to HiDock device...")
        success, error = device.connect()
        
        if not success:
            print(f"❌ Failed to connect: {error}")
            return
            
        print("✅ Connected successfully!")
        
        # Get device info
        print("\n📱 Getting device info...")
        device_info = device.get_device_info()
        print(f"Device info: {device_info}")
        
        # Get file list
        print("\n📂 Getting file list...")
        file_list_result = device.list_files(timeout_s=10)
        
        if not file_list_result or not file_list_result.get('files'):
            print("❌ No files found")
            return
            
        files = file_list_result['files']
        print(f"📁 Found {len(files)} files")
        
        # Pick the first file for download test
        if files:
            test_file = files[0]
            filename = test_file['name']
            file_size = test_file['length']
            
            print(f"\n📥 Testing download of: {filename} ({file_size} bytes)")
            
            # Prepare data collection
            downloaded_data = bytearray()
            
            def data_callback(chunk):
                downloaded_data.extend(chunk)
                print(f"📦 Received chunk: {len(chunk)} bytes, total: {len(downloaded_data)}/{file_size}")
            
            def progress_callback(received, total):
                percent = (received / total) * 100 if total > 0 else 0
                print(f"📊 Progress: {received}/{total} bytes ({percent:.1f}%)")
            
            # Attempt download
            print(f"\n🚀 Starting download of {filename}...")
            result = device.stream_file(
                filename=filename,
                file_length=file_size,
                data_callback=data_callback,
                progress_callback=progress_callback,
                timeout_s=60
            )
            
            print(f"\n📋 Download result: {result}")
            print(f"📊 Downloaded {len(downloaded_data)} bytes")
            
            if result == "OK":
                print("✅ Download successful!")
            else:
                print(f"❌ Download failed: {result}")
        
    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🔌 Disconnecting...")
        device.disconnect()

if __name__ == "__main__":
    test_download()
