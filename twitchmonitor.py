import os
import sys
import time
import requests
import configparser
import logging

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

# Dictionary to track which streamers are live
opened_streamers = {streamer: False for streamer in streamer_names}

# Polling loop
while True:
    for streamer_name in streamer_names:
        if check_if_live(access_token, client_id, streamer_name):
            if not opened_streamers[streamer_name]:
                print(f'{streamer_name} is live!')
                opened_streamers[streamer_name] = True
            else:
                print(f'{streamer_name} is still live. Checking again in 30 seconds...')
        else:
            if opened_streamers[streamer_name]:
                print(f'{streamer_name} is offline.')
                opened_streamers[streamer_name] = False
            else:
                print(f'{streamer_name} is still offline.')
    print('Checking again in 30 seconds...')
    time.sleep(30)
