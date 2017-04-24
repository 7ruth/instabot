"""
    instabot example

    Workflow:
        Like rescent medias from your timeline feed.
"""

import sys
import os
import time
import argparse

sys.path.append(os.path.join(sys.path[0], '../'))
from instabot import Bot

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument('-u', type=str, help="username")
parser.add_argument('-p', type=str, help="password")
parser.add_argument('-proxy', type=str, help="proxy")
args = parser.parse_args()

bot = Bot(username=args.u, password=args.p,
          proxy=args.proxy)

wait = 5 * 60  # in seconds

bot.logger.info("This bot will like last medias from your feed and sleep "
                "for %d minutes between iterations." % (wait / 60))
while True:
	bot.like_timeline()
	time.sleep(wait)
