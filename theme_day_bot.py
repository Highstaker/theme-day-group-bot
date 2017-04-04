#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#############################################
#    Theme day bot code for Polyglot Furries
#    Date of last update: 29/03/2017
#    Authors: @LucianLutrae @Highstaker
#############################################

from time import time
import logging
from datetime import datetime, timedelta

from telegram.ext import Updater, CommandHandler, Job, JobQueue

import config

logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
					level=logging.INFO)

VERSION = (0, 1, 3)


def seconds_till_next_day():
	cur_time = datetime.now()
	result = (cur_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1) - cur_time).seconds
	return result

def get_weekday():
	return datetime.now().weekday()


class ThemeDayBot(object):
	"""docstring for ThemeDayBot"""
	def __init__(self):
		super(ThemeDayBot, self).__init__()

		self.updater = Updater(token=config.BOT_TOKEN)
		self.dispatcher = self.updater.dispatcher
		self.dispatcher.add_handler(CommandHandler('start', self.start))
		self.dispatcher.add_handler(CommandHandler('help', self.help_function))
		self.dispatcher.add_handler(CommandHandler('themedaylist', self.theme_day_list))
		self.dispatcher.add_handler(CommandHandler('update', self.update_today_message))

		self.dispatcher.add_error_handler(self.error_handler)

		# queue handling new day notification tasks
		self.new_day_notify_job_queue = JobQueue(self.updater.bot)
		self.new_day_notify_job_queue.start()

		self.bot_is_setup = False

		self.pinned_message_id = None

		self.run()

	def run(self):
		self.updater.start_polling()
		self.updater.idle()

	def start(self, bot, update):
		chat_id=update.message.chat_id

		if chat_id>0:
			#it is a private chat
			msg = "This bot is supposed to be run in a supergroup chat."
			bot.sendMessage(chat_id=chat_id, text=msg)
		else:
			#it is a group chat
			admins_list = bot.getChatAdministrators(chat_id)  # raises error in private chats
			user_sent = update.message.from_user
			user_id = user_sent.id
			is_admin = user_id in [i.user.id for i in admins_list]

			if is_admin:
				if self.bot_is_setup:
					msg = "The bot is already set up!"
				else:
					self.group_chat_id = chat_id
					self.check_set_theme_day(bot, force_schedule=True)
					msg = """Hello, I am a bot that sets theme days for the Polyglot Furries Channel! 
I have been set up to run this group! 
Thanks for running me, and have a good day!
"""
					self.bot_is_setup = True

				bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def help_function(self, bot, update):
		bot.sendMessage(chat_id=update.message.chat_id, text='Commands that can be used are:\n /start - starts the bot (Admins Only)\n /help - gets the list of commands\n /startnoenglishtuesday - Tells bot to generate an automated message for the theme day \"No English Tuesday\" (Admin only)\n /themedaylist - returns a list with descriptions of current theme days')

	def theme_day_list(self, bot, update):
		msg = "\n".join(u"{0} - {1}".format(i['name'], i['desc']) for i in config.THEME_DAYS if i)
		bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def error_handler(self, bot, update, error):
		logging.warn('Update "%s" caused error "%s"' % (update, error))
		if "/update" in update.message.text:
			#the message to edit is no longer available, let's make a new one.
			#I'm not sure about the particular errors it may raise
			#Maybe the condition checking needs to be expanded, dunno
			self.pinned_message_id = None
			self.check_set_theme_day(bot)

	def update_today_message(self, bot, update):
		if self.bot_is_setup:
			# try:
			# 	# run it as a job from a queue and then remove it
			# 	logging.debug(self.new_day_notify_job_queue.jobs())#debug
			# 	job = self.new_day_notify_job_queue.jobs()[0]
			# 	job.run(bot)
			# 	job.schedule_removal()
			# 	self.new_day_notify_job_queue.tick()
			# 	#TODO: it won't remove the jobs! DX
			# except IndexError:
				# this should not happen, but if the queue is empty, then just run the function directly
			
			print self.new_day_notify_job_queue.jobs()#debug
			self.check_set_theme_day(bot)

	def check_set_theme_day(self, bot, job=None, force_schedule=False):
		weekday = get_weekday()
		theme_day = config.THEME_DAYS[weekday]

		if theme_day:
			msg = u"{0}\n{1}".format(theme_day['name'], theme_day['desc'])
		else:
			msg = "No theme today." 

		msg += "\n\nPIN THIS MESSAGE!" 

		msg = str(time()) + msg # debug

		if self.pinned_message_id:
			bot.editMessageText(text=msg, chat_id=self.group_chat_id, message_id=self.pinned_message_id)
		else:
			sent_message = bot.sendMessage(chat_id=self.group_chat_id, text=msg)
			self.pinned_message_id = sent_message.message_id

		if job or force_schedule:
			# reset the job only if it is run by a job scheduler
			interval = seconds_till_next_day()+config.DAY_MARGIN
			# interval = 15#debug
			next_job = Job(self.check_set_theme_day, interval=interval, repeat=False)
			self.new_day_notify_job_queue.put(next_job)

if __name__ == '__main__':
	ThemeDayBot()
