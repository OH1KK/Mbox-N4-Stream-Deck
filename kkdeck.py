#!/usr/bin/python
import signal
import sys
import os
from StreamDock.DeviceManager import DeviceManager
from StreamDock.Devices.StreamDockN1 import StreamDockN1
import threading
import time

# Function for button 2's commands
def button_2_actions():
    print("Button 2 was pressed - launching gnome-calculator")
    os.system("/usr/bin/gnome-calculator")  # Launch gnome calculator

# Dictionary to map button numbers to commands
BUTTON_COMMANDS = {
    1: lambda: (print("Button 1 was pressed"), print("Button 1: Executing command 1")),  # Multiple actions in lambda
    2: lambda: button_2_actions(),  # Call a function with multiple actions
    3: lambda: print("Button 3 pressed: Executing command 3"),
    4: lambda: print("Button 4 pressed: Executing command 4"),
    5: lambda: print("Button 5 pressed: Executing command 5"),
    # Add more mappings as needed for buttons 6-10
}

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    for device in streamdocks:
        device.close()
    sys.exit(0)

def parse_feedback(feedback):
    """Parse the feedback string to extract Key and Status."""
    try:
        parts = feedback.split(", ")
        key_part = parts[2].split(": ")[1]  # Extract "Key: X"
        status_part = parts[3].split(": ")[1]  # Extract "Status: Y"
        return int(key_part), int(status_part)
    except (IndexError, ValueError):
        return None, None

class StreamDockPrintCapture:
    """Custom stdout wrapper to capture and process StreamDock output."""
    def __init__(self):
        self.original_stdout = sys.stdout
        self.last_press_time = 0
        self.debounce_interval = 0.2  # 200ms

    def write(self, text):
        # Write to original stdout
        self.original_stdout.write(text)
        # Process the text if it looks like StreamDock feedback
        text = text.strip()
        if text.startswith("Acknowledgement: ACK"):
            key, status = parse_feedback(text)
            if key is not None and status is not None:
                if status == 1 and key in BUTTON_COMMANDS:
                    current_time = time.time()
                    if current_time - self.last_press_time > self.debounce_interval:
                        BUTTON_COMMANDS[key]()
                        self.last_press_time = current_time
        # Ensure newline after feedback
        if text.endswith("Status: 0") or text.endswith("Status: 1"):
            self.original_stdout.write("\n")

    def flush(self):
        self.original_stdout.flush()

if __name__ == "__main__":
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Override stdout to capture StreamDock output
    sys.stdout = StreamDockPrintCapture()
    
    manager = DeviceManager()
    streamdocks = manager.enumerate()
    
    # Start device monitoring thread
    t = threading.Thread(target=manager.listen)
    t.daemon = True
    t.start()
    
    print(f"Found {len(streamdocks)} Stream Dock(s).\n")
    
    for device in streamdocks:
        # Open and initialize device
        device.open()
        device.init()
        
        # Start original whileread thread
        t = threading.Thread(target=device.whileread)
        t.daemon = True
        t.start()
        
        # Set touchscreen background image
        device.set_touchscreen_image("./img/sliderbg.png")
        device.refresh()
        time.sleep(2)
        
        # Set key images with fallback to button_template.png
        for i in range(1, 11):
            image_path = f"./img/b{i}.png"
            if os.path.exists(image_path):
                device.set_key_image(i, image_path)
            else:
                device.set_key_image(i, "./img/button_template.png")
            device.refresh()
        time.sleep(2)
        
        ## Clear single key icon
        #device.cleaerIcon(3)
        #device.refresh()
        #time.sleep(1)
        
        ## Clear all key icons
        #device.clearAllIcon()
        #device.refresh()
        #time.sleep(0)
        
        # Switch mode for N1 devices
        if isinstance(device, StreamDockN1):
            device.switch_mode(0)
    
    # Keep program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

