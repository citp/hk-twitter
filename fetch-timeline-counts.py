import os
import json
import datetime
import time

from dateutil import parser
import glob
import json
from dataclasses import dataclass, field
from dacite import from_dict, Config
from typing import Optional
import pandas as pd

CREDENTIALS_FILE = "creds.txt"
fromtime = datetime.date(2019, 1, 1)
until = datetime.date(2022, 1, 1)


from TwitterAPI import TwitterAPI, TwitterOAuth, TwitterRequestError, TwitterPager

o = TwitterOAuth.read_file(CREDENTIALS_FILE)
api = TwitterAPI(o.consumer_key, o.consumer_secret, o.access_token_key, o.access_token_secret, auth_type="oAuth2", api_version="2")

start_timer = datetime.datetime.utcnow()

def sleep_off_ratelimit():
    global start_timer
    to_sleep = (15*60) - (datetime.datetime.utcnow() - start_timer).total_seconds() + 1
    print(f"Sleeping off the rate limit, {to_sleep} seconds...")
    time.sleep(to_sleep)
    start_timer = datetime.datetime.utcnow()


def count_tweets(file_to_dump, endpoint, params):
    global start_timer
    pager = TwitterPager(api, "tweets/counts/all", params)
    n_tweets = 0
    time.sleep(1)
    try:
        for result in pager.get_iterator(wait=1):
            n_tweets += result["tweet_count"]
    except TwitterRequestError as e:
        print(e)
        sleep_off_ratelimit()
        return count_tweets(file_to_dump, endpoint, params)
    return n_tweets


users_df = pd.read_pickle("notebook/users_ia_hk.pkl")
all_hk_users = set(users_df.loc[users_df["deleted"] == False]["id"])

counted_users = set()
with open("hk_users_tweet_counts.json", "r") as f:
    for line in f:
        counted_users.add(json.loads(line.strip())["id"])

offset = 0
for i, user in enumerate(all_hk_users):
    if user in counted_users:
        continue
    if i < offset:
        continue
    print(f"User {i}/{len(all_hk_users)}: {user}")
    params = {
        "start_time": fromtime.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end_time": until.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "query": f"from:{user}",
        "granularity": "day",
    }
    n_tweets = count_tweets("notebook/timelines.json", "tweets/search/all", params)
    print(f"... has {n_tweets} tweets from 1/1/2019 to 1/1/2022")
    with open("hk_users_tweet_counts.json", "a+") as f:
        json.dump({"id": user, "count": n_tweets}, f)
        f.write("\n")

