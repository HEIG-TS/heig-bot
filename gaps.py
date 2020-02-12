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

"""
    Parsing of notes is inspired/copied by https://gitlab.theswissbay.ch/heig/hidapo
"""

import re
import subprocess
import json
import requests
import copy
from bs4 import BeautifulSoup
from datetime import date

URL_BASE = "https://gaps.heig-vd.ch/"
URL_CONSULTATION_NOTES = URL_BASE+"/consultation/controlescontinus/consultation.php"
URL_ATTENDANCE = URL_BASE+"/consultation/etudiant/"

class GapsError(Exception):
    pass

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
        text = requests.get(URL_ATTENDANCE, auth=(username, password)).text
        if text.find('idStudent = ') == -1:
            return "Fail, check your login/password (login is HEIG login, not HES-SO login)"
        else:
            self._data["username"] = username
            self._data["password"] = password
            self._data["gapsid"] = text[text.find('idStudent = ') + 12:text.find('// default') - 2]
            self._user.save()
            return "Success (GAPS ID: "+str(self._data["gapsid"])+")"

    def get_notes_online(self, year):
        """
            Get notes from GAPS
        """
        if not self.is_registred():
            raise GapsError("You are not registred")
        text = requests.post(
                URL_CONSULTATION_NOTES,
                auth=(self._data['username'], self._data['password']),
                headers={'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'},
                data={
                    'rs': 'getStudentCCs',
                    'rsargs': '[' + self._data["gapsid"] + ',' + year + ',null]',
                    ':': None
                }
            ).text
        try:
            text = json.loads(text[2:])
        except:
            raise GapsError("Parsing of gaps notes page ERROR, are you changed your GAPS password ? (/setgapscredentials)")
        soup = BeautifulSoup(text, 'html.parser')
        rows = soup.find_all('tr')

        current_course = None
        current_eval_type = None
        courses = {}

        for row in rows:
            row_content_type = row.contents[0].attrs['class'][0]
            if row_content_type == 'bigheader':
                if current_course is not None:
                    courses[current_course.name] = current_course
                r = re.match(
                        "(?P<mat>[^ ]+) - moyenne hors examen : (?P<moy>[0-9.]+|-)",
                        row.contents[0].contents[0]
                    )
                current_course = GradeCourse(
                    str(r.group("mat")),
                    str(r.group("moy"))
                )
            elif row_content_type == 'edge' or row_content_type == 'odd':
                current_eval_type = row.contents[0].contents[0]
                average = str(row.contents[0].contents[2][10:])
                coef = str(row.contents[0].contents[4][8:])
                current_course.evals[current_eval_type] = \
                        GradeGroupEvaluation(average, coef)
            elif row_content_type == 'bodyCC':
                # checking if evaluation is released
                if isinstance(row.contents[1].contents[0].contents[0], str):
                    notedescr = str(row.contents[1].contents[0].contents[0])
                else:
                    notedescr = str(row.contents[1].contents[0].contents[0].contents[3].contents[0])
                notedate = str(row.contents[0].contents[0] )
                noteclass= str(row.contents[2].contents[0] )
                notecoeff= str(row.contents[3].contents[0] )
                notecoeff= re.sub(r'^[0-9/]+ \(([0-9]+)%\)$', r'\1', str(notecoeff))
                note = str(row.contents[4].contents[0])
                notedescr = notedescr.strip()

                current_course.evals[current_eval_type].evals.append(
                        GradeEvaluation(notedescr, notedate, noteclass, note, notecoeff)
                    )

        if current_course is not None:
            courses[current_course.name] = current_course
        self._data["notes"][year] = courses
        self._user.save()
        return courses


    def get_notes(self, year):
        if not "notes" in self._data:
            self._data["notes"] = {}
        if not str(year) in self._data["notes"]:
            self.get_notes_online(year)
        return self._data["notes"][year]

    def send_notes_course(self, year, course, chat_id, status=0, notes=0, only_diff=False, text=""):
        if 0 == notes:
            notes = self.get_notes(year)[course]

        text += notes.str(year)

        self._user.send_message(text, chat_id=chat_id) #, parse_mode="Markdown")
        return True

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
        if "notes" not in self._data:
            self._data["notes"] = {}
        years = sorted(self._data["notes"].keys())
        if date.today().month < 6:
            actualyear = str(date.today().year - 1)
        else:
            actualyear = str(date.today().year)
        if actualyear not in years:
            years.insert(len(years), actualyear)
        if actualyear not in self._data["notes"]:
            self._data["notes"][actualyear] = {}
        for year in years:
            self._user.debug("Check gaps notes "+year)
            oldnotes = self._data["notes"][year]
            newnotes = self.get_notes_online(year)
            for i in set().union(oldnotes.keys(), newnotes.keys()):
                if i not in newnotes:
                    newnotes[i] = oldnotes[i]
                    newnotes[i].setr_status("del")
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], only_diff=True, text="Suppression\n")
                    sended = True 
                elif i not in oldnotes:
                    newnotes[i].setr_status("add")
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], only_diff=True, text="Ajout\n")
                    sended = True 
                elif oldnotes[i] == newnotes[i]:
                    pass
                else:
                    self.send_notes_course(year, i, chat_id, notes=oldnotes[i], only_diff=True, text="Ancien\n")
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], only_diff=True, text="Nouveau\n")
                    sended = True 
                    #newnotes[i].merge(oldnotes[i])
                    #self.send_notes_course(year, i, chat_id, notes=newnotes[i], only_diff=True)

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

class GradeCourse:
    def __init__(self, name, average):
        self.name = name
        self.average = average
        self.evals = {}
        self.status = None
    def __eq__(self, other):
        if not isinstance(other, GradeCourse):
            return NotImplemented
        return self.name == other.name \
                and self.average == other.average \
                and self.evals == other.evals

    def str(self, year, all=True):
        if(self.status == "add"):
            prefix = "(+)"
        elif(self.status == "del"):
            prefix = "(-)"
        elif(self.status == "change"):
            prefix = "(~)"
        else:
            prefix = "   "
        text = ""
        for typ,notelst in self.evals.items():
            text += notelst.str(typ)
        if text != "" or all or self.status != None:
            return prefix + " " + year + " - "+self.name+" (moy="+self.average+")\n" + text
        else:
            return ""

    def merge(self, other):
        if other.name != self.name:
            self.dname = self.name+"→"+other.name
            self.name = other.name
            self.status = "change"
        if other.average != self.average:
            self.daverage = self.average+"→"+other.average
            self.average = other.average
            self.status = "change"
        for k in set().union(self.evals.keys(), other.evals.keys()):
            if k not in self.evals:
                self.evals[k] = other.evals[k]
                other.evals[k].setr_status("add")
            elif k not in other.evals:
                self.evals[k].setr_status("del")
            else:
                self.evals[k].merge(other.evals[k])

    def set_status(self, status):
        self.status = status
    def setr_status(self, status):
        self.set_status(status)
        for k in self.evals.keys():
            self.evals[k].setr_status(status)


class GradeGroupEvaluation:
    def __init__(self, average, coeff):
        self.average = average
        self.coeff = coeff
        self.evals = []
        self.status = None
    def __eq__(self, other):
        if not isinstance(other, GradeGroupEvaluation):
            return NotImplemented
        return self.average == other.average \
                and self.coeff == other.coeff \
                and self.evals == other.evals
    def str(self, typ, all=True):
        if(self.status == "add"):
            prefix = "(+)"
        elif(self.status == "del"):
            prefix = "(-)"
        elif(self.status == "change"):
            prefix = "(~)"
        else:
            prefix = "   "
        text = ""
        for data in self.evals:
            text += data.str()
        if text != "" or all or self.status != None:
            return prefix+" "+typ+" (moy="+self.average+", "+self.coeff+"%)\n"+text
        else:
            return ""


    def merge(self, other):
        if self.average != other.average:
            self.daverage = self.average+"→"+other.average
            self.average = other.average
            self.status = "change"
        if self.coeff != other.coeff:
            self.dcoeff = self.coeff+"→"+other.coeff
            self.coeff = other.coeff
            self.status = "change"
        for k in range(max(len(self.evals), len(other.evals))):
            if k >= len(self.evals):
                print("ALL Add")
                self.evals[k] = other.evals[k]
                other.evals[k].set_status("add")
            if k >= len(other.evals):
                print("ALL Del")
                self.evals[k].set_status("del")
            else:
                print("ALL Merge")
                self.evals[k].merge(other.evals[k])

    def set_status(self, status):
        self.status = status
    def setr_status(self, status):
        self.set_status(status)
        for k in self.evals:
            k.set_status(status)

class GradeEvaluation:
    def __init__(self, description, date, classaverage, grade, coeff):
        self.date = date
        self.description = description
        self.classaverage = classaverage
        self.grade = grade
        self.coeff = coeff
        self.status = None
    def __eq__(self, other):
        if not isinstance(other, GradeEvaluation):
            return NotImplemented
        return self.date == other.date \
                and self.description == other.description \
                and self.classaverage == other.classaverage \
                and self.grade == other.grade \
                and self.coeff == other.coeff
    def str(self, all=True):
        if(self.status == "add"):
            prefix = "(+)"
        elif(self.status == "del"):
            prefix = "(-)"
        elif(self.status == "change"):
            prefix = "(~)"
        else:
            prefix = "   "
        if all or self.status != None:
            return prefix+"  «"+self.description+"»\n" \
                + prefix+"    "+self.date+" ("+self.grade+", cls="+self.classaverage+", "+self.coeff+"%)\n"
        else:
            return ""

    def merge(self, other):
        if self.date != other.date:
            self.ddate = self.date+"→"+other.date
            self.date = other.date
            self.status = "change"
        if self.description != other.description:
            self.ddescription = self.description+"→"+other.description
            self.description = other.description
            self.status = "change"
        if self.classaverage != other.classaverage:
            self.dclassaverage = self.classaverage+"→"+other.classaverage
            self.classaverage = other.classaverage
            self.status = "change"
        if self.grade != other.grade:
            self.dgrade = self.grade+"→"+other.grade
            self.grade = other.grade
            self.status = "change"
        if self.coeff != other.coeff:
            self.dcoeff = self.coeff+"→"+other.coeff
            self.coeff = other.coeff
            self.status = "change"
    def set_status(self, status):
        self.status = status


