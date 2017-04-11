#/bin/bash

mkdir logs
env32_2/bin/python2 theme_day_bot.py "$@" >> logs/theme_day_bot.log 2>&1

exit 0

