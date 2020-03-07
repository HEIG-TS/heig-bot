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

"""
    Parsing of notes is inspired/copied by https://gitlab.theswissbay.ch/heig/hidapo
"""

import json
import os.path
import re
from datetime import date

import arrow
import requests
from bs4 import BeautifulSoup
from ics import Calendar

URL_BASE = "https://gaps.heig-vd.ch/"
URL_CONSULTATION_NOTES = URL_BASE+"/consultation/controlescontinus/consultation.php"
URL_ATTENDANCE = URL_BASE+"/consultation/etudiant/"
URL_TIMETABLE = URL_BASE+"/consultation/horaires/"

DIR_DB_GAPS = "/heig.gaps/"
DIR_DB_TIMETABLE = "/heig.gaps.timetable/"

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
            _data["gapsid"] = id for GAPS
            _data["tracking"]["notes"] = bool (true for notes tracking)
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

    def tracking(self, type="notes") -> bool:
        """
            Indicate if tracking is enable
            
            :param type: Type of tracking (notes, ...)
            :type type: str
            :rtype: bool
        """
        if "tracking" in self._data and type in self._data["tracking"]:
            return self._data["tracking"][type]
        else:
            return False

    def set_tracking(self, type, value) -> None:
        """
            Set tracking mode for type

            :param type: Type of tracking (notes, ...)
            :type type: str
            :param value: True for enable tracking
            :type value: bool
            :rtype: None
        """
        if "tracking" not in self._data:
            self._data["tracking"] = {}
        self._data["tracking"][type] = value
        self._user.save()

    def is_registred(self):
        """
            Indicate if we have credentials for GAPS
        """
        return "gapsid" in self._data and "password" in self._data

    def get_timetable_ics(self, year, trimester, id, type, force=False):
        """
            Get ICS file.
            File in cache is used if possible.

            :param year: Year of timetable
            :type year: int

            :param trimester: Trimester of timetable
            :type trimester: int

            :param id: id of entity
            :type id: int

            :param type: type of entity
            :type type: int

            :param force: Force download and update cache
            :type force: bool
        """
        from heig.init import config
        dirname = config()["database_directory"]+DIR_DB_TIMETABLE+"/"+str(year)+"/"+str(trimester)+"/"+str(type)
        filename = dirname+"/"+str(id)+".ics"
        download = force or not os.path.isfile(filename)
        os.makedirs(dirname, exist_ok=True)
        if download:
            if not self.is_registred():
                raise GapsError("You are not registred")
            ics = requests.get(
                    URL_TIMETABLE,
                    auth=(self._data['username'], self._data['password']),
                    params={'annee':year,'trimestre':trimester, 'type':type, 'id':id, 'icalendarversion':2}
                ).text
            file = open(filename, "w")
            file.write(ics)
            file.close()
        else:
            file = open(filename, "r")
            ics = file.read()
            file.close();
        return ics

    def get_day_lesson(self, dt: arrow.Arrow = arrow.now(), text: bool = False):
        """

        :param dt: Date for show lesson
        :param text: Return type is text
        """
        if "gapsid" not in self._data:
            raise GapsError("You are not gaps id, please /setgapscredentials")
        c = Calendar(self.get_timetable_ics(2019, 3, self._data["gapsid"], 2))
        if text:
            ret = dt.format('*dddd D MMMM YYYY*\n', locale="fr")
            for i in c.timeline.on(dt):
                ret += "`" \
                       + i.begin.to('Europe/Paris').format('HH:mm') \
                       + "→" + i.end.to('Europe/Paris').format('HH:mm') \
                       + "`: *" + i.location + "*: " + str(i.name) + "\n"
            return ret
        else:
            return c.timeline.on(dt)

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

    def unset_credentials(self):
        del self._data["password"]
        self._user.save()

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
                        "(?P<mat>[^ ]+) - moyenne( hors examen)? : (?P<moy>[0-9.]+|-)",
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
        if chat_id < 0:
            level = "group"
        else:
            level = "full"
        if 0 == notes:
            notes = self.get_notes(year)[course]

        text = prefix + notes.str(year, level=level)

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

    def send_diff_gaps_notes(self, chat_id, oldnotes, newnotes, year) -> bool:
        if chat_id < 0:
            level = "group"
        else:
            level = "full"
        for i in set().union(oldnotes.keys(), newnotes.keys()):
            if i not in newnotes:
                text = oldnotes[i].str(year, "-", level)
                self._user.send_message(text, chat_id=chat_id)
                sended = True
                self._user.debug("A")
            elif i not in oldnotes:
                text = newnotes[i].str(year, "+", level)
                self._user.send_message(text, chat_id=chat_id)
                sended = True
                self._user.debug("B")
            elif GradeCourse.eq(oldnotes[i], newnotes[i], level):
                pass
            else:
                text = GradeCourse.diff(oldnotes[i], newnotes[i], year, level)
                if text != "":
                    self._user.send_message(text, chat_id=chat_id)
                    sended = True
                    self._user.debug("C")
        return sended

    def check_gaps_notes(self, chat_id=None):
        """
            Check update on GAPS

            :param chat_id: send message to this chat id (else send a private message)
            :type chat_id: int

        """
        if chat_id == None:
            chat_id = self._user._user_id
            auto = True
        else:
            auto = False
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

            if self.send_diff_gaps_notes(chat_id, oldnotes, newnotes, year):
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

    @classmethod
    def diff(cls, a, b, year, level="full"):
        if cls.eq(a, b, level):
            return ""
        else:
            if a.name == b.name:
                name = a.name
            else:
                name = a.name + "→" + b.name
            if a.average == b.average:
                average = a.average
            else:
                average = a.average + "→" + b.average
            if a.name == b.name and (a.average == b.average or level != "full"):
                symbol = " "
            else:
                symbol = "~"
            if level == "full":
                text = symbol + year + " - " + name + " (moy=" + average + ")\n"
            else:
                text = symbol + year + " - " + name + "\n"
            for i in list(set(a.evals.keys()) + set(b.evals.keys())):
                if i not in a.evals:
                    text += b.evals[i].str(i, "+")
                elif i not in b.evals:
                    text += a.evals[i].str(i, "-")
                else:
                    text += GradeGroupEvaluation.diff(a.evals[i], b.evals[i], i, level)
            return text

    @classmethod
    def eq(cls, a, b, level="full"):
        if level == "full" and (a.name != b.name or a.average != b.average):
            return False
        elif level != "full" and a.name != b.name:
            return False
        else:
            for typ,notelst in a.evals.items():
                if typ not in b.evals or not GradeGroupEvaluation.eq(notelst, b.evals[typ], level):
                    return False
            for typ,notelst in b.evals.items():
                if typ not in a.evals or not GradeGroupEvaluation.eq(a.evals[typ], notelst, level):
                    return False
            return True

    def str(self, year, prefix=" ", level="full"):
        text = ""
        for typ,notelst in self.evals.items():
            text += notelst.str(typ, prefix, level)
        if text != "":
            if level == "full":
                return prefix + year + " - "+self.name+" (moy="+self.average+")\n" + text
            else:
                return prefix + year + " - "+self.name+"\n" + text
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

    @classmethod
    def diff(cls, a, b, typ, level="full"):
        if cls.eq(a, b, level):
            return ""
        else:
            if a.coeff == b.coeff:
                coeff = a.coeff
            else:
                coeff = a.coeff + "→" + b.coeff
            if a.average == b.average:
                average = a.average
            else:
                average = a.average + "→" + b.average
            if a.coeff == b.coeff and (a.average == b.average or level != "full"):
                symbol = " "
            else:
                symbol = "~"
            if level == "full":
                text = symbol + typ + " (moy=" + average + ", " + coeff + "%)\n"
            else:
                text = symbol + typ + "(" + coeff + ")\n"
            for i in range(0, max(len(a.evals), len(b.evals))):
                if i in a.evals and i in b.evals:
                    text += GradeEvaluation.diff(a, b, level)
                elif i in a.evals:
                    text += a.str("-")
                else:
                    text += b.str("+")
            return text

    @classmethod
    def eq(cls, a, b, level="level"):
        if level == "full":
            if a.coeff != b.coeff or a.average != b.average or len(a.evals) != len(b.evals):
                return False
            for i in range(0, len(a.evals)):
                if not GradeEvaluation.eq(a.evals[i], b.evals[i], level):
                    return False
            return True
        else:
            if a.coeff != b.coeff or len(a.evals) != len(b.evals):
                return False
            for i in range(0, len(a.evals)):
                if not GradeEvaluation.eq(a.evals[i], b.evals[i], level):
                    return False
            return True

    def str(self, typ, prefix=" ", level="full"):
        text = ""
        for data in self.evals:
            text += data.str(prefix, level)
        if text != "":
            if level == "full":
                return prefix + typ + " (moy=" + self.average + ", " + self.coeff + "%)\n" + text
            else:
                return prefix + typ + " (" + self.coeff + "%)\n" + text
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

    @classmethod
    def diff(cls, a, b, level="full"):
        """
            
            :param a:
            :type a: GradeEvaluation
            :param b:
            :type b: GradeEvaluation
            :param level: "full" or "group" (group hide personal note)
            :type level: str
            :return:
        """
        if cls.eq(a, b, level):
            return ""
        else:
            if a.description == b.description:
                description = a.description
            else:
                description = a.description + "→" + b.description
            if a.date == b.date:
                date = a.date
            else:
                date = a.date + "→" + b.date
            if a.grade == b.grade:
                grade = a.grade
            else:
                grade = a.grade + "→" + b.grade
            if a.classaverage == b.classaverage:
                classaverage = a.classaverage
            else:
                classaverage = a.classaverage + "→" + b.classaverage
            if a.coeff == b.coeff:
                coeff = a.coeff
            else:
                coeff = a.coeff + "→" + b.coeff
            if level == "full":
                return "~ "+description+"\n" \
                    + "~   "+date+" (class="+classaverage+", "+coeff+"%)\n"
            else:
                return "~ "+description+"\n" \
                    + "~   "+date+" ("+grade+", cls="+classaverage+", "+coeff+"%)\n"

    @classmethod
    def eq(cls, a, b, level="full"):
        """

            :param a:
            :type a: GradeEvaluation
            :param b:
            :type b: GradeEvaluation
            :param level:
            :return:
        """
        if level == "full":
            return a.date == b.date \
                    and a.description == b.description \
                    and a.classaverage == b.classaverage \
                    and a.grade == b.grade \
                    and a.coeff == b.coeff
        else:
            return a.date == b.date \
                    and a.description == b.description \
                    and a.classaverage == b.classaverage \
                    and a.coeff == b.coeff

    def str(self, prefix=" ", level="full"):
        if level == "full":
            return prefix+" "+self.description+"\n" \
                + prefix+"   "+self.date+" ("+self.grade+", cls="+self.classaverage+", "+self.coeff+"%)\n"
        else:
            return prefix+" "+self.description+"\n" \
                + prefix+"   "+self.date+" (class="+self.classaverage+", "+self.coeff+"%)\n"

