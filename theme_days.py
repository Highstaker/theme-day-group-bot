#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import logging
from inspect import getargspec

from config import THEME_DAYS_FILENAME, DAYS_OF_WEEK


def theme_day_constructor(name=None, desc=None):
	return dict(name=name,
		desc=desc if desc else "",
		) if name else None

THEME_DAYS = [
# 0 - monday
None,
# 1 - tuesday
theme_day_constructor(name=u"🚫🇬🇧🚫No English Tuesday🚫🇬🇧🚫",
	desc="A day where we purposefully don't speak English as an exercise in practicing our target languages together.",
	),
# 2 - wednesday
None,
# 3 - thursday
None,
# 4 - friday
None,
# 5 - saturday
None,
# 6 - sunday
None,
]


def load_from_file():
	try:
		with open(THEME_DAYS_FILENAME, 'r') as f:
			for day_n, line in enumerate(f):
				if day_n >= len(THEME_DAYS):
					# there are more than 7 lines in the file, ignore the rest
					break

				# split and remove the first element, 
				# it is a day of week, it's just for convinience in the file.
				parse = line.strip().split("@@")[1:]

				# ['name', 'desc']
				constructor_args = getargspec(theme_day_constructor).args
				params = [None] * len(constructor_args)
				try:
					for n, el in enumerate(parse):
						params[n] = el
				except IndexError:
					logging.info("Not all data is specified for {}".format(DAYS_OF_WEEK[day_n]))

				THEME_DAYS[day_n] = theme_day_constructor(*params)
			logging.debug("THEME_DAYS: {}".format(THEME_DAYS))
	except IOError:
		logging.warning("No theme days file found. Loading defaults!")

load_from_file()
