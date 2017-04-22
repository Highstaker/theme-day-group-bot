
# Theme day bot

## Overview

This bot sets themes for the group chat.

## Deployment

### Tested systems

This bot has been tested on Ubuntu 14.04 and Python 2.7

### Dependencies

To install requirements, run
```
pip2 install -r requirements.txt
```

## Installation

### Setting up the bot token

Create a file called `token.txt` and put it into the folder with the bot. Input (or copy/paste) the bot token in it.

### Setting up the theme days

Perform `cp theme_days.csv.sample theme_days.csv` and edit the new file. The fields are separated by `@@`. The first field is the day of week, it's just for convenience and is ignored by the program. The second field is the name of a theme day. The third field is its detailed description, it is optional. In the sample, Monday and Tuesday have both a name and a description. Thursday has only a name. Other days are themeless.

### Tieing to group

Use `/start` command to tie the bot to your group. It will send a hello message and a message with today's theme. The admin should pin it and issue a `/pinned` command. This will update the message, removing the garbage, like "PIN THIS MESSAGE" text and mentions of admins. From this point onwards, the bot will update the pinned message every day automatically, whenever it is required.

## Bot's behaviour

The bot updates the pinned message every day at midnight UTC, when required. 

- If the new day has a theme, the pinned message is updated to show the theme. 
- If the new day has no theme, but the previous day had one, the bot the info message saying that the theme day has ended (this info message is not supposed to b pinned, it's just a notification for group members)
- If neither the previous day nor the new day has any themes, does nothing.
