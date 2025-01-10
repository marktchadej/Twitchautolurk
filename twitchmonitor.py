import os
import sys
import time
import requests
import configparser
import subprocess
import psutil
import pychrome
import threading

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

# Function to get all open URLs in Chrome/Chromium windows using Chrome DevTools Protocol
def get_open_urls():
    urls = []
    try:
        browser = pychrome.Browser(url="http://127.0.0.1:9222")
        tabs = browser.list_tab()
        for tab in tabs:
            if tab.url and (tab.url.startswith('http://') or tab.url.startswith('https://')):
                urls.append(tab.url)
    except Exception as e:
        print(f"Error getting URLs: {str(e)}")
    return urls

# Function to close all Chrome/Chromium browsers
def close_all_browsers():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] in ['chrome.exe', 'chromium.exe']:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except psutil.NoSuchProcess:
                pass
            except psutil.TimeoutExpired:
                pass

# Function to reopen browser windows with given URLs
def reopen_browsers_with_urls(urls):
    for url in urls:
        subprocess.Popen(['C:/Program Files/Google/Chrome/Application/chrome.exe', '--new-window', url])

# Function to handle keyboard input
def listen_for_q():
    while True:
        if input().lower() == 'q':
            global stop_thread
            stop_thread = True
            break

# Get the access token
access_token = get_access_token(client_id, client_secret)

# Dictionary to track which streamers are live and their process objects
opened_streamers = {streamer: None for streamer in streamer_names}

# Flag to indicate when to stop the script
stop_thread = False

# Start the thread to listen for 'q' key press
listener_thread = threading.Thread(target=listen_for_q)
listener_thread.start()

# Polling loop
while not stop_thread:
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f'{"Streamer":<20}{"Status":<10}')
    print('-' * 30)
    info_messages = []
    for streamer_name in streamer_names:
        if check_if_live(access_token, client_id, streamer_name):
            if not opened_streamers[streamer_name]:
                info_messages.append(f'{streamer_name} is live! Opening stream...')
                process = subprocess.Popen(['C:/Program Files/Google/Chrome/Application/chrome.exe', '--new-window', f'https://www.twitch.tv/{streamer_name}'])
                opened_streamers[streamer_name] = process
            status = f'{GREEN}online{RESET}'
        else:
            if opened_streamers[streamer_name]:
                info_messages.append(f'{streamer_name} is offline. Taking note of all open URLs, closing browsers, and reopening remaining URLs...')
                open_urls = get_open_urls()
                filtered_urls = [url for url in open_urls if streamer_name.lower() not in url.lower()]
                close_all_browsers()
                reopen_browsers_with_urls(filtered_urls)
                opened_streamers[streamer_name] = None
            status = f'{RED}offline{RESET}'
        print(f'{streamer_name:<20}{status:<10}')
    print('\nInfo:')
    print('-' * 30)
    for message in info_messages:
        print(message)
    print('\nPress Q to exit.')
    print('\nChecking again in 30 seconds...')
    time.sleep(30)

print('Script terminated by user.')
