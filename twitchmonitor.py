import os
import sys
import time
import requests
import configparser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Suppress USB-related errors from Selenium logs
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Disable logging for Selenium
options.add_argument("--log-level=3")

# Set up Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Load configuration from config.conf
config = configparser.ConfigParser()
config.read('config.conf')

# Your Twitch app credentials from the config file
client_id = config['Credentials']['client_id']
client_secret = config['Credentials']['client_secret']
streamer_names = config['Streamers']['streamers'].split(', ')  # List of streamers

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
    else:
        print(f"Error: 'data' key not found in response for {streamer_name}.")
        return False

# Get the access token
access_token = get_access_token(client_id, client_secret)

# Dictionary to track which streamers have already been opened and their tabs
opened_streamers = {streamer: None for streamer in streamer_names}

# Polling loop
while True:
    for streamer_name in streamer_names:
        if check_if_live(access_token, client_id, streamer_name):
            if not opened_streamers[streamer_name]:
                print(f'{streamer_name} is live! Opening stream...')
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(f'https://www.twitch.tv/{streamer_name}')
                opened_streamers[streamer_name] = driver.current_window_handle
            else:
                print(f'{streamer_name} is still live. Checking again in 30 seconds...')
        else:
            if opened_streamers[streamer_name]:
                print(f'{streamer_name} is offline. Closing stream tab...')
                driver.switch_to.window(opened_streamers[streamer_name])
                driver.close()
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
                opened_streamers[streamer_name] = None
            else:
                print(f'{streamer_name} is still offline.')
    print('Checking again in 30 seconds...')
    time.sleep(30)
