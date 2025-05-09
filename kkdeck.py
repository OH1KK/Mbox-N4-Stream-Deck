#!/usr/bin/python
import signal
import sys
import os
from StreamDock.DeviceManager import DeviceManager
from StreamDock.Devices.StreamDockN1 import StreamDockN1
import threading
import time
import subprocess

# Dictionary to map button numbers to commands
BUTTON_COMMANDS = {
    1: ["/usr/bin/gnome-terminal"],
    2: ["/usr/bin/gnome-calculator"],
    3: ["/usr/bin/gedit"],
    4: ["/usr/bin/xclock"],
    5: ["/usr/bin/gimp"],
    6: ["/usr/local/bin/camscript", "frontdoor"],
    7: ["/usr/local/bin/camscript", "backyard"],
    8: ["/usr/local/bin/camscript", "garage"],
    9: ["/usr/local/bin/camscript", "hamschack"],
    10: ["/usr/bin/firefox"],
}

# Dictionary to store running processes
running_processes = {}

def signal_handler(sig, frame):
    print("\nShutting down gracefully...")
    # Terminate all running processes
    for key, proc in running_processes.items():
        if proc.poll() is None:  # Check if process is still running
            proc.terminate()
            try:
                proc.wait(timeout=2)  # Wait briefly for graceful termination
            except subprocess.TimeoutExpired:
                proc.kill()  # Force kill if it doesn't terminate
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
                        self.handle_button_press(key)
                        self.last_press_time = current_time
        # Ensure newline after feedback
        if text.endswith("Status: 0") or text.endswith("Status: 1"):
            self.original_stdout.write("\n")

    def flush(self):
        self.original_stdout.flush()

    def handle_button_press(self, key):
        """Handle button press: start or kill the process for the button."""
        print(f"Button {key} was pressed")
        if key in running_processes and running_processes[key].poll() is None:
            # Process is running; terminate it
            running_processes[key].terminate()
            try:
                running_processes[key].wait(timeout=2)
                print(f"Terminated process for button {key}")
            except subprocess.TimeoutExpired:
                running_processes[key].kill()
                print(f"Forced termination of process for button {key}")
            del running_processes[key]
        else:
            # No process running; start a new one
            cmd = BUTTON_COMMANDS[key]
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                running_processes[key] = proc
                print(f"Started process for button {key} with PID {proc.pid}")
            except Exception as e:
                print(f"Failed to start process for button {key}: {e}")

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
        time.sleep(4)
        
        # Set key images with fallback to button_template.png
        for i in range(1, 11):
            image_path = f"./img/b{i}.png"
            if os.path.exists(image_path):
                device.set_key_image(i, image_path)
            else:
                device.set_key_image(i, "./img/button_template.png")
            device.refresh()
        time.sleep(2)
        
        # Switch mode for N1 devices
        if isinstance(device, StreamDockN1):
            device.switch_mode(0)
    
    # Keep program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
