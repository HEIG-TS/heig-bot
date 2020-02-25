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
URL_TIMETABLE = URL_BASE+"/consultation/horaires/"

class GapsError(Exception):
    """
        Class for manage exception on Gaps
    """
    pass

class Gaps:
    """
        Class for access to GAPS account

        :ivar _user: User object for GAPS access
        :vartype _user: User

        :ivar _data: GAPS information
            _data["notes"][2020]["ANA"] = GradeCourse
        :vartype _data: User
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

    def is_registred(self):
        """
            Indicate if we have credentials for GAPS
        """
        return "gapsid" in self._data

    def set_credentials(self, username, password):
        """
            Set credentials for GAPS

            :param username: GAPS username, it can be different to SSO
            :type username: str

            :param password: GAPS password
            :type password: str
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

            :param year: Year to get (for 2020-2021 is 2020)
            :type year: 
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
        """
            Get notes from cache, if no cache for this year download from GAPS

            :param year: Year to get (for 2020-2021 is 2020)
            :type year: 
        """
        if not "notes" in self._data:
            self._data["notes"] = {}
        if not str(year) in self._data["notes"]:
            self.get_notes_online(year)
        return self._data["notes"][year]

    def send_notes_course(self, year, course, chat_id, notes=0, prefix=""):
        """
            Send notes for branche

            :param year: Year to send (for 2020-2021 is 2020)
            :type year: 

            :param course: branchname to send
            :type course: str

            :param chat_id: send message to this chat id
            :type chat_id: int

            :param notes: notes to send, if isn't specified, it's getted from cache or online
            :type notes: 

            :param prefix: prefix of message to user
            :type prefix: str
        """
        if 0 == notes:
            notes = self.get_notes(year)[course]

        text = prefix + notes.str(year)

        self._user.send_message(text, chat_id=chat_id) #, parse_mode="Markdown")
        return True

    def send_notes(self, year, courses, chat_id):
        """
            Send notes for multiple branche

            :param year: Year to send (for 2020-2021 is 2020)
            :type year: 

            :param courses: list of branchname to send
            :type courses: 

            :param chat_id: send message to this chat id
            :type chat_id: int
        """
        notes = self.get_notes(year)
        c = []
        for i in courses:
            c.insert(0, i.lower())
        for course in notes.keys():
            if course.lower() in c or len(c) == 0:
                self.send_notes_course(year, course, chat_id)

    def send_notes_all(self, chat_id):
        """
            Send all notes in cache

            :param chat_id: send message to this chat id
            :type chat_id: int
        """
        fullnotes = self._data["notes"]
        for year in sorted(fullnotes.keys()):
            self.send_notes(year, [], chat_id)


    def check_gaps_notes(self, chat_id, auto=False):
        """
            Check update on GAPS

            :param chat_id: send message to this chat id
            :type chat_id: int

            :param auto: Indicate if this function is called by user or by cron
            :type auto: bool
        """
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
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], prefix="Suppression\n")
                    sended = True 
                elif i not in oldnotes:
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], prefix="Ajout\n")
                    sended = True 
                elif oldnotes[i] == newnotes[i]:
                    pass
                else:
                    self.send_notes_course(year, i, chat_id, notes=oldnotes[i], prefix="Ancien\n")
                    self.send_notes_course(year, i, chat_id, notes=newnotes[i], prefix="Nouveau\n")
                    sended = True 

        if not sended and not auto:
            self._user.send_message("No update", chat_id=chat_id)

class GradeCourse:
    """
        Class for stockage of grade course.

        Cette classe corresponds à une branche

        :ivar name: 
        :vartype name: str

        :ivar average: 
        :vartype average:

        :ivar evals: 
        :vartype evals:
    """
    def __init__(self, name, average):
        """
            Make a new GradeCourse object

            :param name: Name of course
            :type name: str

            :param average: Average of course for user
            :type name: str
        """
        self.name = name
        self.average = average
        self.evals = {}

    def __eq__(self, other):
        if not isinstance(other, GradeCourse):
            return NotImplemented
        return self.name == other.name \
                and self.average == other.average \
                and self.evals == other.evals

    def str(self, year):
        text = ""
        for typ,notelst in self.evals.items():
            text += notelst.str(typ)
        if text != "":
            return year + " - "+self.name+" (moy="+self.average+")\n" + text
        else:
            return ""

class GradeGroupEvaluation:
    """
        Class for stockage of grade group of evaluation

        Cette classe corresponds à un groupe d'une branche (labo ou controlecontinus)

        :ivar average: 
        :vartype average:

        :ivar coeff: 
        :vartype coeff:

        :ivar evals: 
        :vartype evals:
    """
    def __init__(self, average, coeff):
        self.average = average
        self.coeff = coeff
        self.evals = []
    def __eq__(self, other):
        if not isinstance(other, GradeGroupEvaluation):
            return NotImplemented
        return self.average == other.average \
                and self.coeff == other.coeff \
                and self.evals == other.evals
    def str(self, typ):
        text = ""
        for data in self.evals:
            text += data.str()
        if text != "":
            return typ+" (moy="+self.average+", "+self.coeff+"%)\n"+text
        else:
            return ""


class GradeEvaluation:
    """
        Class for stockage of a evaluation

        :ivar date: 
        :vartype date:

        :ivar description: 
        :vartype description:

        :ivar classaverage: 
        :vartype classaverage:

        :ivar grade: 
        :vartype grade:

        :ivar coeff: 
        :vartype coeff:
    """
    def __init__(self, description, date, classaverage, grade, coeff):
        self.date = date
        self.description = description
        self.classaverage = classaverage
        self.grade = grade
        self.coeff = coeff
    def __eq__(self, other):
        if not isinstance(other, GradeEvaluation):
            return NotImplemented
        return self.date == other.date \
                and self.description == other.description \
                and self.classaverage == other.classaverage \
                and self.grade == other.grade \
                and self.coeff == other.coeff
    def str(self):
        return "  "+self.description+"\n" \
            + "    "+self.date+" ("+self.grade+", cls="+self.classaverage+", "+self.coeff+"%)\n"

