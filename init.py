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
import logging
import subprocess
import json
import sys
import os.path
import re

#if len(sys.argv) == 2:
#    config = json.load(open(sys.argv[1], 'r'))
#else:
config = json.load(open("config.json", 'r'))

updater = telegram.ext.Updater(token=config["bot_tocken"], use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

def saveconfig(c): 
    """
    Save bot config c in config.json
    :param c: array to save
    """
    json.dump(c, open("config.json", 'w'), indent=2)

def isadmin(id):
    """
    Test if user is admin
    :param id: id of user to test
    """
    return str(id) in config["admins_userid"] or id in config["admins_userid"]

def isadmin_u(update):
    """
    Test if user is admin
    :param update: update object from telegram lib
    """
    return isadmin(update.effective_user.id)

def load(id):
    """
    Load user informations
    :param id: id of user to get infos
    """
    filename = config["database_directory"]+"/"+str(id)+".json";
    if(os.path.isfile(filename)):
        file = open(filename, 'r')
        return json.load(file);
    else:
        return json.loads("{}");

def load_u(update):
    """
    Load user informations
    :param update: update object from telegram lib
    """
    return load(update.effective_user.id)

def save(userid, data):
    """
    Save user informations
    :param userid: id of user to save infos
    :param date: data to save
    """
    file = open(config["database_directory"]+"/"+str(userid)+".json", 'w')
    json.dump(data, file, indent=2)

def save_u(update, data):
    """
    Save user informations
    :param update: update object from telegram lib
    :param date: data to save
    """
    save(update.effective_user.id, data)

def setGapsCredentials(update, username, password):
    cmd = "curl -s https://gaps.heig-vd.ch/consultation/controlescontinus/consultation.php -u \""+username+":"+password+"\" | grep -oE 'show_CCs\([0-9]+' | grep -oE [0-9]+ | uniq"
    output = subprocess.check_output(cmd, shell=True)
    if(output.decode("utf-8") == ""):
        return "Error"
    else:
        data = load_u(update)
        data["gapsusername"] = username
        data["gapspassword"] = password
        data["gapsid"] = output.decode("utf-8").strip()
        save_u(update, data)
        return "ok"

def getGapsNote(userid, year):
    notes = {}
    notesdiff = {}
    matiere = "?"
    typenote = "?"
    idnote = -1
    data = load(userid)
    cmd = "echo -e \"$(curl -H \"Content-Type: application/x-www-form-urlencoded; charset=utf-8\" "
    cmd += "-s 'https://gaps.heig-vd.ch/consultation/controlescontinus/consultation.php' "
    cmd += "--data \"rs=getStudentCCs&rsargs=%5B"+data["gapsid"]+"%2C"+year+"%2Cnull%5D&\" "
    cmd += "-u \""+data["gapsusername"]+":"+data["gapspassword"]+"\" "
    cmd += ")\" | xmllint --html - 2> /dev/null "# | sed 's/\\\\//g' "
    output = subprocess.check_output(cmd, shell=True).decode("unicode-escape")
    for i in output.splitlines():
        if i[:2] == "<!": continue
        if i[:5] == "<html": continue
        if i[:6] == "</body": continue
        if i[:6] == "<table": continue
        if i[:7] == "</table": continue
        if i == "<tr>": continue
        if i == "</tr>": continue
        if i == "       ": continue
        if i == "</td>": continue
        if i == "</div></td>": continue
        if i == "</div></div></td>": continue
        if i == "</div>": continue
        if i == "<p>-e +:\"</p>": continue
        if re.match("^<td style='\"width:[13]00px;\"' class='\"l2header\"'>[a-z.]+</td>$", i): continue
        if re.match("^<td><div style='\"width:300px;\"class=\"formulaire_contenu_label\"' id='\"lm_[a-z0-9]+\"'><div onclick='\"toggleLMNodes\\(this.childNodes\\);\"'> <div id='\"short__lm_[a-z0-9]+\"' style='\"display:block;\"'>[^<]+&nbsp;\\[...\\]$", i): continue
        r = re.match("^<tr><td class='\"bigheader\"' colspan='\"6\"'>(?P<mat>[^ ]+) - moyenne hors examen : (?P<moy>[0-9.]+|-)</td></tr>$", i)
        if r:
            matiere = r.group("mat")
            if not matiere in notes:
                notes[matiere] = {}
            notes[matiere]["moyenne"] = r.group("moy")
            continue
        r = re.match("^<td class='\"(odd|edge)\"' rowspan='\"[0-9]+\"'>(?P<typ>[a-zA-Z]+)<br>moyenne : (?P<moy>[0-9.]+|-)<br>poids : (?P<poid>[0-9.]+)</td>$", i)
        if r:
            typenote = r.group("typ")
            idnote = -1
            if not typenote in notes[matiere]:
                notes[matiere][typenote] = {}
            notes[matiere][typenote]["moyenne"] = r.group("moy")
            notes[matiere][typenote]["poids"] = r.group("poid")
            continue
        r = re.match("^<td class='\"bodyCC\"'>(?P<dt>[0-9]{2}.[0-9]{2}.[0-9]{4})</td>$", i)
        if r:
            idnote += 1
            notes[matiere][typenote][idnote] = {}
            notes[matiere][typenote][idnote]["date"] = r.group("dt")
            continue
        r = re.match("^       <div id='\"long__lm_[0-9a-z]+\"' style='\"display:none;\"'>(?P<descr>.+)$", i)
        if r:
            notes[matiere][typenote][idnote]["title"] = r.group("descr")
            continue
        r = re.match("^<td><div style='\"width:300px;\"class=\"formulaire_contenu_label\"' id='\"lm_[a-z0-9]+\"'>(?P<descr>[^<]+)<td class='\"bodyCC\"'>(?P<moy>[0-9.]+|-)</td>$", i)
        if r:
            notes[matiere][typenote][idnote]["title"] = r.group("descr")
            notes[matiere][typenote][idnote]["moyenne"] = r.group("moy")
            continue
        r = re.match("^<td class='\"bodyCC\"'>[0-9]+(\\\\/[0-9]+)? \((?P<poid>[0-9]+)%\)</td>$", i)
        if r:
            #if not idnote in notes[matiere][typenote]:
            #    notes[matiere][typenote][idnote] = {}
            notes[matiere][typenote][idnote]["poids"] = r.group("poid")
            continue
        r = re.match("^ *<td class='\"bodyCC\"'>(?P<note>[0-9.]+|-)(</td>|\")$", i)
        if r:
            if "moyenne" in notes[matiere][typenote][idnote]:
                notes[matiere][typenote][idnote]["note"] = r.group("note")
            else:
                notes[matiere][typenote][idnote]["moyenne"] = r.group("note")
            continue
        print("unknown line : >>"+i+"<<")
    return notes

def getGapsNote_u(update, year):
    return getGapsNote(update.effective_user.id, year)

def getGapsNoteCache(userid, year):
    data = load(userid)
    if not "gapsnotes" in data:
        data["gapsnotes"] = {}
    if not str(year) in data["gapsnotes"]:
        data["gapsnotes"][year] = getGapsNote(userid, year)
        save(userid, data)
    return data["gapsnotes"][year]

def getGapsNoteCache_u(update, year):
    return getGapsNoteCache(update.effective_user.id, year)


def send_message(context, chatid, message):
    text = ""
    for line in message.splitlines():
        if len(text) + len(line) >= telegram.constants.MAX_MESSAGE_LENGTH:
            context.bot.send_message(chat_id=chatid, text=text)
            text = line
        else:
            text += line
    #context.bot.send_message(chat_id=chatid, text=message)



