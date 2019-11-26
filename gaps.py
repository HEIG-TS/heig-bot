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

import re
import subprocess
import json

class Gaps:
    """
        Class for access to GAPS account

        - _user
    """

    def __init__(self, user):
        """
            Make a Gaps object
            :param user: User object for configuration
            :type user: User
        """
        self._user = user
        if not "gaps" in self._user._data:
            self._user._data["gaps"] = {}
        self._data = self._user._data["gaps"]
    def debug(self, text):
        print(str(self._user.id()) + ": " + text)

    def notes(self):
        return self._data["notes"]

    def is_registred(self):
        return "gapsid" in self._data

    def set_credentials(self, username, password):
        """
            Set credentials for GAPS
        """
        cmd = "curl -s https://gaps.heig-vd.ch/consultation/controlescontinus/consultation.php -u \""+username+":"+password+"\" | grep -oE 'show_CCs\([0-9]+' | grep -oE [0-9]+ | uniq"
        output = subprocess.check_output(cmd, shell=True)
        if(output.decode("utf-8") == ""):
            return "Error"
        else:
            self._data["username"] = username
            self._data["password"] = password
            self._data["gapsid"] = output.decode("utf-8").strip()
            self._user.save()
            return "ok"

    def get_notes_online(self, year):
        """
            Get notes from GAPS
        """
        if not self.is_registred():
            self._user.send_message("You are not registred")
        notes = {}
        notesdiff = {}
        matiere = "?"
        typenote = "?"
        idnote = -1
        cmd = "echo -e \"$(curl -H \"Content-Type: application/x-www-form-urlencoded; charset=utf-8\" "
        cmd += "-s 'https://gaps.heig-vd.ch/consultation/controlescontinus/consultation.php' "
        cmd += "--data \"rs=getStudentCCs&rsargs=%5B"+self._data["gapsid"]+"%2C"+year+"%2Cnull%5D&\" "
        cmd += "-u \""+self._data["username"]+":"+self._data["password"]+"\" "
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
        self._data["notes"][year] = json.loads(json.dumps(notes))
        self._user.save()
        return notes

    def get_notes(self, year):
        if not "notes" in self._data:
            self._data["notes"] = {}
        if not str(year) in self._data["notes"]:
            self.get_notes_online(year)
        return self._data["notes"][year]

    def send_notes_course(self, year, course, chat_id, status=0, notes=0, only_diff=False):
        if notes == 0:
            notes = self.get_notes(year)[course]
        text = ""
        if status != 0:
            text = status+": "

        send = not only_diff or is_diff(notes['moyenne'])

        course_moyenne = diff_to_md(notes['moyenne'])
        text += year + " - "+course+" (moy="+course_moyenne+")"
        self.debug(text)
        text += "\n"
        for typ,notelst in notes.items():
            if typ == "moyenne": continue
            diff = is_diff(notelst['moyenne']) or is_diff(notelst['poids'])
            typ_moyenne = diff_to_md(notelst['moyenne'])
            typ_poids = diff_to_md(notelst['poids'])
            prefix_display = " "+typ+" (moy="+typ_moyenne+", "+typ_poids+"%)\n"
            if diff or not only_diff:
                text += prefix_display
                prefix_display = ""
                send = True
            for k in notelst.keys():
                if isinstance(notelst[k], str): continue
                if k == "_del":
                    data = notelst[k]
                    st = '⊖'
                    diff = True
                    send = True
                elif k == "_add": 
                    data = notelst[k]
                    st = '⊕'
                    diff = True
                    send = True
                else:
                    data = {k:notelst[k]}
                    st = '   '
                    diff = False
                force_send = False
                if diff or not only_diff:
                    text += prefix_display
                    prefix_display = ""
                    force_send = True
                for i in data.keys():
                    diff = is_diff(data[i]['note']) or is_diff(data[i]['title']) \
                            or is_diff(data[i]['moyenne']) or is_diff(data[i]['poids']) or is_diff(data[i]['date'])
                    note = diff_to_md(data[i]['note'])
                    title = diff_to_md(data[i]['title'])
                    moyenne = diff_to_md(data[i]['moyenne'])
                    poids = diff_to_md(data[i]['poids'])
                    date = diff_to_md(data[i]['date'])
                    if force_send or diff or not only_diff:
                        send = True
                        text += prefix_display
                        prefix_display = ""
                        text += st+"  «"+title+"»\n"
                        text += st+"    "+date+" ("+note+", cls="+moyenne+", "+poids+"%)\n"
        if send:
            self._user.send_message(text, chat_id=chat_id, parse_mode="Markdown")
        else:
            self._user.send_message("IGNORED ", chat_id=chat_id)
        return send

    def send_notes(self, year, courses, chat_id):
        notes = self.get_notes(year)
        c = []
        for i in courses:
            c.insert(0, i.lower())
        for course in notes.keys():
            if course.lower() in c or len(c) == 0:
                self.send_notes_course(year, course, chat_id)

    def send_notes_all(self, chat_id):
        fullnotes = self._data["notes"]
        for year in sorted(fullnotes.keys()):
            self.send_notes(year, [], chat_id)


    def check_gaps_notes(self, chat_id, auto=False):
        sended = False
        for year in sorted(self._data["notes"].keys()):
            self.debug("Check gaps notes "+year)
            oldnotes = self._data["notes"][year]
            newnotes = self.get_notes_online(year)
            newnotes = json.loads(json.dumps(newnotes))
            diffnotes = diff(oldnotes, newnotes)
            for course in diffnotes.keys():
                if course != "_del" and course != "_add":
                    r = self.send_notes_course(year, course, chat_id, notes=diffnotes[course], only_diff=True)
                    sended = sended or r
                else:
                    status = course
                    if status == "_add": status = "⊕"
                    elif status == "_del": status = "⊖"
                    for i in diffnotes[course].keys():
                        r = self.send_notes_course(year, i, chat_id, notes=diffnotes[course][i], status=status)
                        sended = sended or r
        if not sended and not auto:
            self._user.send_message("No update", chat_id=chat_id)

def is_diff(diff):
    if isinstance(diff, dict):
        if "_del" in diff:
            return True
        elif "_add" in diff:
            return True
        elif "_change" in diff:
            return True
    return False

def diff_to_md(diff):
    if isinstance(diff, dict):
        if "_del" in diff:
            return "~⊖"+diff["_del"]+"~"
        elif "_add" in diff:
            return "*⊕"+diff["_add"]+"*"
        elif "_change" in diff:
            return "*"+diff["_change"][0]+"→"+diff["_change"][1]+"*"
    return diff

def diff(old, new):
    if isinstance(new, dict) and isinstance(old, dict):
        if len(new) == 0 and len(old) != 0:
            return {"_del": old}
        elif len(new) != 0 and len(old) == 0:
            return {"_add": new}
        else:
            tab = {}
            for k in set().union(new.keys(), old.keys()):
                if k not in new and k in old:
                    if isinstance(old[k], dict):
                        if not "_del" in tab: tab["_del"] = {}
                        tab["_del"][k] = old[k]
                    else:
                        tab[k] = {"_del": old[k]}
                elif k in new and k not in old:
                    if isinstance(new[k], dict):
                        if not "_add" in tab: tab["_add"] = {}
                        tab["_add"][k] = new[k]
                    else:
                        tab[k] = {"_add": new[k]}
                else:
                    tab[k] = diff(new[k], old[k])
            return tab
    elif new == old:
        return new
    else:
        return {"_change": [old, new]}




