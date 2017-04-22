#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

#############################################
#    Theme day bot
#    Date of last update: 29/03/2017
#    Authors: @LucianLutrae @Highstaker
#############################################

import logging
import os
from datetime import datetime, timedelta
import pickle
from argparse import ArgumentParser

arg_parser = ArgumentParser()
arg_parser.add_argument("--debug", action='store_true', dest="debug_mode")
args = arg_parser.parse_args()

if args.debug_mode:
	logging_level = logging.DEBUG
else:
	logging_level = logging.WARNING

logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
					level=logging_level)

from telegram import TelegramError
from telegram.ext import Updater, CommandHandler, Job, JobQueue

import config
from theme_days import THEME_DAYS

VERSION = (0, 2, 3)


def seconds_till_next_day():
	cur_time = datetime.now()
	result = (cur_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1) - cur_time).seconds
	logging.debug("Seconds left till next day: {}".format(result))
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
		self.dispatcher.add_handler(CommandHandler('update', self.update))
		self.dispatcher.add_handler(CommandHandler('force_update', self.force_update))
		self.dispatcher.add_handler(CommandHandler('pinned', self.pinned))

		self.dispatcher.add_error_handler(self.error_handler)

		self.current_weekday = get_weekday()

		# queue handling new day notification tasks
		self.new_day_notify_job_queue = JobQueue(self.updater.bot)
		self.new_day_notify_job_queue.start()

		self.bot_is_setup = False

		self.pinned_message_id = None
		self.pinned = False  # is the message pinned? If yes, remove garbage from it.

		self.load_chat_data()

		self.run()

	def setup_bot(self, bot, chat_id=None):
		if chat_id:
			self.group_chat_id = chat_id
		# self.save_chat_data() # not needed in this version, but may be required in the future
		self.reset_job()
		self.bot_is_setup = True

	def load_chat_data(self):
		try:
			with open(config.CHAT_DATA_FILENAME, "r") as f:
				data = pickle.load(f)
			self.group_chat_id = data['group_chat_id']
			self.pinned_message_id = data['pinned_message_id']
			self.pinned = data['message_is_pinned']
			self.setup_bot(self.updater.bot)
		except IOError:
			logging.warning("No chat data savefile found. Need initialization!")
			self.group_chat_id = None
			self.pinned_message_id = None

	def save_chat_data(self):
		data = dict()

		data['pinned_message_id'] = self.pinned_message_id
		data['group_chat_id'] = self.group_chat_id
		data['message_is_pinned'] = self.pinned

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
		chat_id = update.message.chat_id
		if chat_id < 0:
			admins_list = bot.getChatAdministrators(chat_id)  # raises error in private chats
			user_sent = update.message.from_user
			user_id = user_sent.id
			is_admin = user_id in [i.user.id for i in admins_list]
			return is_admin
		else:
			return None

	def start(self, bot, update):
		chat_id = update.message.chat_id

		if chat_id > 0:
			# it is a private chat
			msg = "This bot is supposed to be run in a supergroup chat."
			bot.sendMessage(chat_id=chat_id, text=msg)
		else:
			# it is a group chat
			is_admin = self.isAdmin(bot, update)

			if is_admin:
				if self.bot_is_setup:
					msg = "The bot is already set up!"
				else:
					self.setup_bot(bot, chat_id)
					msg = """I have been set up to run this group! 
Thanks for running me, and have a good day!
"""

				bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def help_function(self, bot, update):
		is_admin = self.isAdmin(bot, update)
		bot.sendMessage(chat_id=update.message.chat_id, text=config.HELP_TEXT
			+ (config.HELP_ADMINS if is_admin else ""))

	def theme_day_list(self, bot, update):
		no_theme_text = "[NO THEME]"
		day_messages = (u"{0} - {1}".format(i['name'], i['desc']) if i else no_theme_text for i in THEME_DAYS)
		day_messages = (u"{0}: {1}".format(config.DAYS_OF_WEEK[n], i) for n, i in enumerate(day_messages))

		msg = "\n\n".join(day_messages)
		bot.sendMessage(chat_id=update.message.chat_id, text=msg)

	def error_handler(self, bot, update, error):
		if update:
			logging.warning('Update "%s" caused error "%s"' % (update, error))
			if "/update" in update.message.text:
				# the message to edit is no longer available, let's make a new one.
				# I'm not sure about the particular errors it may raise
				# Maybe the condition checking needs to be expanded, dunno
				self.pinned_message_id = None
				self.check_set_theme_day(bot)

	def update(self, bot, update):
		"""A command to update the today's message.
		Most likely users won't have to use it, as the bot can update it automatically.
		"""
		if self.bot_is_setup:
			self.check_set_theme_day(bot)

	def force_update(self, bot, update):
		"""Like /update, but it resends the message (and reassigns variables)
		no matter what.
		"""
		if self.isAdmin(bot, update):
			if self.bot_is_setup:
				self.pinned = False
				self.check_set_theme_day(bot, force_resend=True)

	def pinned(self, bot, update):
		if self.isAdmin(bot, update):
			if self.bot_is_setup:
				self.pinned = True
				self.save_chat_data()
				self.check_set_theme_day(bot)

	def edit_pinned_message(self, bot, text):
		# Prevents error that is raised when we try editing a message and applying the same text to it.
		# Returns status 0, if modificaton occured, status 1 if the message is the same
		try:
			bot.editMessageText(text=text, chat_id=self.group_chat_id, message_id=self.pinned_message_id)
			status = 0
		except TelegramError, e:
			if "message is not modified" in str(e):
				logging.warning("message is the same")
				status = 1
			else:
				raise e
		return status

	def reset_job(self):
		"""Resets the job to either hard interval or time left until next day"""
		interval = min(seconds_till_next_day() + config.DAY_MARGIN, config.JOB_INTERVAL)
		next_job = Job(self.job_callback, interval=interval, repeat=False)
		self.new_day_notify_job_queue.put(next_job)

	def job_callback(self, bot, job):
		# Check if it is the next day
		if self.current_weekday != get_weekday():
			self.check_set_theme_day(bot)
			self.current_weekday = get_weekday()
		else:
			logging.info("The day is the same, the job did not do anything")
		self.reset_job()

	def compile_message(self, weekday, message_type="pinned", bot=None):
		"""
		Compiles a message about the theme day

		weekday: for which weekday the message should be compiled

		message type: what kind of message
		"pinned" is supposed to be pinned
		"info" is sent at the beginning of a day, just a notification, not for pinning
		It is sent when the new day has a theme.
		"info_end" is sent if the previous day had a theme but a new one doesn't.
		Notifies about the end of theme day, in other words. `weekday` is the previous day

		bot: needed to get admins in "pinned"
		"""
		theme_day = THEME_DAYS[weekday]

		msg = ""

		if message_type == "pinned":
			if theme_day:
				msg = u"{0}\n{1}".format(theme_day['name'], theme_day['desc'])
			else:
				msg = u"No theme today."
			msg = config.DAYS_OF_WEEK[weekday] + ": " + msg
			if not self.pinned:
				msg += "\n\nPIN THIS MESSAGE and press /pinned!"
				# poke admins so they would pin the message
				msg += "\n\n" + " ".join(
					"@{}".format(i.user.username) for i
					in bot.getChatAdministrators(self.group_chat_id)
					)
			# msg = str(time()) + msg # debug
		elif message_type == "info":
			msg = u"{0}\n{1}".format(theme_day['name'], theme_day['desc'])
			msg = config.DAYS_OF_WEEK[weekday] + ": " + msg
		elif message_type == "info_end":
			msg = u"{0}\nThis day has ended!\nThere is no theme today!".format(
				theme_day['name'], theme_day['desc'])

		return msg

	def check_send_info_message(self, bot):
		"""
		Sends an info message about the new day.
		If the new day is theme-less, says that the previous day has ended.
		If both the previous and new days are themeless, does nothing.
		Assumes that the new day has already come.
		"""
		new_day = get_weekday()
		prev_day = (new_day - 1) % 7

		if THEME_DAYS[new_day]:
			# if the new day has a theme, it doesn't matter whether the old one had it or not
			# just send the info message about the new day
			msg = self.compile_message(new_day, message_type="info")
			bot.sendMessage(chat_id=self.group_chat_id, text=msg)
		if not THEME_DAYS[new_day] and THEME_DAYS[prev_day]:
			# send notification about the end of the theme day
			msg = self.compile_message(prev_day, message_type="info_end")
			bot.sendMessage(chat_id=self.group_chat_id, text=msg)

	def check_set_theme_day(self, bot, force_resend=False):
		"""
		Sends message that is supposed to be pinned. Or updates it if it is already present.

		force_resend: don't update the old message. 
		Instead, send it again as if the previous were not available anymore.
		"""

		weekday = get_weekday()

		# compiling the message
		msg = self.compile_message(weekday, message_type="pinned", bot=bot)

		if self.pinned_message_id and not force_resend:
			edit_status = self.edit_pinned_message(bot, text=msg)
			if edit_status == 0:
				self.check_send_info_message(bot)
		else:
			sent_message = bot.sendMessage(chat_id=self.group_chat_id, text=msg)
			self.pinned_message_id = sent_message.message_id
			self.pinned = False
			self.save_chat_data()

if __name__ == '__main__':
	ThemeDayBot()
