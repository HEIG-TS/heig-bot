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

command_list = {
    'cmd_start': [
        'start',
        ['user', '', 'Start the bot'],
    ],
    'cmd_help': [
        'help',
        ["user", '', 'Show this help'],
        ["user", 'botcmd', 'Show command list in format for BotFather'],
    ],
    'cmd_gaps_calendar': [
        'gapscalendar',
        ['user', "[<YYYY-MM-DD>]", "Get your planning for a specific day"],
    ],
    'cmd_admin_kill': [
        'adminkill',
        ['admin', '', 'Kill the bot'],
    ],
    'cmd_admin_update': [
        'adminupdate',
        ['admin', '', 'Update bot by git'],
    ],
    'cmd_gaps_set_credentials': [
        'gapssetcredentials',
        ['user', '<username> <password>', 'Set credentials for GAPS'],
    ],
    'cmd_gaps_remove_password': [
        'gapsremovepassword',
        ['user', '', 'Clear credentials for GAPS'],
    ],
    'cmd_gaps_get_notes': [
        'gapsgetnotes',
        ['user', '[<annee> [<cours> ...]]', 'Show GAPS notes'],
    ],
    'cmd_gaps_clear_notes': [
        'gapsclearnotes',
        ['user', '', 'Clear cache of GAPS notes'],
    ],
    'cmd_gaps_check_notes': [
        'gapschecknotes',
        ['user', '', 'Check if you have new notes'],
    ],
    'cmd_version': [
        'version',
        ['user', '', 'Show version and copyright information'],
    ],
    'cmd_close': [
        'close',
        ['user', '', 'Delete all information stocked by the bot'],
    ],
    'cmd_gaps_notes_track': [
        'gapsnotestrack',
        ['user', '', 'Show gaps notes tracking'],
        ['user', '*|<branchname> ...', 'Enable gaps notes tracking'],
    ],
    'cmd_gaps_notes_untrack': [
        'gapsnotesuntrack',
        ['user', '', 'Disable gaps notes tracking'],
    ],
    'cmd_show_data': [
        'showdata',
        ['user', '', 'Show data saved about you'],
    ]
}


def usage(
        cmdname,
        right=None,
        prefix=False,
        user=None,
        send=False,
        chat_id=None
) -> str:
    if prefix == False:
        prefix = ""
    elif prefix == True:
        prefix = "Usage : \n"
    if right is None:
        right = ['user']
        if user is not None and user.is_admin():
            right.append('admin')
    text = prefix
    ttt = []
    for v in command_list[cmdname][1:]:
        if v[0] in right:
            ttt.append(
                "/" + command_list[cmdname][0]
                + " `" + v[1] + "`\n  " + v[2]
            )
    ttt.sort()
    text += "\n".join(ttt)
    if send:
        user.send_message(text, chat_id=chat_id, parse_mode="Markdown")
    return text


def cmd_gaps_set_credentials(update, context):
    """
        treatment of command /gapssetcredentials

        Change user credentials for connexion to GAPS, for security the 
        message from user contain password is deleted

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    if len(context.args) == 2:
        act_result = u.gaps().set_credentials(context.args[0], context.args[1])
        u.send_message("set GAPS credentials : " + act_result, chat_id=update.effective_chat.id)
    else:
        usage("cmd_gaps_set_credentials", user=u, prefix=True, send=True, chat_id=update.effective_chat.id)
    context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)
    u.send_message("Your message has been deleted for security", chat_id=update.effective_chat.id)


def cmd_gaps_remove_password(update, context):
    """
        treatment of command /gapsremovepassword

        Delete user credentials for connexion to GAPS

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    u.gaps().unset_credentials()
    u = User(update.effective_user.id)
    if u.gaps().is_registred():
        u.send_message("Sorry, failed to delete credentials", chat_id=update.effective_chat.id)
    else:
        u.send_message("credentials deleted", chat_id=update.effective_chat.id)


def cmd_gaps_clear_notes(update, context):
    """
        treatment of command /gapsclearnotes

        Remove cache of GAPS notes

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    u.gaps()._data["notes"] = {}
    u.save()
    u.send_message("Notes cache cleared", chat_id=update.effective_chat.id)


def cmd_show_data(update, context):
    """
        treatment of command /showdata

        Show all information about user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    d = copy.deepcopy(u._data)
    if "gaps" in d:
        if "notes" in d["gaps"]:
            for year in d["gaps"]["notes"].keys():
                for branch in d["gaps"]["notes"][year].keys():
                    d["gaps"]["notes"][year][branch] = d["gaps"]["notes"][year][branch].serilizable()
        d["gaps"]["password"] = "HIDDEN"
    text = json.dumps(d, indent=1)
    u.send_message(text, prefix="```\n", suffix="```", parse_mode="Markdown")


def cmd_gaps_notes_untrack(update, context) -> None:
    """
        treatment of command /gapsnotesuntrack

        Disable tracking gaps note

        :param update:
        :type update: telegram.Update

        :param context:
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    u.gaps().set_tracking(type="notes", branch_list=False, user_id=update.effective_chat.id)
    if u.gaps().tracking("notes", user_id=update.effective_chat.id):
        text = "Tracking gaps notes is *enable*"
    else:
        text = "Tracking gaps notes is *disable*"
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmd_gaps_notes_track(update, context) -> None:
    """
        treatment of command /gapsnotestrack

        Get tracking gaps note value

        treatment of command /gapsnotestrack *
        treatment of command /gapsnotestrack [<branchname> ...]

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
        usage("cmd_gaps_notes_track", user=u, prefix=True, send=True, chat_id=update.effective_chat.id)
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


def cmd_gaps_calendar(update, context) -> None:
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


def cmd_gaps_check_notes(update, context):
    """
        treatment of command /checkgapsnotes

        Check online if user have new mark or an update

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    u.gaps().check_gaps_notes()


def cmd_gaps_get_notes(update, context):
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
    u = User(update.effective_user.id)
    if len(context.args) >= 1:
        year = context.args[0]
        courses = context.args[1:]
        u.gaps().send_notes(year, courses, update.effective_chat.id)
    else:
        usage("cmd_gaps_get_notes", user=u, prefix=True, send=True, chat_id=update.effective_chat.id)
        u.gaps().send_notes_all(update.effective_chat.id)


def cmd_help(update, context):
    """
        treatment of command /help

        Send help information to user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    text = ""
    if len(context.args) == 1 and context.args[0] == "botcmd":
        ttt = []
        for cmd in command_list.values():
            if len(cmd) >= 2 \
                    and cmd[0] not in ttt \
                    and cmd[1][0] == 'user':
                ttt.append(cmd[0] + " - " + cmd[1][2])
        ttt.sort()
        text = "\n".join(ttt)
    else:
        right = ['user']
        if u.is_admin():
            right.append('admin')

        for r in right:
            ttt = []
            for cmd in command_list.values():
                for v in cmd[1:]:
                    if v[0] == r:
                        ttt.append(
                            "/" + cmd[0] + " `" + v[1] + "`\n  " + v[2]
                        )
            ttt.sort()
            text += "\n\n*" + r + " usage* : \n" + "\n".join(ttt)

        text += "\n\nYour telegram id is `" + str(update.effective_user.id) + "`\n"
        text += "Your chat id is `" + str(update.effective_chat.id) + "`\n"
    u.send_message(text, chat_id=update.effective_chat.id, parse_mode="Markdown")


def cmd(update, context):
    if config()["admin_exec"] == "on":
        u = User(update.effective_user.id)
        if u.is_admin():
            my_cmd = update.message.text
            print(my_cmd)
            output = subprocess.check_output(my_cmd, shell=True)
            u.send_message(output.decode("utf-8"), prefix="`", suffix="`", parse_mode="Markdown",
                              reply_to=update.effective_message.message_id, chat_id=update.effective_chat.id)
        else:
            u.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)


##############

def cmd_admin_kill(update, context):
    """
        treatment of command /adminkill

        Exec `killall bot.py`

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    user = User(update.effective_user.id)
    if user.is_admin():
        subprocess.check_output("killall bot.py", shell=True)
        user.send_message("Kill is apparrently failed", chat_id=update.effective_chat.id)
    else:
        user.send_message("Sorry, you aren't admin", chat_id=update.effective_chat.id)


def cmd_admin_update(update, context):
    """
        treatment of command /adminupdate

        Exec `git pull`
        Exec `killall bot.py`

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    if u.is_admin():
        update.message.text = "git pull"
        cmd(update, context)
        cmd_admin_kill(update, context)


def cmd_start(update, context):
    """
        treatment of command /start

        Send initial information to user

        :param update: 
        :type update: telegram.Update

        :param context: 
        :type context: telegram.ext.CallbackContext
    """
    u = User(update.effective_user.id)
    text = """Welcome to the unofficial HEIG bot
set your GAPS credentials with :  
/setgapscredentials <username> <password> 
get help with /help"""
    u.send_message(text, chat_id=update.effective_chat.id)


for k, v in command_list.items():
    updater().dispatcher.add_handler(telegram.ext.CommandHandler(
        v[0],
        locals()[k]
    ))

# Need to be after CommandHandler for non-admin user
if config()["admin_exec"] == "on":
    updater().dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, cmd))

for id in config()["group"]["log"]:
    user = User(id)
    user.send_message("Bot starting")
updater().start_polling()
