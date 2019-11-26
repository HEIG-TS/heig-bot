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
import json
import os.path

from init import config
from init import updater
from gaps import Gaps

class User:
    """
        User manager

        - _user_id
        - _data
        - _filename
    """

    def __init__(self, user_id):
        self._user_id = user_id
        self._filename = config["database_directory"]+"/"+str(self._user_id)+".json"
        if(os.path.isfile(self._filename)):
            file = open(self._filename, 'r')
            self._data = json.load(file);
        else:
            self._data = json.loads("{}");

    def id(self):
        return self._user_id

    def save(self):
        """
            Save data in file
        """
        file = open(self._filename, 'w')
        json.dump(self._data, file, indent=2)


    def gaps(self):
        """
            Get gaps object for current user
        """
        filename = config["database_directory"]+"/"+str(self._user_id)+".json"
        return Gaps(self)

    def is_admin(self):
        """
            Indicate if this user is admin
        """
        return str(self._user_id) in config["admins_userid"] or self._user_id in config["admins_userid"]

    def send_message(self, message, prefix="", suffix="", reply_to=0, context=updater, chat_id=0, parse_mode=None):
        """
            Send message to user

            :param message: message to send
            :type message: str
            :param prefix: prefix to add on all message
            :type prefix: str
            :param suffix: suffix to add on all message
            :type suffix: str
            :param reply_to: message id to reply
            :type reply_to: int
            :param context: context of message
            :type context: ??
            :param chat_id: chat id of destination of message
            :type chat_id: int
            :param parse_mode: Format of message (Markdown or HTML
            :type parse_mode: str
        """
        if chat_id == 0:
            chat_id = self._user_id
        text = ""
        for line in message.splitlines():
            if len(text) + len(line) + len(suffix) >= telegram.constants.MAX_MESSAGE_LENGTH:
                context.bot.send_message(chat_id=chat_id, text=prefix+text+suffix, parse_mode=parse_mode, reply_to_message_id=reply_to)
                reply_to = 0
                text = line
            else:
                text += line + "\n"
        if not text == "":
            context.bot.send_message(chat_id=chat_id, text=prefix+text+suffix, parse_mode=parse_mode, reply_to_message_id=reply_to)
        #context.bot.send_message(chat_id=chat_id, text=message)



