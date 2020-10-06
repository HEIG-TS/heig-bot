#
# Regular cron jobs for the heig-bot package
#
0 4	* * *	root	[ -x /usr/bin/heig-bot_maintenance ] && /usr/bin/heig-bot_maintenance
