#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#############################################
#    Theme day bot code for Polyglot Furries
#    Date of last update: 29/03/2017
#    Authors: @LucianLutrae @Highstaker
#############################################

import os
from time import time
import logging
from datetime import datetime, timedelta
import pickle
from argparse import ArgumentParser

from telegram import TelegramError
from telegram.ext import Updater, CommandHandler, Job, JobQueue

import config

arg_parser = ArgumentParser()
arg_parser.add_argument("--debug",  action='store_true', dest="debug_mode")
args = arg_parser.parse_args()

if args.debug_mode:
	logging_level = logging.DEBUG
else:
	logging_level = logging.WARNING

logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
					level=logging_level)


VERSION = (0, 1, 10)


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

		self.load_chat_data()

		self.run()

	def setup_bot(self, bot, chat_id=None):
		if chat_id:
			self.group_chat_id = chat_id
		# self.save_chat_data() # not needed in this version, but may be required in the future
		self.check_set_theme_day(bot, force_schedule=True)
		self.bot_is_setup = True

	def load_chat_data(self):
		try:
			with open(config.CHAT_DATA_FILENAME, "r") as f:
				data = pickle.load(f)
			self.group_chat_id = data['group_chat_id']
			self.pinned_message_id = data['pinned_message_id']
			self.setup_bot(self.updater.bot)
		except IOError:
			logging.warning("No chat data savefile found. Need initialization!")
			self.group_chat_id = None
			self.pinned_message_id = None

	def save_chat_data(self):
		data = dict()

		data['pinned_message_id'] = self.pinned_message_id
		data['group_chat_id'] = self.group_chat_id

		with open(config.CHAT_DATA_FILENAME, "w") as f:
			pickle.dump(data, f)

	def idle_with_exiter(self):
		"""Have to call hard exit, or else it freezes after exiting idle()"""
		self.updater.idle()
		os._exit(0)

	def run(self):
		self.updater.start_polling()
		self.idle_with_exiter()

	def isAdmin(self, bot, update):
		"""
		Returns True if the user in the update is admin. False otherwise.
		Returns None if it is not a group chat.
		"""
		chat_id=update.message.chat_id
		if chat_id < 0:
			admins_list = bot.getChatAdministrators(chat_id)  # raises error in private chats
			user_sent = update.message.from_user
			user_id = user_sent.id
			is_admin = user_id in [i.user.id for i in admins_list]
			return is_admin
		else:
			return None


	def start(self, bot, update):
		chat_id=update.message.chat_id

		if chat_id>0:
			#it is a private chat
			msg = "This bot is supposed to be run in a supergroup chat."
			bot.sendMessage(chat_id=chat_id, text=msg)
		else:
			#it is a group chat
			is_admin = self.isAdmin(bot, update)

			if is_admin:
				if self.bot_is_setup:
					msg = "The bot is already set up!"
				else:
					self.setup_bot(bot, chat_id)
					msg = """Hello, I am a bot that sets theme days for the Polyglot Furries Channel! 
I have been set up to run this group! 
Thanks for running me, and have a good day!
"""

				bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def help_function(self, bot, update):
		is_admin = self.isAdmin(bot, update)
		bot.sendMessage(chat_id=update.message.chat_id, text=config.HELP_TEXT \
			+ (config.HELP_ADMINS if is_admin else ""))

	def theme_day_list(self, bot, update):
		msg = "\n".join(u"{0} - {1}".format(i['name'], i['desc']) for i in config.THEME_DAYS if i)
		bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def error_handler(self, bot, update, error):
		if update:
			logging.warning('Update "%s" caused error "%s"' % (update, error))
			if "/update" in update.message.text:
				#the message to edit is no longer available, let's make a new one.
				#I'm not sure about the particular errors it may raise
				#Maybe the condition checking needs to be expanded, dunno
				self.pinned_message_id = None
				self.check_set_theme_day(bot)

	def update_today_message(self, bot, update):
		"""A command to update the today's message.
		Most likely users won't have to use it, as the bot can update it automatically.
		"""
		if self.bot_is_setup:
			self.check_set_theme_day(bot)

	def editPinnedMessage(self, bot, text):
		# Prevents error that is raised when we try editing a message and applying the same text to it.
		try:
			bot.editMessageText(text=text, chat_id=self.group_chat_id, message_id=self.pinned_message_id)
		except TelegramError, e:
			if "message is not modified" in str(e):
				logging.warning("message is the same")
			else:
				raise e

	def check_set_theme_day(self, bot, job=None, force_schedule=False):
		weekday = get_weekday()
		theme_day = config.THEME_DAYS[weekday]

		if theme_day:
			msg = u"{0}\n{1}".format(theme_day['name'], theme_day['desc'])
		else:
			msg = u"No theme today." 

		msg += "\n\nPIN THIS MESSAGE!" 

		# msg = str(time()) + msg # debug

		if self.pinned_message_id:
			self.editPinnedMessage(bot, text=msg)
		else:
			sent_message = bot.sendMessage(chat_id=self.group_chat_id, text=msg)
			self.pinned_message_id = sent_message.message_id
			self.save_chat_data()

		if job or force_schedule:
			# reset the job only if it is run by a job scheduler
			interval = seconds_till_next_day()+config.DAY_MARGIN
			next_job = Job(self.check_set_theme_day, interval=interval, repeat=False)
			self.new_day_notify_job_queue.put(next_job)

if __name__ == '__main__':
	ThemeDayBot()
