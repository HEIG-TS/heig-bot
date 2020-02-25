# HEIG bot
Telegram bot for check gradle in GAPS (HEIG-VD's platform for gradle).
This can also check regulary if a user have new gradle and send message if.

## Link
 - **Demo:** [https://t.me/uzka_heig_prod_bot](https://t.me/uzka_heig_prod_bot)
 - **News:** [https://t.me/heig_bot_news](https://t.me/heig_bot_news)


## Depends
 - python-telegram-bot
 - beautifulsoup4

### On Debian buster and earlier
```bash
pip3 install python-telegram-bot beautifulsoup4
```

### On Debian bullseye/sid
```bash
apt install python3-python-telegram-bot python3-bs4
```

### On Arch Linux
```bash
sudo pacman -S python-telegram-bot python-beautifulsoup4
```

## Installation

```bash
cd /opt/
git clone https://github.com/g-roch/heig-bot.git -b stable
cp heig-bot/config.json.sample heig-bot/config.json
mkdir -p /var/heig-bot/ # set right for script can write
```

### Create bot

You need create a telegram bot with BotFather, and copy
the bot key in `config.json`. (value of `bot_tocken`)

### Admin/Logs configuration 

heig-bot can have admin, you can copy telegram userid (it's a number)
to `config.json` in `admins_userid`.

heig-bot can send a message when he start, you can copy telegram userid 
(it's a number) to `config.json` in `admins_userid`.

You can see your telegram userid when you send `/help` to the `heig-bot`.
The bot can start without admin, but you need remove "" from `admins_userid`
and `logs_userid` in `config.json`, for empty array.

### Start bot

```bash
cd /opt/heig-bot && ./bot.py
```

### Auto update

add to cron :
```cron
*/5 * * * * cd /opt/heig-bot && ./cron.py
```
