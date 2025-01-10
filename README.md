# Twitchautolurk
Create a list of streamers and have this python script check if they're streaming. Will open the stream when they come online in your default browser.

## Requirements
1. [Python 3](https://www.python.org/downloads/) installed
2. Run `pip install psutil`
3. Run `pip install pychrome`

## Setting up
1. Go to the twitch dev console [here](https://dev.twitch.tv/console)
2. Create a new application, set your OAuth Redirect URLs to http://localhost:3000
3. Note your client ID and create a new secret and take note of it (keep it secret, keep it safe!)
4. Edit config.conf and enter your client ID and client secret in the provided fields
5. Populate your list with as many streamers as you want in the provided field in config.conf
6. From command line in the location of the script type
   `python twitchmonitor.py`
7. Enjoy! 
