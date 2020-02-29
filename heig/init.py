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


def onerror(update, context):
    try:
        raise context.error
    except GapsError as error:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Error : "+str(error))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknow error !, see the console for more details ")
        print(str(context.error))


sys.setrecursionlimit(10000)

#if len(sys.argv) == 2:
#    config = json.load(open(sys.argv[1], 'r'))
#else:
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

