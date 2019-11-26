# HEIG bot
## Demo
[https://t.me/uzka_heig_prod_bot](https://t.me/uzka_heig_prod_bot)

## Depends
 - python-telegram-bot
 - curl
 - xmllint

### On Debian
```bash
pip3 install python-telegram-bot
apt install curl 
apt install libxml2-utils # for binary xmllint
```

## Installation

```bash
cd /opt/
git clone https://github.com/g-roch/heig-bot.git
mkdir -p /var/heig-bot/ # set right for script can write
```

### Start bot

```bash
cd /opt/heig-bot && ./bot.py
```

### Auto update

add to cron :
```cron
*/5 * * * * cd /opt/heig-bot && ./cron.py
```
