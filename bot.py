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
from init import *

def cmdset(update, context):
    if(len(context.args) == 2):
        data = load(update)
        data[context.args[0]] = context.args[1]
        save(update, data)
        send_message(context, update.effective_chat.id, context.args[0]+"="+context.args[1])
def cmdget(update, context):
    if(len(context.args) == 1):
        data = load(update)
        send_message(context, update.effective_chat.id, data[context.args[0]])

def cmdadminset(update, context):
    if(isadmin_u(update)):
        if(len(context.args) == 2 and not isinstance(config[context.args[0]], list)):
            config[context.args[0]] = context.args[1]
            saveconfig(config)
            send_message(context, update.effective_chat.id, "Ok")
        else:
            send_message(context, update.effective_chat.id, "Error")
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")
def cmdadminget(update, context):
    if(isadmin_u(update)):
        if(len(context.args) == 1):
            if(isinstance(config[context.args[0]], list)):
                send_message(context, update.effective_chat.id, ','.join(config[context.args[0]]))
            else:
                send_message(context, update.effective_chat.id, config[context.args[0]])
        else:
            send_message(context, update.effective_chat.id, "Error")
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")
def cmdadminadd(update, context):
    if(isadmin_u(update)):
        if(len(context.args) == 2 and isinstance(config[context.args[0]], list)):
            config[context.args[0]].append(context.args[1])
            saveconfig(config)
            send_message(context, update.effective_chat.id, "Ok")
        else:
            send_message(context, update.effective_chat.id, "Error")
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")
def cmdadmindel(update, context):
    if(isadmin_u(update)):
        if(len(context.args) == 2 and isinstance(config[context.args[0]], list)):
            config[context.args[0]].remove(context.args[1])
            saveconfig(config)
            send_message(context, update.effective_chat.id, "Ok")
        else:
            send_message(context, update.effective_chat.id, "Error")
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")
def cmdadminkill(update, context):
    if(isadmin_u(update)):
        subprocess.check_output("killall bot.py", shell=True)
        send_message(context, update.effective_chat.id, "Sorry, fail")
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")

def cmddebug(update, context):
    if(isadmin_u(update)):
        send_message(context, update.effective_chat.id, update.effective_chat.id)
        send_message(context, update.effective_chat.id, update.effective_user.id)
    else:
        send_message(context, update.effective_chat.id, "Sorry, you aren't admin")

def start(update, context):
    send_message(context, update.effective_chat.id, "I'm a bot, please talk to me!")

def cmd(update, context):
    if(isadmin_u(update)):
        #if(30087148 == update.effective_user.id):
        my_cmd = update.message.text
        print(my_cmd)
        output = subprocess.check_output(my_cmd, shell=True)
        send_message(context, update.effective_chat.id, output.decode("utf-8"))
    else:
        send_message(context, update.effective_chat.id, str(update.effective_user.id))

def cmdsetgapscredentials(update, context):
    if(len(context.args) == 2):
        asd = setGapsCredentials(update, context.args[0], context.args[1])
        send_message(context, update.effective_chat.id, asd)
    else:
        send_message(context, update.effective_chat.id, "Use: /setgapscredentials username password")
    context.bot.delete_message(update.effective_chat.id, update.effective_message.message_id)

def sendMatiere(update, context, notes, matiere, year):
    matvalue = notes[matiere]
    text = year + " - "+matiere+" (moy="+matvalue["moyenne"]+")\n"
    print(matiere)
    for typ,notelst in matvalue.items():
        if typ == "moyenne": continue
        text += " "+typ
        text += " (moy="+notelst['moyenne']+", "+notelst['poids']+"%)\n";
        for notek in notelst.keys():
            note = notelst[notek]
            if isinstance(note, str): continue
            text += "  «"+note['title']+"»\n"
            text += "    "+note['date']+" ("+note['note']+", cls="+note['moyenne']+", "+note['poids']+"%)\n"
    send_message(context, update.effective_chat.id, text)

def cmdgetgapsnotes(update, context):
    if(len(context.args) >= 1):
        year = context.args[0]
        notes = getGapsNoteCache_u(update, year)
        selectedmat = notes.keys()
        if(len(context.args) >= 2):
            selectedmat = context.args[1:]
        for matiere in selectedmat:
            if not matiere in notes: 
                send_message(context, update.effective_chat.id, "Pas de "+matiere+" en "+year)
                continue
            sendMatiere(update, context, notes, matiere, year)
    else:
        send_message(context, update.effective_chat.id, "Use: /getgapsnotes [<annee> [<cours> ...]]")
        fullnotes = load_u(update)
        if not "gapsnotes" in fullnotes:
            return
        fullnotes = fullnotes["gapsnotes"]
        for year in sorted(fullnotes.keys()):
            notes = fullnotes[year]
            for matiere in notes.keys():
                sendMatiere(update, context, notes, matiere, year)
def cmdcleargapsnotes(update, context):
    data = load_u(update)
    data["gapsnotes"] = {}
    save_u(update, data)
    send_message(context, update.effective_chat.id, "Cache de note vidé")


def cmdhelp(update, context):
    d = [
            ["help", "", "Affiche cette aide"],
            ["help", "botcmd", "Affiche la liste de commande au format BotFather"],
            ["getgapsnotes", "[<annee> [<cours> ...]]", "Affiche les notes GAPS"],
            ["setgapscredentials", "<username> <password>", "Définit l'identité GAPS"],
            ["cleargapsnotes", "", "Supprimme le cache de note"],
        ]
    d_admin_all = [
            ["help", "admin", "Affiche l'aide pour les admins"],
        ]
    d_admin = [
            ["adminset", "<key> <value>", "Set configuration entry"],
            ["adminget", "<key>", "Get configuration entry"],
            ["adminadd", "<key> <value>", "Add value to configuration entry"],
            ["admindel", "<key> <value>", "Remove value to configuration entry"],
            ["adminkill", "", "Kill the bot"],
        ]
    text = ""
    if len(context.args) == 1 and context.args[0] == "botcmd":
        ttt = []
        for cmd in d:
            if not cmd[0] in ttt:
                text += "" + cmd[0] + " - " + cmd[2] + "\n"
                ttt.append(cmd[0])
    else:
        text += "Usage:"
        if isadmin_u(update) and len(context.args) == 1 and context.args[0] == "admin":
            d += d_admin_all + d_admin
        elif isadmin_u(update):
            d += d_admin_all
        for cmd in d:
            textnew = "\n/" + cmd[0] + " " + cmd[1] + " - " + cmd[2]
            if len(text) + len(textnew) >= telegram.constants.MAX_MESSAGE_LENGTH:
                send_message(context, update.effective_chat.id, text)
                text = textnew
            else:
                text += textnew
    send_message(context, update.effective_chat.id, text)

dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text, cmd))
dispatcher.add_handler(telegram.ext.CommandHandler('adminset', cmdadminset))
dispatcher.add_handler(telegram.ext.CommandHandler('adminget', cmdadminget))
dispatcher.add_handler(telegram.ext.CommandHandler('adminadd', cmdadminadd))
dispatcher.add_handler(telegram.ext.CommandHandler('admindel', cmdadmindel))
dispatcher.add_handler(telegram.ext.CommandHandler('adminkill', cmdadminkill))
dispatcher.add_handler(telegram.ext.CommandHandler('setgapscredentials', cmdsetgapscredentials))
dispatcher.add_handler(telegram.ext.CommandHandler('getgapsnotes', cmdgetgapsnotes))
dispatcher.add_handler(telegram.ext.CommandHandler('cleargapsnotes', cmdcleargapsnotes))
dispatcher.add_handler(telegram.ext.CommandHandler('help', cmdhelp))

# setgapscredentials - Définit les crédentials à utiliser pour se connecter à GAPS
# getgapsnotes - Obtient les notes à partir de GAPS

if(config["debug"] == "on"):
    cmdset_handler = telegram.ext.CommandHandler('set', cmdset)
    cmdget_handler = telegram.ext.CommandHandler('get', cmdget)
    cmddebug_handler = telegram.ext.CommandHandler('debug', cmddebug)
    dispatcher.add_handler(cmdset_handler)
    dispatcher.add_handler(cmdget_handler)
    dispatcher.add_handler(cmddebug_handler)

for id in config["logs_userid"]:
    send_message(updater, id, "Bot starting")
    #updater.bot.send_message(chat_id=id, text="Bot starting")
updater.start_polling()
