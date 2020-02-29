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
import json
import pickle
import os.path

from heig.init import config
from heig.init import updater
from heig.gaps import Gaps

DIR_DB_PICKLE = "/heig.user/"

class User:
    """
        User manager

        :ivar _user_id: Telegram id of user
        :vartype _user_id: 

        :ivar _filename: Filename of pickle file for user's data stockage
        :vartype _filename: str

        :ivar _data: User's data
            _data["gaps"] see Gaps._data
        :vartype _data: dict
    """

    def __init__(self, user_id):
        """
            Initialize User object, and if possible load user's data

            :param user_id: Telegram userid
            :type user_id: 
        """
        self._user_id = user_id
        self._filename = config["database_directory"]+DIR_DB_PICKLE+str(self._user_id)+".pickle"
        if(os.path.isfile(self._filename)):
            file = open(self._filename, 'rb')
            self._data = pickle.load(file);
        else:
            self._data = {};

    def id(self):
        """
            get telegram id of user
        """
        return self._user_id

    def save(self):
        """
            Save user's data on disk
        """
        os.makedirs(config["database_directory"]+DIR_DB_PICKLE, exist_ok=True)
        file = open(self._filename, 'wb')
        pickle.dump(self._data, file)


    def gaps(self):
        """
            Get gaps object for current user

            :returns: Gaps object of current user
            :rtype: Gaps
        """
        return Gaps(self)

    def is_admin(self):
        """
            Indicate if this user is admin
            
            :rtype: bool
        """
        return str(self._user_id) in config["admins_userid"] or self._user_id in config["admins_userid"]

    def send_message(self, message, prefix="", suffix="", reply_to=0, context=updater, chat_id=0, parse_mode=None):
        """
            Send a message to user

            :param message: message to send
            :type message: str

            :param prefix: prefix to add on all message
            :type prefix: str

            :param suffix: suffix to add on all message
            :type suffix: str
            
            :param reply_to: message id to reply
            :type reply_to: int

            :param context: context of message
            :type context: telegram.ext.CallbackContext

            :param chat_id: chat id of destination of message
            :type chat_id: int

            :param parse_mode: Format of message (Markdown or HTML)
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
            self.debug("SEND: "+(prefix+text+suffix).strip())
            context.bot.send_message(chat_id=chat_id, text=prefix+text+suffix, parse_mode=parse_mode, reply_to_message_id=reply_to)

    def debug(self, text):
        """
            Display debug information on console

            :param text: Information to display
            :type text: str
        """
        print("["+str(self.id()) + "] " + text)


