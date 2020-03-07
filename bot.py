#!/usr/bin/python3
"""
    Copyright 2019,2020 Gabriel Roch

    This file is part of heig-bot.

    heig-bot is free software: you can redistribute it and/or modify
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

import arrow
import telegram.ext
import subprocess
import copy
import json

from heig.init import *
from heig.user import User


def cmdsetgapscredentials(update, context):
    """
        treatment of command /setgappscredentials

        Change user credentials for connexion to GAPS, for security the 
        message from user contain password is deleted

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    if (len(context.args) == 2):
        act_result = user.gaps().set_credentials(context.args[0], context.args[1])
        user.send_message("set GAPS credentials : " + act_result, chat_id=update.effective_chat.id)
    else:
        user.send_message("Usage : /setgapscredentials username password", chat_id=update.effective_chat.id)
    context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)
    user.send_message("Your message has been deleted for security", chat_id=update.effective_chat.id)


def cmdunsetgapscredentials(update, context):
    """
        treatment of command /unsetgappscredentials

        Delete user credentials for connexion to GAPS

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    user.gaps().unset_credentials()
    user = User(update.effective_user.id)
    if user.gaps().is_registred():
        user.send_message("Sorry, failed to delete credentials", chat_id=update.effective_chat.id)
    else:
        user.send_message("credentials deleted", chat_id=update.effective_chat.id)


def cmdcleargapsnotes(update, context):
    """
        treatment of command /cleargapsnotes

        Remove cache of GAPS notes

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    user.gaps()._data["notes"] = {}
    user.save()
    user.send_message("Notes cache cleared", chat_id=update.effective_chat.id)
    
def cmd_showdata(update, context):
    """
        treatment of command /showdata

        Show all information about user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    d = copy.deepcopy(user._data)
    if "gaps" in d:
        if "notes" in d["gaps"]:
            for year in d["gaps"]["notes"].keys():
                for branch in d["gaps"]["notes"][year].keys():
                    d["gaps"]["notes"][year][branch] = d["gaps"]["notes"][year][branch].serilizable()
        d["gaps"]["password"] = "HIDDEN"
    text = json.dumps(d, indent=1)
    user.send_message(text, prefix="```\n", suffix="```", parse_mode="Markdown")



def cmd_untracking_gaps_notes(update, context) -> None:
    """
        treatment of command /untrackinggapsnotes

        Disable tracking gaps note

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    print("Z")
    u.gaps().set_tracking(type="notes", branch_list=False, user_id=update.effective_chat.id)
    print("A")
    if u.gaps().tracking("notes", user_id=update.effective_chat.id):
        text = "Tracking gaps notes is *enable*"
    else:
        text = "Tracking gaps notes is *disable*"
    print("B")
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")

def cmd_tracking_gaps_notes(update, context) -> None:
    """
        treatment of command /trackinggapsnotes

        Get tracking gaps note value

        treatment of command /trackinggapsnotes *
        treatment of command /trackinggapsnotes [<branchname> ...]

        Set tracking gaps note value

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    text = ""

    if len(context.args) == 1 and context.args[0] == "*":
        u.gaps().set_tracking(type="notes", branch_list=True, user_id=update.effective_chat.id)
    elif len(context.args) >= 1:
        u.gaps().set_tracking(type="notes", branch_list=context.args, user_id=update.effective_chat.id)
    else:
        text = "Usage: /trackinggapsnotes *\n"
        text = "Usage: /trackinggapsnotes <branchname> ...\n\n"
    if u.gaps().tracking("notes", user_id=update.effective_chat.id):
        text += "Tracking gaps notes is *enable*"
    else:
        text += "Tracking gaps notes is *disable*"
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmd_version(update, context) -> None:
    """
        treatment of command /version

        Show bot version and copyright information

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    text = "HEIG-bot version " + BOT_RELEASE + "\n\n" + COPYRIGHT_INFO
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmd_close(update, context) -> None:
    """
        treatment of command /calendar <YYYY-MM-DD>

        Get timetable for a day

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    u.destroy_data()


def cmd_calendar(update, context) -> None:
    """
        treatment of command /calendar <YYYY-MM-DD>

        Get timetable for a day

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)

    if len(context.args) == 1:
        dt = arrow.get(context.args[0])
    else:
        dt = arrow.now()

    text = u.gaps().get_day_lesson(text=True, dt=dt)
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmdcheckgapsnotes(update, context):
    """
        treatment of command /checkgapsnotes

        Check online if user have new mark or an update

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    user.gaps().check_gaps_notes(update.effective_chat.id)


def cmdgetgapsnotes(update, context):
    """
        treatment of command /getgapsnotes [<year> [<branch> ...]]

        Send to user the note.

        If no year and no branch specified, all mark in cache send

        If only no branch specified, all mark of the specific year send

        If multiple branch specified, all mark of specified branch send

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    if (len(context.args) >= 1):
        year = context.args[0]
        courses = context.args[1:]
        user.gaps().send_notes(year, courses, update.effective_chat.id)
    else:
        user.send_message("Usage : /getgapsnotes [<year> [<course> ...]]", chat_id=update.effective_chat.id)
        user.gaps().send_notes_all(update.effective_chat.id)


def cmdhelp(update, context):
    """
        treatment of command /help

        Send help information to user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    d = [
        ["help", "", "Show this help"],
        ["help", "botcmd", "Show command list in format for BotFather"],
        ["getgapsnotes", "[<annee> [<cours> ...]]", "Show GAPS notes"],
        ["setgapscredentials", "<username> <password>", "Set credentials for GAPS"],
        ["unsetgapscredentials", "", "Clear credentials for GAPS"],
        ["checkgapsnotes", "", "Check if you have new notes"],
        ["cleargapsnotes", "", "Clear cache of GAPS notes"],
        ["calendar", "\\[<YYYY-MM-DD>]", "Get your planning for a specific day"],
        ["close", "", "Delete all information stocked by the bot"],
        ["version", "", "Show version and copyright information"],
        ["trackinggapsnotes", "", "Show gaps notes tracking"],
        ["trackinggapsnotes", "\*|<branchname> ...", "Enable gaps notes tracking"],
        ["untrackinggapsnotes", "", "Disable gaps notes tracking"],
        ["showdata", "", "Show data saved about you"],
    ]
    d_admin_all = [
        ["help", "admin", "Show admin help"],
    ]
    d_admin = [
        ["adminkill", "", "Kill the bot"],
        ["adminupdate", "", "Update bot by git"],
    ]
    user = User(update.effective_user.id)
    text = ""
    if len(context.args) == 1 and context.args[0] == "botcmd":
        ttt = []
        d.sort()
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
        d.sort()
        for cmd in d:
            textnew = "\n/" + cmd[0] + " " + cmd[1] + " - " + cmd[2]
            if len(text) + len(textnew) >= telegram.constants.MAX_MESSAGE_LENGTH:
                user.send_message(text, chat_id=update.effective_chat.id)
                text = textnew
            else:
                text += textnew
        text += "\n\nYour telegram id is `" + str(update.effective_user.id) + "`\n"
        text += "Your chat id is `" + str(update.effective_chat.id) + "`\n"
    user.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmd(update, context):
    if config()["admin_exec"] == "on":
        user = User(update.effective_user.id)
        if (user.is_admin()):
            my_cmd = update.message.text
            print(my_cmd)
            output = subprocess.check_output(my_cmd, shell=True)
            user.send_message(output.decode("utf-8"), prefix="`", suffix="`", parse_mode="Markdown",
                              reply_to=update.effective_message.message_id, chat_id=update.effective_chat.id)
        else:
            user.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)


##############

def cmdadminkill(update, context):
    """
        treatment of command /adminkill

        Exec `killall bot.py`

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    if (user.is_admin()):
        subprocess.check_output("killall bot.py", shell=True)
        user.send_message("Kill is apparrently failed", chat_id=update.effective_chat.id)
    else:
        user.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)


def cmdadminupdate(update, context):
    """
        treatment of command /adminkill

        Exec `git pull`
        Exec `killall bot.py`

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    if (user.is_admin()):
        update.message.text = "git pull"
        cmd(update, context)
        cmdadminkill(update, context)


def start(update, context):
    """
        treatment of command /start

        Send initial information to user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    text = """Welcome to the unofficial HEIG bot
set your GAPS credentials with :  
/setgapscredentials <username> <password> 
get help with /help"""
    user.send_message(text, chat_id=update.effective_chat.id)


updater().dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('help', cmdhelp))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('calendar', cmd_calendar))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('adminkill', cmdadminkill))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('adminupdate', cmdadminupdate))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('setgapscredentials', cmdsetgapscredentials))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('unsetgapscredentials', cmdunsetgapscredentials))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('getgapsnotes', cmdgetgapsnotes))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('cleargapsnotes', cmdcleargapsnotes))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('checkgapsnotes', cmdcheckgapsnotes))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('version', cmd_version))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('close', cmd_close))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('trackinggapsnotes', cmd_tracking_gaps_notes))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('untrackinggapsnotes', cmd_untracking_gaps_notes))
updater().dispatcher.add_handler(telegram.ext.CommandHandler('showdata', cmd_showdata))

# Need to be after CommandHandler for non-admin user
if config()["admin_exec"] == "on":
    updater().dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, cmd))

for id in config()["group"]["log"]:
    user = User(id)
    user.send_message("Bot starting")
updater().start_polling()
