#!/usr/bin/python3
"""
    Copyright 2019 Gabriel Roch

    This file is part of heig-bot.

    Foobar is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    heig-bot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with heig-bot. If not, see <https://www.gnu.org/licenses/>.
"""

import telegram.ext
import sys
import subprocess
import json
import os.path
from user import User
from init import *

def cmdsetgapscredentials(update, context):
    user = User(update.effective_user.id)
    if(len(context.args) == 2):
        act_result = user.gaps().set_credentials(context.args[0], context.args[1])
        user.send_message("set GAPS credentials : "+act_result, chat_id=update.effective_chat.id)
    else:
        user.send_message("Usage : /setgapscredentials username password", chat_id=update.effective_chat.id)
    context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)
    user.send_message("Your message is deleted for security", chat_id=update.effective_chat.id)

def cmdcleargapsnotes(update, context):
    user = User(update.effective_user.id)
    user.gaps()._data["notes"] = {}
    user.save()
    user.send_message("Notes cache cleared", chat_id=update.effective_chat.id)

def cmdcheckgapsnotes(update, context):
    user = User(update.effective_user.id)
    user.gaps().check_gaps_notes(update.effective_user.id)

def cmdgetgapsnotes(update, context):
    user = User(update.effective_user.id)
    if(len(context.args) >= 1):
        year = context.args[0]
        courses = context.args[1:]
        user.gaps().send_notes(year, courses, update.effective_chat.id)
    else:
        user.send_message( "Usage : /getgapsnotes [<annee> [<cours> ...]]", chat_id=update.effective_chat.id)
        user.gaps().send_notes_all(update.effective_chat.id)

def cmdhelp(update, context):
    d = [
            ["help", "", "Show this help"],
            ["help", "botcmd", "Show command list in format for BotFather"],
            ["getgapsnotes", "[<annee> [<cours> ...]]", "Show GAPS notes"],
            ["setgapscredentials", "<username> <password>", "Set credentials for GAPS"],
            ["checkgapsnotes", "", "Check if you have new notes"],
            ["cleargapsnotes", "", "Clear cache of GAPS notes"],
        ]
    d_admin_all = [
            ["help", "admin", "Show admin help"],
        ]
    d_admin = [
            ["adminset", "<key> <value>", "Set configuration entry"],
            ["adminget", "<key>", "Get configuration entry"],
            ["adminadd", "<key> <value>", "Add value to configuration entry"],
            ["admindel", "<key> <value>", "Remove value to configuration entry"],
            ["adminkill", "", "Kill the bot"],
            ["adminupdate", "", "Update bot by git"],
        ]
    user = User(update.effective_user.id)
    text = ""
    if len(context.args) == 1 and context.args[0] == "botcmd":
        ttt = []
        for cmd in d:
            if not cmd[0] in ttt:
                text += "" + cmd[0] + " - " + cmd[2] + "\n"
                ttt.append(cmd[0])
    else:
        text += "Usage :"
        if user.is_admin() and len(context.args) == 1 and context.args[0] == "admin":
            d += d_admin_all + d_admin
        elif user.is_admin():
            d += d_admin_all
        for cmd in d:
            textnew = "\n/" + cmd[0] + " " + cmd[1] + " - " + cmd[2]
            if len(text) + len(textnew) >= telegram.constants.MAX_MESSAGE_LENGTH:
                user.send_message(text, chat_id=update.effective_chat.id)
                text = textnew
            else:
                text += textnew
    user.send_message(text, chat_id=update.effective_chat.id)

def cmd(update, context):
    user = User(update.effective_user.id)
    if(user.is_admin()):
        my_cmd = update.message.text
        print(my_cmd)
        output = subprocess.check_output(my_cmd, shell=True)
        user.send_message(output.decode("utf-8"), prefix="`", suffix="`", parse_mode="Markdown", reply_to=update.effective_message.message_id, chat_id=update.effective_chat.id)
    else:
        user.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)








##############

def cmdadminkill(update, context):
    user = User(update.effective_user.id)
    if(user.is_admin()):
        subprocess.check_output("killall bot.py", shell=True)
        user.send_message("Kill is apparrently failed", chat_id=update.effective_chat.id)
    else:
        user.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)

def cmdadminupdate(update, context):
    user = User(update.effective_user.id)
    if(user.is_admin()):
        update.message.text = "git pull"
        cmd(update, context)
        cmdadminkill(update, context)

def start(update, context):
    user = User(update.effective_user.id)
    text = """Welcom on a unofficial HEIG bot
set your GAPS credentials with :  
/setgapscredentials <username> <password> 
get help with /help"""
    user.send_message(text, chat_id=update.effective_chat.id)

updater.dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
updater.dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, cmd))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('adminkill', cmdadminkill))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('adminupdate', cmdadminupdate))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('setgapscredentials', cmdsetgapscredentials))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('getgapsnotes', cmdgetgapsnotes))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('cleargapsnotes', cmdcleargapsnotes))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('checkgapsnotes', cmdcheckgapsnotes))
updater.dispatcher.add_handler(telegram.ext.CommandHandler('help', cmdhelp))


for id in config["logs_userid"]:
    user = User(id)
    user.send_message("Bot starting")
updater.start_polling()
