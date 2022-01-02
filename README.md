# Workflow

## Datasets

Users and Tweets, with queried deletion metadata, from historical archives:
 * `datasets/pandas/users_ia.pkl`, `datasets/pandas/tweets_ia.pkl`
   * Approx 40k HK-based users, 300k Tweets
 * `datasets/pandas/control_users_ia.pkl`, `datasets/pandas/control_tweets_ia.pkl`
   * Approx 20k NYC-based users, 130K Tweets

All queried Tweets from users in `datasets/pandas/users_ia`:
 * `timeline_tweets.pkl`
   * Approx 6 million Tweets from 1500 HK-based users

To generate these datasets:

### 1. Fetch & filter Internet Archive Tweet Stream

Run `snakemake -j<number of cores to use>` in order to fetch and filter the entire historical [Internet Archive tweet stream](https://archive.org/details/twitterstream). This will run the code in `twitter/` to fetch any archive results in the `DATETIME_RANGE` specified in the Snakefile.

This can take on the order of several days. The Internet Archive upload speed is very slow, and the entire Twitter archive is very large, and can contain up to 1-2GB of Tweets per day.

This process will create a directory `results/users`, which will contain a json file for every day in the date range specified.
* Output: `results/users/*`

### 2. Extract users

Run `notebook/users_from_tweets.ipynb` to produce a `users.json` file that aggregates all the data from the above process. Remember to set `TWEETS_DIR` to point to the directory containing the filtered Twitter stream.
* Input: `results/users/*`
* Output: `datasets/users/ia/users.json`

### 3. Query to see if users and tweets still exist today (hits Twitter API)

Run `notebook/query_users.ipynb`. It will query Twitter's API to determine whether the tweets and users in `users.json` are still available today, or whether they have since been deleted or protected.

Since it hits the Twitter API it will take some time, up to 30 minutes. It writes results to the output file as it goes, so stopping in the middle is also safe.

* Input: `datasets/users/ia/users.json`
* Output: `datasets/queried/users.jsonl`, `datasets/queried/tweets.jsonl`

### 4. Generate pandas DB files for processing.

Run `notebook/json-to-pandas.ipynb` to convert all users and tweets (and associated deletion metadata) into an easily query-able Pandas database file.

* Input: `datasets/queried/users.jsonl`, `datasets/queried/tweets.jsonl`
* Output: `datasets/pandas/users_ia.pkl`, `datasets/pandas/tweets_ia.pkl`

### 5. Count how many Tweets we could probably fetch. (hits Twitter API)

Run `python3 fetch-timeline-counts.py` to determine how many Tweets each of these users have made within the supplied date range (default: 2019/1/1 - 2022/1/1).

Note: this does not count towards our total monthly API limits, but it is very slow because a single request can only return (maximum) one month of Tweet counts, and we are trying to see how many Tweets each account makes over several years. It can only process approximately 8-9 total accounts (aka 300 requests) every 15 minutes, so it can process 800 accounts per 24-hour period.

However, it is important to do this step in order to figure out which accounts to prioritize when actually fetching Tweets in the next step, which will count towards an overall monthly API cap.
* Input: `datasets/pandas/users_ia.pkl`
* Output: `hk_users_tweet_counts.json`

### 6. Fetch all the Tweets. (hits Twitter API and counts towards monthly Tweet limit)

Run `python3 fetch-timelines.py`. Each request can retrieve up to 500 Tweets, so it is generally much faster than step 5, but each Tweet will count towards your monthly API Tweet cap. Can alter script in order to prioritize fetching Tweets of accounts with fewer Tweets (accounts with massive numbers of Tweets tend to be marketing or organizational accounts, so they may not contain as much signal for our purposes).

* Input: `hk_users_tweet_counts.json`
* Output: `tweets_timeline.pkl`

## Analyses
