#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

with open("token.txt", 'r') as f:
	BOT_TOKEN = f.read().strip()

DAY_MARGIN = 5  # seconds to add to the next day to guarantee that it fires the next day

CHAT_DATA_FILENAME = "chat_data.save"

def theme_day_constructor(name, desc=""):
	return dict(name=name,
		desc=desc,
		)

THEME_DAYS = [
#0 - monday
None,
#1 - tuesday
theme_day_constructor(name=u"🚫No English Tuesday🚫",
	desc="A day where we purposefully don't speak English as an exercise in practicing our target languages together.",
	),
#2 - wednesday
None,
#3 - thursday
None,
#4 - friday
None,
#5 - saturday
None,
#6 - sunday
None,
]
