#!/usr/bin/env python3
"""
System-level USB monitoring for HiDock
Monitors USB activity without claiming the device
"""

import subprocess
import sys
import time
import threading
import re
from datetime import datetime

class SystemUSBMonitor:
    def __init__(self):
        self.monitoring = False
        
    def monitor_ioreg(self):
        """Monitor USB device registry changes"""
        print("🔍 Monitoring USB device registry...")
        
        last_output = ""
        while self.monitoring:
            try:
                # Get current USB device info for HiDock
                result = subprocess.run([
                    'ioreg', '-p', 'IOUSB', '-l', '-w', '0'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    # Filter for HiDock-related entries
                    lines = result.stdout.split('\n')
                    hidock_section = []
                    in_hidock = False
                    
                    for line in lines:
                        if '10d6' in line or 'HiDock' in line or 'Actions' in line:
                            in_hidock = True
                            hidock_section = [line]
                        elif in_hidock:
                            if line.strip() and not line.startswith('  '):
                                in_hidock = False
                            else:
                                hidock_section.append(line)
                    
                    current_output = '\n'.join(hidock_section)
                    if current_output != last_output and current_output.strip():
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"\n[{timestamp}] USB Registry Change:")
                        print(current_output)
                        last_output = current_output
                
                time.sleep(1)
                
            except subprocess.TimeoutExpired:
                print("⚠️  ioreg timeout")
            except Exception as e:
                print(f"Error monitoring ioreg: {e}")
                time.sleep(2)
    
    def monitor_system_log(self):
        """Monitor system logs for USB activity"""
        print("📋 Monitoring system logs for USB activity...")
        
        try:
            # Start log streaming process
            process = subprocess.Popen([
                'log', 'stream', '--style', 'compact', '--level', 'debug',
                '--predicate', 'eventMessage contains "USB" OR eventMessage contains "10d6" OR eventMessage contains "HiDock"'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] LOG: {line.strip()}")
                elif process.poll() is not None:
                    break
                    
        except Exception as e:
            print(f"Error monitoring system log: {e}")
    
    def monitor_usb_activity(self):
        """Monitor USB activity using multiple methods"""
        print("🔍 Starting comprehensive USB monitoring...")
        
        # Start monitoring threads
        threads = []
        
        # Thread 1: ioreg monitoring
        ioreg_thread = threading.Thread(target=self.monitor_ioreg, daemon=True)
        threads.append(ioreg_thread)
        ioreg_thread.start()
        
        # Thread 2: system log monitoring  
        log_thread = threading.Thread(target=self.monitor_system_log, daemon=True)
        threads.append(log_thread)
        log_thread.start()
        
        print("✅ Monitoring started. Now run your desktop app in another terminal!")
        print("⏹️  Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.monitoring = False
    
    def start(self):
        """Start monitoring"""
        print("🚀 System USB Monitor for HiDock")
        print("=" * 40)
        
        self.monitoring = True
        self.monitor_usb_activity()
        
        print("✅ Monitoring stopped")

def main():
    monitor = SystemUSBMonitor()
    monitor.start()

if __name__ == "__main__":
    main()
