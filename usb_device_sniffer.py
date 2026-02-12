#!/usr/bin/env python3
"""
USB Device-level Packet Sniffer for HiDock
Captures all USB traffic to/from HiDock device
"""

import sys
import time
import threading
import signal
from datetime import datetime

try:
    import usb.core
    import usb.util
    import usb.backend.libusb1
except ImportError:
    print("Error: pyusb not installed. Install with: pip install pyusb")
    sys.exit(1)

class USBDeviceSniffer:
    def __init__(self):
        self.device = None
        self.monitoring = False
        self.packet_count = 0
        
    def find_hidock_device(self):
        """Find any HiDock device"""
        # All known HiDock PIDs
        hidock_pids = [0xb00e, 0xAF0C, 0xAF0D, 0xB00D]
        
        print("Scanning for HiDock devices...")
        for pid in hidock_pids:
            device = usb.core.find(idVendor=0x10d6, idProduct=pid)
            if device:
                print(f"✅ Found HiDock: VID=0x{0x10d6:04x}, PID=0x{pid:04x}")
                print(f"   Device: {device}")
                return device
        
        print("❌ No HiDock device found")
        return None
    
    def decode_hidock_packet(self, data, direction):
        """Decode HiDock protocol packet"""
        if len(data) < 2:
            return None
            
        # Check for HiDock sync bytes
        if data[0] == 0x12 and data[1] == 0x34 and len(data) >= 12:
            try:
                cmd_id = (data[2] << 8) | data[3]  # Big-endian
                seq_id = (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]
                body_len = (data[8] << 24) | (data[9] << 16) | (data[10] << 8) | data[11]
                
                # Get command name
                cmd_names = {
                    1: "GET_DEVICE_INFO",
                    2: "GET_DEVICE_TIME", 
                    3: "SET_DEVICE_TIME",
                    4: "GET_FILE_LIST",
                    5: "TRANSFER_FILE",
                    6: "GET_FILE_COUNT",
                    7: "DELETE_FILE",
                    11: "GET_SETTINGS",
                    12: "SET_SETTINGS", 
                    13: "GET_FILE_BLOCK",
                    14: "UNKNOWN_14",
                    16: "GET_CARD_INFO",
                    18: "GET_RECORDING_FILE"
                }
                
                cmd_name = cmd_names.get(cmd_id, f"UNKNOWN_{cmd_id}")
                
                result = {
                    'cmd_id': cmd_id,
                    'cmd_name': cmd_name,
                    'seq_id': seq_id,
                    'body_len': body_len,
                    'body': data[12:] if len(data) > 12 else b''
                }
                
                return result
            except:
                return None
        
        return None
    
    def format_packet_output(self, data, direction, endpoint):
        """Format packet for display"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.packet_count += 1
        
        # Basic packet info
        hex_data = ' '.join(f'{b:02x}' for b in data[:64])  # Limit display
        if len(data) > 64:
            hex_data += f" ... ({len(data)} total bytes)"
        
        print(f"\n[{self.packet_count:04d}] [{timestamp}] {direction} EP{endpoint:02x}")
        print(f"RAW: {hex_data}")
        
        # Try to decode as HiDock packet
        decoded = self.decode_hidock_packet(data, direction)
        if decoded:
            print(f"🎯 HiDock: {decoded['cmd_name']} (ID={decoded['cmd_id']}) SEQ={decoded['seq_id']} LEN={decoded['body_len']}")
            
            if decoded['body']:
                body_hex = ' '.join(f'{b:02x}' for b in decoded['body'][:32])
                body_ascii = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in decoded['body'][:32])
                if len(decoded['body']) > 32:
                    body_hex += "..."
                    body_ascii += "..."
                print(f"BODY: {body_hex}")
                print(f"TEXT: {body_ascii}")
        else:
            # Show ASCII interpretation
            ascii_data = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:64])
            if ascii_data.strip():
                print(f"ASCII: {ascii_data}")
    
    def monitor_usb_traffic(self):
        """Monitor USB traffic using polling"""
        print("🔍 Starting USB traffic monitoring...")
        print("📡 Monitoring endpoints: IN=0x82, OUT=0x01")
        print("⏹️  Press Ctrl+C to stop\n")
        
        consecutive_errors = 0
        max_errors = 10
        
        while self.monitoring:
            try:
                # Try to read from IN endpoint (device to host)
                try:
                    data = self.device.read(0x82, 64, timeout=50)
                    if data and len(data) > 0:
                        self.format_packet_output(bytes(data), "IN ", 0x82)
                        consecutive_errors = 0
                except usb.core.USBTimeoutError:
                    pass  # Timeout is normal
                except usb.core.USBError as e:
                    if "timeout" not in str(e).lower():
                        consecutive_errors += 1
                        if consecutive_errors < 3:
                            print(f"⚠️  USB IN error: {e}")
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.001)
                
                if consecutive_errors >= max_errors:
                    print(f"❌ Too many consecutive errors ({consecutive_errors}), stopping...")
                    break
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"💥 Unexpected error: {e}")
                break
    
    def start_monitoring(self):
        """Start the USB monitoring process"""
        print("🚀 USB Device Sniffer for HiDock")
        print("=" * 40)
        
        # Find device
        self.device = self.find_hidock_device()
        if not self.device:
            return False
        
        # Setup signal handler
        def signal_handler(sig, frame):
            print("\n🛑 Stopping monitor...")
            self.monitoring = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Check if kernel driver is active
            if self.device.is_kernel_driver_active(0):
                print("⚠️  Kernel driver active - may limit monitoring")
            
            print(f"📱 Device configuration: {self.device.get_active_configuration()}")
            
        except Exception as e:
            print(f"⚠️  Device setup warning: {e}")
        
        # Start monitoring
        self.monitoring = True
        
        try:
            self.monitor_usb_traffic()
        except Exception as e:
            print(f"💥 Monitoring error: {e}")
        finally:
            self.monitoring = False
            print("\n✅ Monitoring stopped")
        
        return True

def main():
    sniffer = USBDeviceSniffer()
    
    if not sniffer.start_monitoring():
        print("❌ Failed to start USB monitoring")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
