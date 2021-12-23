import archive
import logging
import json

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


def main():
    logging.getLogger().setLevel(logging.INFO)
    ta = archive.TweetArchive(2019,7,2)
    ta.fetch()
    with open("2019-7-2-hk.json", "w") as f:
        for tweet in ta.tweets():
            if hk_in_profile(tweet.user):
                f.write(tweet.to_json())
                f.write("\n")
                f.flush()

if __name__=="__main__":
    main()
