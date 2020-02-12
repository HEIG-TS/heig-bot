"""
    Copyright 2019 Gabriel Roch

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
import telegram.ext
import logging
import subprocess
import json
import sys
import os.path
import re
from gaps import GapsError

def onerror(update, context):
    try:
        raise context.error
    except GapsError as error:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Error : "+str(error))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknow error ! ")
        print(str(context.error))


sys.setrecursionlimit(10000)

#if len(sys.argv) == 2:
#    config = json.load(open(sys.argv[1], 'r'))
#else:
config = json.load(open("config.json", 'r'))

updater = telegram.ext.Updater(token=config["bot_tocken"], use_context=True)
# dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
updater.dispatcher.add_error_handler(onerror)

def saveconfig(c): 
    """
    Save bot config c in config.json
    :param c: array to save
    """
    json.dump(c, open("config.json", 'w'), indent=2)

