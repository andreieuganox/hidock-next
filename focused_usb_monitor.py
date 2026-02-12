#!/usr/bin/env python3
"""
Focused USB Monitor for HiDock
Monitors specific USB-related system activity
"""

import subprocess
import sys
import time
import threading
import re
from datetime import datetime

class FocusedUSBMonitor:
    def __init__(self):
        self.monitoring = False
        
    def monitor_usb_logs(self):
        """Monitor USB-specific system logs"""
        print("🔍 Monitoring USB-specific logs...")
        
        try:
            # More specific USB log monitoring
            process = subprocess.Popen([
                'log', 'stream', '--style', 'compact', '--level', 'debug',
                '--predicate', 
                'subsystem contains "usb" OR '
                'subsystem contains "iokit" OR '
                'eventMessage contains "10d6" OR '
                'eventMessage contains "b00e" OR '
                'eventMessage contains "HiDock" OR '
                'eventMessage contains "Actions" OR '
                'eventMessage contains "bulk" OR '
                'eventMessage contains "endpoint" OR '
                'eventMessage contains "transfer"'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    # Filter for relevant USB activity
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in [
                        'usb', 'iokit', '10d6', 'b00e', 'hidock', 'actions',
                        'bulk', 'endpoint', 'transfer', 'device'
                    ]):
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] USB: {line.strip()}")
                elif process.poll() is not None:
                    break
                    
        except Exception as e:
            print(f"Error monitoring USB logs: {e}")
    
    def monitor_kernel_messages(self):
        """Monitor kernel messages for USB activity"""
        print("🔍 Monitoring kernel messages...")
        
        try:
            # Monitor kernel messages
            process = subprocess.Popen([
                'log', 'stream', '--style', 'compact', '--level', 'debug',
                '--predicate', 'subsystem == "com.apple.kernel"'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in [
                        'usb', '10d6', 'b00e', 'hidock', 'bulk', 'endpoint'
                    ]):
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] KERNEL: {line.strip()}")
                elif process.poll() is not None:
                    break
                    
        except Exception as e:
            print(f"Error monitoring kernel messages: {e}")
    
    def monitor_iokit_activity(self):
        """Monitor IOKit activity"""
        print("🔍 Monitoring IOKit activity...")
        
        try:
            # Monitor IOKit specifically
            process = subprocess.Popen([
                'log', 'stream', '--style', 'compact', '--level', 'debug',
                '--predicate', 'subsystem contains "iokit"'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in [
                        'usb', '10d6', 'b00e', 'hidock', 'bulk', 'endpoint', 'transfer'
                    ]):
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        print(f"[{timestamp}] IOKIT: {line.strip()}")
                elif process.poll() is not None:
                    break
                    
        except Exception as e:
            print(f"Error monitoring IOKit: {e}")
    
    def monitor_process_activity(self):
        """Monitor for Python processes that might be using USB"""
        print("🔍 Monitoring process activity...")
        
        while self.monitoring:
            try:
                # Check for Python processes
                result = subprocess.run([
                    'ps', 'aux'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'python' in line.lower() and any(keyword in line.lower() for keyword in [
                            'hidock', 'usb', 'main.py'
                        ]):
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] PROCESS: {line.strip()}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error monitoring processes: {e}")
                time.sleep(5)
    
    def start_monitoring(self):
        """Start comprehensive monitoring"""
        print("🚀 Focused USB Monitor for HiDock")
        print("=" * 50)
        print("Now run your desktop app and download a file!")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        self.monitoring = True
        
        # Start monitoring threads
        threads = [
            threading.Thread(target=self.monitor_usb_logs, daemon=True),
            threading.Thread(target=self.monitor_kernel_messages, daemon=True),
            threading.Thread(target=self.monitor_iokit_activity, daemon=True),
            threading.Thread(target=self.monitor_process_activity, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
        
        try:
            while self.monitoring:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.monitoring = False
        
        print("✅ Monitoring stopped")

def main():
    monitor = FocusedUSBMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
