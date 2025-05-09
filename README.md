# Mbox-N4-Stream-Deck

This is my first to to get Mirabox M4 Stream Deck to work in ubuntu. Repository is mainly for myself to remember how I got it working. This is not production ready code, instead an example how to communicate with a device.

This code includes part of StreamDock-Device-SDK which is available https://github.com/MiraboxSpace/StreamDock-Device-SDK/

## Install

First make mirabox available to regular user

Make file /etc/udev/rules.d/99-mirabox.rules and add there
````
# Allow user access to Mirabox USB HID and Bulk device
SUBSYSTEM=="usb", ATTRS{idVendor}=="6603", ATTRS{idProduct}=="1007", MODE="0666", TAG+="uaccess"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="6603", ATTRS{idProduct}=="1007", MODE="0666", TAG+="uaccess"
KERNEL=="hiddev*", ATTRS{idVendor}=="6603", ATTRS{idProduct}=="1007", MODE="0666", TAG+="uaccess"
````
Then reload rules

````
sudo udevadm control --reload-rules
sudo udevadm trigger
````
Then unplug mirabox and plug it again.

Install some depencies

````
sudo apt install -y python3-pyudev libusb-dev libhidapi-libusb0 python3-willow git
````

Then clone this repository and try it out.

````
git clone https://github.com/OH1KK/Mbox-N4-Stream-Deck.git
cd Mbox-N4-Stream-Deck
chmod +x kkdock.py
./kkdock.py
````
