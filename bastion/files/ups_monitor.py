import subprocess
import requests
import socket
import os
import re
import time

# Check if the server startup notification has been sent
def read_server_startup_notification_state(file_path):
    return os.path.exists(file_path)

# Mark the server startup notification as sent
def mark_server_startup_notification_sent(file_path):
    with open(file_path, 'w') as file:
        file.write("sent")

# Set UPS server and address
UPS_SERVER = "servers@192.168.200.2"
STATUS_FILE = "./status_file.txt"  # Path to the file storing the last known status
SHUTDOWN_NOTIFICATION_FILE = "/tmp/shutdown_notification_sent.txt"  # Path to the file storing the shutdown notification state
SERVER_STARTUP_NOTIFICATION_FILE = "/tmp/server_startup_notification_sent.txt"  # Path to the file storing the server startup notification state
SERVER_STARTUP_NOTIFICATION_SENT = read_server_startup_notification_state(SERVER_STARTUP_NOTIFICATION_FILE)


# Slack Details
SLACK_URL = 'https://hooks.slack.com/services/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'
HEADERS = {'Content-Type': 'application/json'}


# Fetch UPS information
def fetch_ups_info(ups_server):
    result = subprocess.run(["upsc", ups_server], capture_output=True, text=True)
    return result.stdout

UPS_OUTPUT = fetch_ups_info(UPS_SERVER)
HOSTNAME = socket.gethostname()

# Extract battery.charge and ups.status
def extract_value(output, key):
    for line in output.splitlines():
        if line.startswith(key):
            return line.split(":")[1].strip()
    return None
try:
    BATTERY_CHARGE = int(extract_value(UPS_OUTPUT, "battery.charge"))
except TypeError:
    data = {
        "blocks": [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":x: Unable to Access the UPS from {HOSTNAME}"
                    }
                ]
            }
        ]
    }
    response = requests.post(SLACK_URL, json=data, headers=HEADERS)
    if response.status_code == 200:
        print("Slack notification for status change sent successfully.")
    else:
        print(f"Failed to send Slack notification for status change. Status code: {response.status_code}")
UPS_STATUS = extract_value(UPS_OUTPUT, "ups.status")

# Define the conditions
CHARGE_THRESHOLD = 20
STATUS_CONDITION = "OB DISCHRG"

# Read the last known status from the file
def read_last_status(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()
    return None

# Write the current status to the file
def write_current_status(file_path, status):
    with open(file_path, 'w') as file:
        file.write(status)

# Check if the shutdown notification has been sent
def read_shutdown_notification_state(file_path):
    return os.path.exists(file_path)

# Mark the shutdown notification as sent
def mark_shutdown_notification_sent(file_path):
    with open(file_path, 'w') as file:
        file.write("sent")

LAST_STATUS = read_last_status(STATUS_FILE)
SHUTDOWN_NOTIFICATION_SENT = read_shutdown_notification_state(SHUTDOWN_NOTIFICATION_FILE)

def wake_device(interface, mac_address):
    try:
        # Send the Wake-on-LAN packet using etherwake
        subprocess.run(["sudo", "etherwake", "-i", interface, "-b", mac_address, "-D"], check=True)
        print(f"Wake-on-LAN packet sent to {mac_address} on {interface}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send WOL packet to {mac_address} on {interface}: {e}")

def is_device_online(ip, timeout=5):
    # Ping the IP address with a specific timeout
    response = os.system(f"ping -c 1 -W {timeout} {ip} > /dev/null 2>&1")
    return response == 0

def wake_and_verify(interface, mac_address, ip_address, name, wait_time=600):
    wake_device(interface, mac_address)

    # Wait a short period before starting to ping
    time.sleep(10)

    # Check if the device is online, retrying during the wait time
    for _ in range(wait_time // 5):
        if is_device_online(ip_address):
            print(f"Device with IP {ip_address} is now online.")
            data = {
                "blocks": [
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f":zap: SERVER STARTUP: Device named {name} is now online from {HOSTNAME}"
                            }
                        ]
                    }
                ]
            }
            response = requests.post(SLACK_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                print("Slack notification for server startup sent successfully.")
                mark_server_startup_notification_sent(SERVER_STARTUP_NOTIFICATION_FILE)
            else:
                print(f"Failed to send Slack notification for server startup. Status code: {response.status_code}")
            return True
        print(f"Waiting for device with IP {ip_address} to come online...")
        time.sleep(5)

    print(f"Device with IP {ip_address} did not come online within {wait_time} seconds.")
    return False

# Define devices with their MAC addresses and corresponding IP addresses
devices = [
    {"interface": "eth0.400", "mac": "00:11:32:92:91:15", "ip": "10.211.211.10", "name": "Synology NAS"},
    {"interface": "eth0.100", "mac": "D8:43:AE:1B:25:E3", "ip": "10.10.10.100", "name": "Proxmox Server"}
]

# Send server startup notification if not already sent
if not SERVER_STARTUP_NOTIFICATION_SENT:
    data = {
        "blocks": [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":zap: SERVER STARTUP: Battery charge is {BATTERY_CHARGE}% and UPS status is {UPS_STATUS} on {HOSTNAME}"
                    }
                ]
            }
        ]
    }
    response = requests.post(SLACK_URL, json=data, headers=HEADERS)
    if response.status_code == 200:
        print("Slack notification for server startup sent successfully.")
        mark_server_startup_notification_sent(SERVER_STARTUP_NOTIFICATION_FILE)
    else:
        print(f"Failed to send Slack notification for server startup. Status code: {response.status_code}")

    for device in devices:
        success = wake_and_verify(device["interface"], device["mac"], device["ip"], device["name"])
        if not success:
            print(f"Failed to wake and verify device: {device['name']}")

            data = {
                "blocks": [
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f":zap: SERVER STARTUP: Battery charge is {BATTERY_CHARGE}% and UPS status is {UPS_STATUS} on {HOSTNAME}"
                            }
                        ]
                    }
                ]
            }
            response = requests.post(SLACK_URL, json=data, headers=HEADERS)
            if response.status_code == 200:
                print("Slack notification for server startup sent successfully.")
                mark_server_startup_notification_sent(SERVER_STARTUP_NOTIFICATION_FILE)
            else:
                print(f"Failed to send Slack notification for server startup. Status code: {response.status_code}")
            break  # Stop if a device is not verified to be online before moving to the next one


# Check if the status has changed
if UPS_STATUS != LAST_STATUS:
    data = {
        "blocks": [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":zap: UPS STATUS CHANGE (:low_battery: Battery: {BATTERY_CHARGE}%, Status: {UPS_STATUS}): on {HOSTNAME}"
                    }
                ]
            }
        ]
    }
    response = requests.post(SLACK_URL, json=data, headers=HEADERS)
    if response.status_code == 200:
        print("Slack notification for status change sent successfully.")
    else:
        print(f"Failed to send Slack notification for status change. Status code: {response.status_code}")

    # Update the last known status
    write_current_status(STATUS_FILE, UPS_STATUS)

# Check conditions for shutdown
if BATTERY_CHARGE < CHARGE_THRESHOLD and UPS_STATUS == STATUS_CONDITION:
    print(f"Battery charge is below {CHARGE_THRESHOLD}% and UPS is on battery (discharging).")
    print("Shutting down the Bastion...")

    if not SHUTDOWN_NOTIFICATION_SENT:
        # Send Slack notification for shutdown
        data = {
            "blocks": [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f":zap: UPS POWER FAILURE (:low_battery: Battery: {BATTERY_CHARGE}%, Status: {STATUS_CONDITION}%): Shutting down {HOSTNAME}"
                        }
                    ]
                }
            ]
        }
        response = requests.post(SLACK_URL, json=data, headers=HEADERS)
        if response.status_code == 200:
            print("Slack notification for shutdown sent successfully.")
            mark_shutdown_notification_sent(SHUTDOWN_NOTIFICATION_FILE)
        else:
            print(f"Failed to send Slack notification for shutdown. Status code: {response.status_code}")
else:
    print(f"Conditions not met. Battery charge: {BATTERY_CHARGE}%, UPS status: {UPS_STATUS}.")
