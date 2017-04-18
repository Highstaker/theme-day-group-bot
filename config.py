#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

with open("token.txt", 'r') as f:
	BOT_TOKEN = f.read().strip()

DAY_MARGIN = 2  # seconds to add to the next day to guarantee that it fires the next day
JOB_INTERVAL = 60  # seconds between checks of the next day

CHAT_DATA_FILENAME = "chat_data.save"
THEME_DAYS_FILENAME = "theme_days.csv"

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

HELP_TEXT = """Commands that can be used are:
/help - shows the list of commands
/themedaylist - returns a list with descriptions of current theme days
/update - updates the pinned message. If the pinned message is not accessible, the bot resends it and asks to pin it.
"""

# This will be added to HELP_TEXT if the user is an admin.
HELP_ADMINS = """
/start - starts the bot (Admins Only)
/pinned - equivalent to /update, except it sets the flag to remove the auxiliary text (like "PIN THIS MESSAGE").
/force_update - resend the message in any case, don't update the old one even if it is available.
"""