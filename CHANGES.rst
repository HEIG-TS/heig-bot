ChangeLog
=========

0.3.2 (2020-03-03)
------------------

New features:

- Add documentation on readthedocs
- #12 `/unsetgapscredentials` remove password on user file

Bug fixes:

- #21 Parsing course without exam
- #20 Hide telegrame id on `/help botcmd`
- #10 Display good error message when `/calendar` without cache and 
  without credentials

0.3 (2020-02-29)
----------------

**For update**:

- Need re-create pickle user-database, format has changed

Breaking changes:

- User config in pickle file.

New features:

- Move class to package heig
- Update documentation
- Add telegram userid and chatid to help message
- Clear unsued code on gaps.py

Bug fixes:

- #2 Timetable access
- #3 Update doc /admin*

0.2 (2020-02-20)
----------------

**For update**:

- remove all file in your `database_directory` (see your `config.json`, default: `/var/heig-bot`)
- all user need to `/setgapscredentials` again

New features:

- Rewrite gaps grade parsing with beautifulsoup4
- remove depends curl xmllint
- add depends python-beautifulsoup4
- user data format change from json to pickle
- update of README.md

0.1 (2019-11-26)
----------------
- First version
