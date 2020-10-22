# r/destiny bot

Reddit automation bot to post daily moderator threads. Written in Python3 with PRAW. This Reddit bot will create a daily thread asking for news links and likely more in the future™.

## Configure It

1. copy `.example.env` to `.env`

2. Get a Reddit account + app tokens at https://ssl.reddit.com/prefs/apps/
2.1. Make the Reddit a subreddit moderator with `Posts` permissions
```
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=destinyggbot 0.01 - contact@destiny.gg
REDDIT_USERNAME=destinyggbot
REDDIT_PASSWORD=
```
3. Configure the subreddit settings
```
REDDIT_SUBREDDIT=Destiny
REDDIT_FLAIR_ID=24539a60-c72a-11e5-8462-0e738b837a3d
REDDIT_TTL_MINS=1440
```
4. Set streamers local timezone
```
LOCALE_TIMEZONE=America/Los_Angeles
```
5. Configure DB settings. Set `SQLITE_FAILURE_STALL` to `false` on first setup
```
SQLITE_DATABASE=reddit.sqlite
SQLITE_FAILURE_STALL=true
```
## Personalize it

Edit `template.md`. This file is read and used for the subreddit post. Supports full Reddit markdown: https://www.reddit.com/wiki/markdown

## Set Up

Install dependencies (and a venv)
```Bash
python3 -m pip install -r requirements.txt
```

## Running

This script is configured to run as a cronjob, an example is:

```
0 0/1 * * * (cd /home/bots/reddit; /usr/bin/python3 app.py)
```

This will run the job hourly at the start of the hour.