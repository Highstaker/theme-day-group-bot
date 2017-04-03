#############################################
#    Theme day bot code for Polyglot Furries
#    Date of last update: 29/03/2017
#    Authors: @LucianLutrae @Highstaker
#############################################

import time
import logging

from telegram.ext import Updater, CommandHandler

import config

logging.basicConfig(format=u'[%(asctime)s] %(filename)s[LINE:%(lineno)d]# %(levelname)-8s  %(message)s',
                    level=logging.INFO)

VERSION = (0,1,1)

def wait_func(s):
    while(1):
        now = time.strftime("%H:%M")
        if now == s:
            break
        else:
            continue

def start(bot, update):
    chat_id=update.message.chat_id
    msg='Hello, I am a bot that sets theme days for the Polyglot Furries Channel! Thanks for running me, and have a good day!'

    if chat_id>0:
        #it is a private chat
        bot.sendMessage(chat_id=chat_id, text=msg)
    else:
        #it is a group chat
        admins_list = bot.getChatAdministrators(chat_id)#raises error in private chats
        user_sent = update.message.from_user
        user_id = user_sent.id

        is_admin = user_id in [i.user.id for i in admins_list]
        print is_admin #debug

        if is_admin:
            bot.sendMessage(chat_id=update.message.chat_id, text=msg)

def help_function(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text='Commands that can be used are:\n /start - starts the bot (Admins Only)\n /help - gets the list of commands\n /startnoenglishtuesday - Tells bot to generate an automated message for the theme day \"No English Tuesday\" (Admin only)\n /themedaylist - returns a list with descriptions of current theme days')

def startNoEnglishTuesday(bot, update):
    chat_id=update.message.chat_id
    admins_list = bot.getChatAdministrators(chat_id)
    user_sent = update.message.from_user
    message_id = update.message.message_id
    user_id = user_sent.id
    is_admin = user_id in [i.user.id for i in admins_list]
    print is_admin
    bot.sendMessage(chat_id=update.message.chat_id, text=''+('Timed message to be sent at 0:10 today' if is_admin else ''), reply_to_message_id=message_id)
    if is_admin:
        wait_func('00:10')
    bot.sendMessage(chat_id=update.message.chat_id, text=''+('Hello World!' if is_admin else ''), reply_to_message_id=message_id)

def themeDayList(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text='No English Tuesday - A day where we purposefully don\'t speak English as an exercise in practicing our target languages together.')

def error_handler(bot, update, error):
    logging.warn('Update "%s" caused error "%s"' % (update, error))

updater = Updater(token=config.bot['token'])
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help_function))
dispatcher.add_handler(CommandHandler('startnoenglishtuesday', startNoEnglishTuesday))
dispatcher.add_handler(CommandHandler('themedaylist', themeDayList))

dispatcher.add_error_handler(error_handler)

updater.start_polling()
updater.idle()
