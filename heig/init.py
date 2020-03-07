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
import json
import logging
import sys

import telegram.ext

from heig.gaps import GapsError

BOT_VERSION_MAJOR = 0
BOT_VERSION_MINOR = 4
BOT_VERSION_REVISION = 0
BOT_RELEASE = str(BOT_VERSION_MAJOR) + "." + str(BOT_VERSION_MINOR)
BOT_VERSION = BOT_RELEASE + "." + str(BOT_VERSION_REVISION)

COPYRIGHT_INFO = """Copyright 2019,2020 Gabriel Roch

heig-bot is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

heig-bot is distributed in the hope that it will be useful, but *WITHOUT ANY WARRANTY*; without even the implied warranty of *MERCHANTABILITY* or *FITNESS FOR A PARTICULAR PURPOSE*.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with heig-bot. If not, see https://www.gnu.org/licenses/ .

Code source of this software can be download at https://github.com/g-roch/heig-bot .
"""


def onerror(update, context):
    str_error = ""
    try:
        raise context.error
    except GapsError as error:
        str_error = "Error : " + str(error)
    except:
        str_error = "Unknow error! See the console for more details."
    context.bot.send_message(chat_id=update.effective_chat.id, text=str_error)
    str_debug = "[" + str(update.effective_chat.id) + "] " + str(context.error)
    if config()["debug"] >= 3:
        updater().bot.send_message(chat_id=update.effective_chat.id, text="```\n" + str_debug + "\n```",
                                   parse_mode="Markdown")
    if config()["debug"] >= 2:
        for uid in config()["admin"]["debug"]:
            if str(uid) != str(update.effective_chat.id):
                updater().bot.send_message(chat_id=uid, text="```\n" + str_debug + "\n```", parse_mode="Markdown")
    if config()["debug"] >= 1:
        print(str_debug)


sys.setrecursionlimit(10000)


# if len(sys.argv) == 2:
#    config = json.load(open(sys.argv[1], 'r'))
# else:
def config():
    if not hasattr(config, "data"):
        config.data = json.load(open("config.json", 'r'))
    return config.data


def updater():
    if not hasattr(updater, "data"):
        updater.data = telegram.ext.Updater(token=config()["bot_token"], use_context=True)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        updater.data.dispatcher.add_error_handler(onerror)
    return updater.data


# dispatcher = updater.dispatcher

def saveconfig(c):
    """
    Save bot config c in config.json
    :param c: array to save
    """
    json.dump(c, open("config.json", 'w'), indent=2)
