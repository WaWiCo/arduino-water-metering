##############################################
# Bluetooth Controller for Raspberry Pi
# ---- reads audio amplitude data from
# ---- WaWiCo Arduino FFT data transmitted
# ---- from CC254x BLE chip
#
#    Josh Hrisko, 2020
#    Maker Portal LLC x WaWiCo
#
##############################################
#
import time
import pexpect
import subprocess
import sys
import logging
#
#
logger = logging.getLogger("btctl")
#
#
#
####################################
# Raspberry Pi Bluetooth Controller 
####################################
#
class Bluetoothctl: 
    """A wrapper for bluetoothctl utility."""
    def __init__(self):
        subprocess.check_output("rfkill unblock bluetooth", shell=True)
        self.process = pexpect.spawnu("bluetoothctl", echo=False)

    def send(self, command, pause=0):
        self.process.send(f"{command}\n")
        time.sleep(pause)
        if self.process.expect(["bluetooth", pexpect.EOF]):
            raise Exception(f"failed after {command}")

    def default_agent(self):
        """default agent request"""
        try:
            self.send("default-agent")
        except Exception as e:
            logger.error(e)
           
    def agent_on(self):
        """agent on request"""
        try:
            self.send("agent on")
        except Exception as e:
            logger.error(e)

    def get_output(self, *args, **kwargs):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.send(*args, **kwargs)
        return self.process.before.split("\r\n")

    def start_scan(self):
        """Start bluetooth scanning process."""
        try:
            self.send("scan on")
        except Exception as e:
            logger.error(e)

    def make_discoverable(self):
        """Make device discoverable."""
        try:
            self.send("discoverable on")
        except Exception as e:
            logger.error(e)

    def parse_device_info(self, info_string):
        """Parse a string corresponding to a device."""
        device = {}
        block_list = ["[\x1b[0;", "removed"]
        if not any(keyword in info_string for keyword in block_list):
            try:
                device_position = info_string.index("Device")
            except ValueError:
                pass
            else:
                if device_position > -1:
                    attribute_list = info_string[device_position:].split(" ", 2)
                    device = {
                        "mac_address": attribute_list[1],
                        "name": attribute_list[2],
                    }
        return device

    def get_available_devices(self):
        """Return a list of tuples of paired and discoverable devices."""
        available_devices = []
        try:
            out = self.get_output("devices")
        except Exception as e:
            logger.error(e)
        else:
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    available_devices.append(device)
        return available_devices

    def get_paired_devices(self):
        """Return a list of tuples of paired devices."""
        paired_devices = []
        try:
            out = self.get_output("paired-devices")
        except Exception as e:
            logger.error(e)
        else:
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    paired_devices.append(device)
        return paired_devices

    def get_discoverable_devices(self):
        """Filter paired devices out of available."""
        available = self.get_available_devices()
        paired = self.get_paired_devices()
        return [d for d in available if d not in paired]

    def get_device_info(self, mac_address):
        """Get device info by mac address."""
        try:
            out = self.get_output(f"info {mac_address}")
        except Exception as e:
            logger.error(e)
            return False
        else:
            return out

    def pair(self, mac_address):
        """Try to pair with a device by mac address."""
        try:
            self.send(f"pair {mac_address}", 4)
        except Exception as e:
            logger.error(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to pair", "Pairing successful", pexpect.EOF]
            )
            return res == 1

    def trust(self, mac_address):
        try:
            self.send(f"trust {mac_address}", 4)
        except Exception as e:
            logger.error(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to trust", "Pairing successful", pexpect.EOF]
            )
            return res == 1

    def remove(self, mac_address):
        """Remove paired device by mac address, return success of the operation."""
        try:
            self.send(f"remove {mac_address}", 3)
        except Exception as e:
            logger.error(e)
            return False
        else:
            res = self.process.expect(
                ["not available", "Device has been removed", pexpect.EOF]
            )
            return res == 1

    def connect(self, mac_address):
        """Try to connect to a device by mac address."""
        try:
            self.send(f"connect {mac_address}", 2)
        except Exception as e:
            logger.error(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to connect", "Connection successful", pexpect.EOF]
            )
            return res == 1

    def disconnect(self, mac_address):
        """Try to disconnect to a device by mac address."""
        try:
            self.send(f"disconnect {mac_address}", 2)
        except Exception as e:
            logger.error(e)
            return False
        else:
            res = self.process.expect(
                ["Failed to disconnect", "Successful disconnected", pexpect.EOF]
            )
            return res == 1
#
################################
# Gatt Bluetooth Controller
# (comm with BLE device)
################################
#
class Gattctl:
    """A wrapper for bluetoothctl utility."""

    def __init__(self):
        subprocess.check_output("rfkill unblock bluetooth", shell=True)
        self.process = pexpect.spawnu("bluetoothctl", echo=False)

    def send(self, command, pause=0):
        self.process.send(f"{command}\n")
        time.sleep(pause)
        if self.process.expect(["WaWiCo", pexpect.EOF]):
            raise Exception(f"failed after {command}")

    def get_output(self, *args, **kwargs):
        """Returns the output from the BLE device"""
        self.send(*args, **kwargs)
        out = self.process.before.split("\r\n")
        data_parsed = []
        for line in out:
            joined = [ii for ii in line if ii!='\x1b' and ii!='\t']
            data_parsed.append(''.join(joined))
        return data_parsed

def disconnect():
    gatt.send("back") # for Gatt service
    gatt.send("disconnect") # disconnect from BLE device
#
################################
# Main Bluetooth Procedure
################################
#
if __name__ == "__main__":
    ble = Bluetoothctl() # BLE controller
    ble.agent_on() # BLE agent on
    ble.default_agent() # set BLE agent
    ble.make_discoverable() # make RPi discoverable
    ble.start_scan() # start BLE scan
    devs = ble.get_available_devices() # get all devices from scan
    #
    ################################
    # Look for device named WaWiCo
    ################################
    #
    for dev_ii in devs:
        if dev_ii['name']=='WaWiCo': # look for WaWiCo Arduino BLE device
            dev_name = dev_ii['name']
            dev_addr = dev_ii['mac_address']
            print('Device Name: {}, Mac Address: {}'.\
                  format(dev_ii['name'],dev_ii['mac_address']))
    if ble.get_paired_devices()!=[]:
        ble.remove(dev_addr) # remove any other BLE devices
    print("Trying to connect to {0} ({1})".format(dev_name,dev_addr))
    conn_status = ble.connect(dev_addr) # connect to BLE device
    #
    #########################
    # Handling the connection
    #########################
    #
    if conn_status: # enter comm if connection is successful
        print('Connected to {} and Listening for Data...'.format(dev_name))
        gatt = Gattctl() # BLE comm
        gatt_menu = gatt.get_output("menu gatt") # enter BLE comm
        for ii in gatt_menu:
##            print(ii) # print out all BLE options
            pass
        gatt_attrs = gatt.get_output("list-attributes")
        for jj in gatt_attrs:
##            print(jj) # print out avilable BLE attributes
            pass
        service_attrs,char_attrs,char_UUIDs = [],[],[]
        for attrs_ii in range(0,len(gatt_attrs)):
            if gatt_attrs[attrs_ii]=='Characteristic':
                char_attrs.append(gatt_attrs[attrs_ii+1]) # all characteristics
                char_UUIDs.append(gatt_attrs[attrs_ii+2]) # all UUIDs
        gatt.get_output("select-attribute "+char_UUIDs[0]) # select char for RX
        gatt.get_output("notify on") # notify on for BLE char
        #
        #########################
        # Parsing Arduino Data
        #########################
        #
        while True: # loop that listens for data from Arduino
            try:
                output = gatt.get_output("")
                if len(output)!=3:
                    continue
                if output[0].split(' ')[2]=='Attribute' and\
                   output[0].split(' ')[4]=='Value:':
                    val = output[1][-16:].replace(' ','')
                    print('Data: {}'.format(val)) # print out data
            except:
                disconnect() # disconnect BLE device from RPi
                print("Disconnected from {0} ({1})".format(dev_name,dev_addr))
                break # exit loop

