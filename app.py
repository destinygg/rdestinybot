import os
import praw
import sqlite3
import logging
from datetime import datetime, timedelta
from pytz import timezone
from dotenv import load_dotenv

# load in envfile
load_dotenv()

# init logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# init reddit
reddit = praw.Reddit(
    client_id=os.environ.get('REDDIT_CLIENT_ID'),
    client_secret=os.environ.get('REDDIT_CLIENT_SECRET'),
    user_agent=os.environ.get('REDDIT_USER_AGENT'),
    username=os.environ.get('REDDIT_USERNAME'),
    password=os.environ.get('REDDIT_PASSWORD')
)

if not reddit.read_only:
    logger.info("Connected to Reddit with Read/Write access!")

# init the DB
dbconn = sqlite3.connect(os.environ.get('SQLITE_DATABASE'))
dbcursor = dbconn.cursor()

# check if we need to crash out because the db is fucked, or just make the schema
dbcursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='posts'")
if dbcursor.fetchone()[0] == 0:
    if os.environ.get('SQLITE_FAILURE_STALL') == 'true':
        logger.critical("SQLITE_FAILURE_STALL enabled and DB is empty. Disable SQLITE_FAILURE_STALL to init DB or check storage.")
        exit()
    else:
        logger.warning("Creating SQLite Database.")
        dbcursor.execute("""
            CREATE TABLE posts (
                reddit_id TEXT NOT NULL,
                reddit_posted timestamp,
                reddit_expires timestamp,
                completed integer
            )
        """)
        dbconn.commit()


def create_post():
    # create a localized Datetime object to the LOCALE_TIMEZONE in .env
    localized_tz = timezone(os.environ.get('LOCALE_TIMEZONE'))
    localized_datetime = datetime.now(localized_tz)

    # format a date and create the Title
    date_format = localized_datetime.strftime('%b %d, %Y')
    title = f'News for Destiny: {date_format}'
    logger.info(f"Creating new reddit thread: {title}")

    # load in the template.md file used as the body
    with open('template.md') as f:
        template = f.read()

    # post it to the reddits
    submission = reddit.subreddit(os.environ.get('REDDIT_SUBREDDIT')).submit(
        title=title,
        selftext=template,
        send_replies=False
    )

    # sticky the new post
    submission.mod.sticky()

    # flair the new post
    submission.mod.flair(flair_template_id=os.environ.get('REDDIT_FLAIR_ID'))

    # get the expiry time
    dt_created = datetime.fromtimestamp(submission.created_utc)
    dt_expire = dt_created + timedelta(minutes=int(os.environ.get('REDDIT_TTL_MINS')) - 10)

    # write the post to the db
    query = "INSERT INTO 'posts' ('reddit_id', 'reddit_posted', 'reddit_expires', 'completed') VALUES (?,?,?,?)"
    query_values = (submission.id, dt_created.isoformat(), dt_expire.isoformat(), 0)
    dbcursor.execute(query, query_values)
    dbconn.commit()


def remove_post(reddit_id):
    submission = reddit.submission(id=reddit_id)

    # lock thread
    submission.mod.lock()

    # remove
    try:
        submission.mod.remove()
    except Exception as e:
        logger.critical(f"Exception thrown attempting to delete thread. Error:{e}")
    else:
        dbcursor.execute("UPDATE posts set completed=1 where reddit_id=?", (reddit_id,))
        dbconn.commit()

def check_post():
    # ask for all posts, if there are no post history + stall enabled, fail out safe
    dbcursor.execute("SELECT * FROM posts")
    res = dbcursor.fetchall()
    if len(res) == 0 and os.environ.get('SQLITE_FAILURE_STALL') == 'false':
        logger.warning("DB is empty + SQLITE_FAILURE_STALL is false. Creating genesis post.")
        create_post()

    # query for anything in the DB marked as 0 for completed
    dbcursor.execute("SELECT * FROM posts WHERE completed='0'")
    res = dbcursor.fetchall()

    posts = len(res)
    logger.info(f"{posts} are marked as incomplete")

    # loop through pending posts 0[0] = id, 0[1] = create, 0[2] = expire, 0[3] = status
    for post in res:
        dt_expire = datetime.strptime(post[2], "%Y-%m-%dT%H:%M:%S")
        dt_now = datetime.utcnow()

        # if the post is past expiry, run delete_post(), make a new post
        if dt_now > dt_expire:
            logger.info(f"Post {post[0]} expired at {post[2]}. Running removal...")
            remove_post(post[0])
            posts = posts - 1
        else:
            logger.info(f"Post {post[0]} still active, will expire at {post[2]}.")

    # if there are 0 pending threads, make one
    if posts == 0:
        create_post()

if __name__ == "__main__":
    check_post()