import os
import sys
import time
import requests
import configparser
import subprocess
import threading
import logging
import psutil
from collections import deque
from datetime import datetime

# Set up logging
logging.basicConfig(filename='streamer_script.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from config.conf
config = configparser.ConfigParser()
config.read('config.conf')

# Your Twitch app credentials from the config file
client_id = config['Credentials']['client_id']
client_secret = config['Credentials']['client_secret']
streamer_names = config['Streamers']['streamers'].split(', ')  # List of streamers

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

# Authenticate and get an access token
def get_access_token(client_id, client_secret):
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    return response.json()['access_token']

# Function to check if the streamer is live
def check_if_live(access_token, client_id, streamer_name):
    url = f'https://api.twitch.tv/helix/streams?user_login={streamer_name}'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response_data = response.json()
    if 'data' in response_data:
        data = response_data['data']
        return len(data) > 0
    return False

# Function to get the PID of the Chrome window with the matching URL
def get_pid_by_url(url):
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'chrome' in proc.info['name'].lower():
                if url in proc.info['cmdline']:
                    logging.debug(f"Found Chrome PID: {proc.info['pid']} for URL: {url}")
                    return proc.info['pid']
    except Exception as e:
        logging.error(f"Error getting PID for URL {url}: {str(e)}")
    return None

# Function to terminate a process by PID
def terminate_process_by_pid(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        logging.info(f"Terminated process with PID: {pid}")
    except Exception as e:
        logging.error(f"Error terminating process with PID: {pid} - {str(e)}")

# Function to handle keyboard input
def listen_for_enter():
    input()
    global stop_thread
    stop_thread = True

# Get the access token
access_token = get_access_token(client_id, client_secret)

# Dictionary to track which streamers are live and their opened URLs
opened_streamers = {streamer: None for streamer in streamer_names}

# Deque to store the last 10 messages
info_messages = deque(maxlen=10)

# Flag to indicate when to stop the script
stop_thread = False

# Start the thread to listen for Enter key press
listener_thread = threading.Thread(target=listen_for_enter)
listener_thread.start()

# Polling loop
while not stop_thread:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'{"Streamer":<20}{"Status":<10}')
    print('-' * 30)
    for streamer_name in streamer_names:
        is_live = check_if_live(access_token, client_id, streamer_name)
        if is_live:
            if not opened_streamers[streamer_name]:
                message = f'{streamer_name} is live! Opening stream...'
                logging.info(message)
                timestamped_message = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {message}'
                info_messages.appendleft(timestamped_message)
                process = subprocess.Popen(['C:/Program Files/Google/Chrome/Application/chrome.exe', 
                                            '--new-window', 
                                            f'https://www.twitch.tv/{streamer_name}'])
                opened_streamers[streamer_name] = process.pid
            status = f'{GREEN}online{RESET}'
        else:
            if opened_streamers[streamer_name]:
                message = f'{streamer_name} is offline. Closing their specific browser window...'
                logging.info(message)
                timestamped_message = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {message}'
                info_messages.appendleft(timestamped_message)
                pid = opened_streamers[streamer_name]
                if pid:
                    terminate_process_by_pid(pid)
                opened_streamers[streamer_name] = None
            status = f'{RED}offline{RESET}'
        print(f'{streamer_name:<20}{status:<10}')
    
    # Display the "Info" section
    print('\nInfo:')
    for msg in info_messages:
        print(msg)
        
    print('\nPress Enter to exit.')
    print('\nChecking again in 30 seconds...')
    time.sleep(30)

print('Script terminated by user.')
