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
prev_until = "2021-07-01"
fromtime = datetime.date(2019, 1, 1)
until = datetime.date(2021, 12, 31)
tweets_db_file = "notebook/timeline_tweets.pkl"


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


def get_and_dump_tweets(file_to_dump, endpoint, params, counted=False):
    global start_timer
    # get count; make sure we don't pull too many tweets
    if not counted:
        time.sleep(1)
        count_tweets = api.request("tweets/counts/all",
                                   {"query": params["query"], "start_time": params["start_time"], "end_time": params["end_time"], "granularity": "day"})
        count_data = count_tweets.json()
        if "meta" not in count_data:
            print(count_data)
            sleep_off_ratelimit()
            return get_and_dump_tweets(file_to_dump, endpoint, params, False)
        n_tweets = count_data["meta"]["total_tweet_count"]
        if n_tweets > 100:
            print(f"{n_tweets} in most recent month, too many tweets to pull! Skipping")
            return 0
        else:
            print(f"{n_tweets} in most recent month. Fetching since 2019...")

    pager = TwitterPager(api, endpoint, params)
    n_tweets = 0
    with open(file_to_dump, "a+") as f:
        time.sleep(1)
        try:
            for tweet in pager.get_iterator(wait=1):
                if n_tweets > 0 and n_tweets % 1000 == 0:
                    print(f"    ...{n_tweets} fetched so far...")
                n_tweets += 1
                json.dump(tweet, f)
                f.write("\n")
        except TwitterRequestError as e:
            print(e)
            sleep_off_ratelimit()
            return get_and_dump_tweets(file_to_dump, endpoint, params, True)
    print(f"...fetched {n_tweets} tweets")
    return n_tweets


users_df = pd.read_pickle("notebook/users_ia_hk.pkl")
all_hk_users = set(users_df.loc[users_df["deleted"] == False]["id"])

df = pd.read_pickle(tweets_db_file)
users = df["author_id"].unique()

# count = 0
# for i, user in enumerate(all_hk_users):
#     if str(user) in users:
#         count += 1
#         print(user)
# 
# print(count)
offset = 1607

total_tweets = 0
for i, user in enumerate(all_hk_users):
    if total_tweets > 1000000:
        break
    if str(user) in users:
        continue
    if i < offset:
        continue
    print(f"User {i}/{len(all_hk_users)}: {user}")
    # times = df[df["author_id"] == user]["created_at"]
    # latest_tweet = times.max()
    # if latest_tweet > prev_until:
    #     continue
    params = {
        "tweet.fields": "id,text,author_id,created_at,withheld",
        "expansions": "geo.place_id", #,referenced_tweets.id",
        "max_results": 500,
        "start_time": fromtime.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "end_time": until.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "query": f"from:{user}"
    }
    n_tweets = get_and_dump_tweets("notebook/timelines.json", "tweets/search/all", params)
    total_tweets += n_tweets

