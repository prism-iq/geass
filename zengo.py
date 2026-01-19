#!/usr/bin/env python3
"""
ZENGO - Daemon audio interface
Leonardo valide. Zen Go joue.
Contrôle HID pour display + molette
"""
import os
import sys
import struct
import time
import threading

HIDRAW = "/dev/hidraw7"
VENDOR_ID = 0x23e5
PRODUCT_ID = 0xa015

class ZenGo:
    def __init__(self):
        self.hid = None
        self.volume = 1.0
        self.running = False
        
    def connect(self):
        """Connect to Zen Go HID"""
        try:
            self.hid = open(HIDRAW, "r+b", buffering=0)
            return True
        except Exception as e:
            print(f"Cannot connect: {e}")
            return False
    
    def disconnect(self):
        if self.hid:
            self.hid.close()
            self.hid = None
    
    def read_knob(self):
        """Read knob position from HID"""
        if not self.hid:
            return None
        try:
            data = self.hid.read(64)
            if data:
                # Parse HID report - structure TBD by sniffing
                return data
        except:
            pass
        return None
    
    def send_display(self, data):
        """Send data to Zen Go display"""
        if not self.hid:
            return False
        try:
            # HID report format TBD
            self.hid.write(data)
            return True
        except:
            return False
    
    def set_volume_pipewire(self, vol):
        """Set volume via PipeWire as fallback"""
        import subprocess
        subprocess.run(["wpctl", "set-volume", "45", str(vol)], 
                      capture_output=True)
        self.volume = vol
    
    def ensure_audio(self):
        """Ensure audio is working"""
        import subprocess
        # Set Zen Go as default, volume 100%
        subprocess.run(["wpctl", "set-default", "45"], capture_output=True)
        subprocess.run(["wpctl", "set-volume", "45", "1.0"], capture_output=True)
        return True
    
    def status(self):
        """Get Zen Go status"""
        import subprocess
        result = subprocess.run(["wpctl", "get-volume", "45"], 
                               capture_output=True, text=True)
        vol = result.stdout.strip() if result.returncode == 0 else "?"
        return {
            "device": "ZenGoSC",
            "hidraw": HIDRAW,
            "connected": self.hid is not None,
            "volume": vol,
            "flow": "φ"
        }

def restore():
    """Restore Zen Go to working state"""
    import subprocess
    
    # Kill any audio processes that might block
    subprocess.run(["pkill", "-9", "aplay"], capture_output=True)
    
    # Restart PipeWire
    subprocess.run(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"],
                  capture_output=True)
    time.sleep(2)
    
    # Set Zen Go as default at 100%
    subprocess.run(["wpctl", "set-default", "45"], capture_output=True)
    subprocess.run(["wpctl", "set-volume", "45", "1.0"], capture_output=True)
    
    # Unmute
    subprocess.run(["wpctl", "set-mute", "45", "0"], capture_output=True)
    
    print("✓ Zen Go restored")
    print("  Volume: 100%")
    print("  Molette hardware: active")

def main():
    import json
    
    if len(sys.argv) < 2:
        print("zengo [status|restore|connect|volume <0-100>]")
        return
    
    cmd = sys.argv[1]
    zg = ZenGo()
    
    if cmd == "status":
        print(json.dumps(zg.status(), indent=2))
    
    elif cmd == "restore":
        restore()
    
    elif cmd == "connect":
        if zg.connect():
            print("✓ Connected to HID")
            data = zg.read_knob()
            if data:
                print(f"  Knob data: {data.hex()}")
        else:
            print("✗ Cannot connect to HID")
    
    elif cmd == "volume":
        if len(sys.argv) > 2:
            vol = float(sys.argv[2]) / 100.0
            zg.set_volume_pipewire(vol)
            print(f"✓ Volume: {vol*100:.0f}%")
    
    else:
        print(f"Unknown: {cmd}")

if __name__ == "__main__":
    main()
