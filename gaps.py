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
        return notes

    def get_notes(self, year):
        if not "notes" in self._data:
            self._data["notes"] = {}
        if not str(year) in self._data["notes"]:
            self._data["notes"][year] = self.get_notes_online(year)
            self._user.save()
        return self._data["notes"][year]

    def send_notes_course(self, year, course, chat_id, status="standard"):
        matvalue = self.get_notes(year)[course]
        text = ""
        if status == "new":
            text = "New "
        elif status == "deleted":
            text = "Deleted "
        text += year + " - "+course+" (moy="+matvalue["moyenne"]+")\n"
        print(course)
        for typ,notelst in matvalue.items():
            if typ == "moyenne": continue
            text += " "+typ
            text += " (moy="+notelst['moyenne']+", "+notelst['poids']+"%)\n";
            for notek in notelst.keys():
                note = notelst[notek]
                if isinstance(note, str): continue
                text += "  «"+note['title']+"»\n"
                text += "    "+note['date']+" ("+note['note']+", cls="+note['moyenne']+", "+note['poids']+"%)\n"
        self._user.send_message(text, chat_id=chat_id)

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


    def check_gaps_notes(self, chat_id):
        for year in sorted(self._data["notes"].keys()):
            newnotes = self.get_notes_online(year)
            oldnotes = self._data["notes"][year]
            courses = set().union(newnotes.keys(), oldnotes.keys())
            for course in courses:
                if not course in oldnotes:
                    self.send_notes_course(year, course, chat_id, status="new")
                if not course in newnotes:
                    self.send_notes_course(year, course, chat_id, status="deleted")
                newcourse = newnotes[course]
                oldcourse = oldnotes[course]
                #for typ in set().union(newcourse.keys(), oldcourse.keys()):



                



