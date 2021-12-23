import argparse
import os
from datetime import datetime
import logging
import json

import archive

def hk_in_profile(user):
    if not user.location:
        return False
    keywords = [ "hongkong", "hong kong", "🇭🇰", "香港" ]
    for keyword in keywords:
        if keyword.lower() in user.location.lower():
            return True
    if user.location.lower().strip == "hk":
        return True
    return False


def _ymd_from_str(date):
    dt = datetime.strptime(date, "%Y_%m_%d")
    return dt.year, dt.month, dt.day


def main(date, subdir=".", tmpdir="./tmp"):
    logging.getLogger().setLevel(logging.INFO)

    filepath = os.path.join(subdir, f"{date}_hk.json")
    year, month, day = _ymd_from_str(date)
    ta = archive.TweetArchive(year, month, day, subdir=tmpdir)
    ta.fetch()

    with open(filepath, "w") as f:
        for tweet in ta.tweets():
            if hk_in_profile(tweet.user):
                f.write(tweet.to_json())
                f.write("\n")
                f.flush()

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("date")
    parser.add_argument("--subdir", default=".")
    args = parser.parse_args()
    main(args.date, args.subdir)
