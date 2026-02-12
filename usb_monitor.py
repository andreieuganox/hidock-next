#!/usr/bin/env python3
"""
Simple USB HiDock Traffic Monitor
Monitors USB communication with HiDock devices
"""

import sys
import time
import threading
from datetime import datetime

try:
    import usb.core
    import usb.util
except ImportError:
    print("Error: pyusb not installed. Install with: pip install pyusb")
    sys.exit(1)

class HiDockUSBMonitor:
    def __init__(self):
        self.device = None
        self.monitoring = False
        
    def find_device(self):
        """Find HiDock device"""
        # Try different HiDock product IDs
        product_ids = [0xb00e, 0xAF0C, 0xAF0D, 0xB00D]
        
        for pid in product_ids:
            device = usb.core.find(idVendor=0x10d6, idProduct=pid)
            if device:
                print(f"Found HiDock device: VID=0x10d6, PID=0x{pid:04x}")
                return device
        
        return None
    
    def monitor_endpoint(self, endpoint_addr, direction_name):
        """Monitor a specific USB endpoint"""
        while self.monitoring:
            try:
                # Read from endpoint with short timeout
                data = self.device.read(endpoint_addr, 64, timeout=100)
                if data and len(data) > 0:
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    hex_data = ' '.join(f'{b:02x}' for b in data)
                    
                    print(f"[{timestamp}] {direction_name}: {hex_data}")
                    
                    # Try to parse HiDock packet
                    if len(data) >= 12 and data[0] == 0x12 and data[1] == 0x34:
                        cmd_id = (data[2] << 8) | data[3]
                        seq_id = (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]
                        body_len = (data[8] << 24) | (data[9] << 16) | (data[10] << 8) | data[11]
                        print(f"    -> HiDock packet: CMD={cmd_id}, SEQ={seq_id}, LEN={body_len}")
                        
                        if len(data) > 12:
                            body_hex = ' '.join(f'{b:02x}' for b in data[12:])
                            body_ascii = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[12:])
                            print(f"    -> Body: {body_hex}")
                            print(f"    -> ASCII: {body_ascii}")
                    print()
                    
            except usb.core.USBTimeoutError:
                # Timeout is expected, continue monitoring
                pass
            except usb.core.USBError as e:
                if "Operation timed out" not in str(e):
                    print(f"USB Error on {direction_name}: {e}")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error monitoring {direction_name}: {e}")
                break
    
    def start_monitoring(self):
        """Start monitoring USB traffic"""
        self.device = self.find_device()
        if not self.device:
            print("No HiDock device found!")
            return False
        
        try:
            # Try to claim the device (might fail if already in use)
            if self.device.is_kernel_driver_active(0):
                print("Kernel driver is active - monitoring may be limited")
            
            # Don't claim interface to avoid conflicts with other apps
            # usb.util.claim_interface(self.device, 0)
            
        except Exception as e:
            print(f"Warning: Could not claim device interface: {e}")
            print("Continuing anyway - monitoring may be limited")
        
        print("Starting USB traffic monitoring...")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        self.monitoring = True
        
        # Start monitoring threads for both endpoints
        in_thread = threading.Thread(
            target=self.monitor_endpoint, 
            args=(0x82, "IN "), 
            daemon=True
        )
        out_thread = threading.Thread(
            target=self.monitor_endpoint, 
            args=(0x01, "OUT"), 
            daemon=True
        )
        
        in_thread.start()
        out_thread.start()
        
        try:
            while self.monitoring:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            self.monitoring = False
        
        return True

def main():
    monitor = HiDockUSBMonitor()
    
    print("HiDock USB Traffic Monitor")
    print("=" * 30)
    
    if not monitor.start_monitoring():
        print("Failed to start monitoring")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
