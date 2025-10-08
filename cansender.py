#!/usr/bin/env python3
from asammdf import MDF
import requests
import json
import sys
import time
from datetime import datetime
import numpy as np


# Configuration - UPDATE THIS IP ADDRESS
# AZURE_SERVER_URL = "http://4.147.153.81:80/can"  # vserver under Sandhy's Azure
AZURE_SERVER_URL = "http://20.211.145.100:80/can"  # vserver under Kangjing's Azure'
DEVICE_ID = "IR1835"
SEND_INTERVAL = 1  # Send data every SEND_INTERVAL seconds
REQUEST_TIMEOUT = 10


# RUN CAN sender
def periodic_sender(candata, send_channels):

    # Read multiple channels, save the interested data and send out
    # channels = ["time", "STEER_RATE", "STEER_ANGLE", "ENGINE_RPM"]
    signals = {}
    for channel in send_channels:
        if channel in candata.channels_db:
            signals[channel] = candata.get(channel)
        else:
            print(f"Channel {channel} not found")

    print("Info: ", candata.info())

    min_sample = len(signals[send_channels[0]])
    for channel in send_channels:
        if min_sample < len(signals[channel]):
            min_sample = len(signals[channel])

    for ind in range(0, min_sample):
        can_data = {
            send_channels[0]: signals[send_channels[0]].samples[ind],
            send_channels[1]: int(signals[send_channels[1]].samples[ind]),  # Convert uint8 to int for JSON
            send_channels[2]: signals[send_channels[2]].samples[ind]
        }

        try:
            response = requests.post(
                AZURE_SERVER_URL,
                json=can_data,
                timeout=REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                print(f"CAN data sent to Azure: "
                      f"\n{send_channels[0]}: {can_data[send_channels[0]]:.1f}"
                      f"\n{send_channels[1]}: {can_data[send_channels[1]]:.1f}"
                      f"\n{send_channels[2]}: {can_data[send_channels[2]]:.4f} \n")
                # return True
            else:
                print(f"Azure server error: HTTP {response.status_code}")
                # return False

        except requests.exceptions.Timeout:
            print("Timeout sending to Azure server")
        except requests.exceptions.ConnectionError:
            print("Connection error to Azure server")
        except Exception as e:
            print(f"Error sending to Azure server: {e}")
        except KeyboardInterrupt:
            print("\nShutting down CAN sender...")

        for i in range(SEND_INTERVAL):
            time.sleep(1)


if __name__ == "__main__":

    print("IR1835 CAN Test Application Started")

    # Validate configuration
    if "YOUR_AZURE_VM_IP" in AZURE_SERVER_URL:
        print("ERROR: Please update AZURE_SERVER_URL with your actual Azure VM IP address!")
        print(f"Current URL: {AZURE_SERVER_URL}")
        sys.exit(1)

    # Test Azure server connectivity
    print("Testing connection to Azure server...")
    try:
        response = requests.get(AZURE_SERVER_URL.replace('/gps', '/health'), timeout=5)
        if response.status_code == 200:
            print("Azure server is reachable")
        else:
            print(f"Azure server responded with status {response.status_code}")
    except Exception as e:
        print(f"Cannot reach Azure server: {e}")
        print("Continuing anyway - will retry when GPS data is available")

    select_channels = ["STEER_DIRECTION", "BRAKE_POSITION", "WHEEL_SPEED_FL"]
    obd2_data = MDF("mercedes.mf4", channels=select_channels)
    # obd2_full = MDF("mercedes.mf4")
    print("=" * 60)
    print("         CAN Data Sender to Azure")
    print("=" * 60)
    print(f"Device ID: {DEVICE_ID}")
    print(f"Azure Server: {AZURE_SERVER_URL}")
    print(f"Send Interval: {SEND_INTERVAL} seconds")
    print("=" * 60)
    try:
        periodic_sender(obd2_data, select_channels)
    except KeyboardInterrupt:
        print("\nShutting down CAN sender...")

    print("Test completed - Application finished successfully")
