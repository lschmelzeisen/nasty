import gzip
import json
import os
import warnings
from time import sleep
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from string_modification import html_to_api_converter, get_indices
from tweet import Tweet, Hashtag, UserMention, TweetURLMapping


warnings.warn(DeprecationWarning, "The functionality of this file was moved to the tweet class."
                                  "use from tweet import Tweet => Tweet.extract(url)")


def download_html(tweet_url, job=None) -> str:
    print(tweet_url)
    # Needed to change. The old didn't return tweets. So try this if you the parser
    # does not have tweets in it's tweets list, while you see them on the website
    # headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.00; Windows 98)'}
    headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'}
    tries = 0
    max_retries = 5

    while tries < max_retries:
        try:
            req = requests.get(tweet_url, headers=headers, timeout=5)
        except requests.exceptions.ConnectionError:
            tries += 1
            sleep(5)
            if tries == max_retries and job is not None:
                failed_jobs_collector(job, reason="requests.exceptions.ConnectionError")
        except requests.exceptions.Timeout:
            tries += 1
            sleep(5)
            if tries == max_retries and job is not None:
                failed_jobs_collector(job, reason="requests.exceptions.Timeout")
        else:
            if req.status_code == 404:
                return ""
            elif req.status_code == 200:
                return req.text


def failed_jobs_collector(job: Dict, reason: str) -> None:
    job["failed-because"] = reason
    with open("failedJobs.json", "a") as failed:
        failed.write(json.dumps(job))
        failed.write("\n")


def creation_time(tweet_id: int) -> int:
    snowflake_epoch = 1288834974657
    tweet_id = int(tweet_id)  # Since it was maybe given as str instead of int
    # Returns the sequence id of a given tweet id
    return (tweet_id >> 22) + snowflake_epoch


def only_whitespaces(text):
    for character in text:
        if character != " ":
            return False
    return True


def parse_html(html_data: str) -> str and List:
    # If download_html fails, e.g. due to connection lost,
    # BeautifulSoup raises a error for None as data
    if not html_data:
        warnings.warn("Empty or None html data in parse_html")
        return "", []
    # BeautifulSoup parser our html data. The chosen parser is "html5lib"
    # since otherwise you get fails at: &#10;&#10; => \n instead of => \n\n
    soup = BeautifulSoup(html_data, features="html5lib")
    if not soup:
        warnings.warn("Html data, but no soup")
        return "", []
    tweet_list = soup.find_all("table", class_="tweet")

    tweets = []
    # This block parses the name, screen_name (@x), created_at, text and id from a normal tweet.
    # e.g. one of the replies
    for raw_tweet in tweet_list:  # for includes if len(tweet_list) == 0, thanks to range()
        if raw_tweet.find("td", class_="tombstone-tweet-text") is None:

            # HTML collected and tested at: 2019-07-09
            # <a href="/MoshTimes?p=s">
            #   <strong class="fullname">
            #       Moshville Times
            #   </strong>
            # <div class="username"><span>@</span>MoshTimes</div></a>
            name = raw_tweet.find("strong", class_="fullname").contents[0].string
            # .find().content => ['\n      ', <span>@</span>, 'oste8minutes\n    ']
            screen_name = raw_tweet.find("div", class_="username").contents[2].string[:-5]

            # HTML collected and tested at: 2019-07-09
            # <td class="timestamp">
            #   <a name="tweet_1142868564866719744"
            #   href="/MoshTimes/status/1142868564866719744?p=p">
            #       23. Juni
            #   </a>
            # </td>
            created_at = raw_tweet.find("td", class_="timestamp").contents[1].string

            # HTML collected and tested at: 2019-07-09
            # <div class="tweet-text"
            # data-id="1142868564866719744">
            #   <div class="dir-ltr" dir="ltr">
            #       Tweet Text, entities (links, mentions, hashtags)
            #   </div>
            # </div>
            raw_tweet_text = raw_tweet.find("div", class_="tweet-text")
            full_text = raw_tweet_text.find("div", class_="dir-ltr").text[:-1]
            id_str = raw_tweet_text.get("data-id")

            # More examples for the entities are in github
            # => 09-ClassesRewrite-Parallelism in "Tweet Entities.html"
            entities_wrapper = raw_tweet_text.find("div", class_="dir-ltr")

            # HTML collected and tested at: 2019-07-09
            # <a href="/hashtag/Testtweet?src=hash"
            # data-query-source="hashtag_click"
            # class="twitter-hashtag dir-ltr"dir="ltr">
            # #Testtweet
            # </a>
            hashtags_list = entities_wrapper.find_all("a", class_="twitter-hashtag dir-ltr")
            hashtags = []
            for hashtag in hashtags_list:
                hashtags.append(Hashtag(hashtag.text[1:], (0, 0)))

            # HTML collected and tested at: 2019-07-09
            # <a href="https://t.co/I8NMVQeekO"
            # rel="nofollow noopener"
            # dir="ltr"
            # data-expanded-url="https://twitter.com/OHiwi2/status/1146162915491364866"
            # data-url="https://twitter.com/OHiwi2/status/1146162915491364866"
            # class="twitter_external_link dir-ltr tco-link"
            # target="_blank"
            # title="https://twitter.com/OHiwi2/status/1146162915491364866">
            #   twitter.com/OHiwi2/status/…
            # </a>
            urls_list = entities_wrapper.find_all("a",
                                                  class_="twitter_external_link dir-ltr tco-link")

            # HTML collected and tested at: 2019-07-09
            # <a href="https://t.co/c076qpkzt2"
            # data-pre-embedded="true"
            # rel="nofollow"
            # data-entity-id="1146165309189087233"
            # dir="ltr"
            # data-url="https://twitter.com/OHiwi2/status/1146165689390120960/video/1"
            # data-tco-id="c076qpkzt2"
            # class="twitter_external_link dir-ltr tco-link has-expanded-path"
            # target="_top"
            # data-expanded-path="/OHiwi2/status/1146165689390120960/video/1">
            #   pic.twitter.com/c076qpkzt2
            # </a>

            # Since we don't differentiate between links and uploaded media, we just add the media
            urls_list += entities_wrapper \
                .find_all("a", class_="twitter_external_link dir-ltr tco-link has-expanded-path")
            urls = []
            for url in urls_list:
                urls.append(
                    TweetURLMapping(url.get("href"), url.get("data-url"), url.text, (0, 0)))

            # HTML collected and tested at: 2019-07-09
            # <span class="tweet-reply-context username">
            # Reply to
            # <a href="/TJCobain">@TJCobain</a>
            # <a href="/TJ_Cobain">@TJ_Cobain</a>
            # and
            # <a href="/angelgab0525/status/1142583459698761728/reply">
            # 5
            # others
            # </a>
            # </span>
            reply_names = raw_tweet.find("div", class_="tweet-reply-context username")
            user_mentions = []
            if reply_names is not None:
                reply_names = reply_names.find_all("a")
                for reply in reply_names:
                    if not only_whitespaces(reply.text[1:]):
                        user_mentions.append(UserMention(reply.text[1:], "", (0, 0)))

            # HTML collected and tested at: 2019-07-09
            # <a href="/OHiwi2"
            # class="twitter-atreply dir-ltr"
            # dir="ltr"
            # data-mentioned-user-id="1117712996795658241"
            # data-screenname="OHiwi2">
            #   @OHiwi2
            # </a>
            user_mentions_list = entities_wrapper.find_all("a", class_="twitter-atreply dir-ltr")
            for user in user_mentions_list:
                user_mentions.append(
                    UserMention(user.text[1:], user.get("data-mentioned-user-id"), (0, 0)))

            # Modify string, get right indices for urls and user_mentions
            full_text, urls, user_mentions = html_to_api_converter(full_text, urls, user_mentions,
                                                                   screen_name)
            # Now also get indices of hashtags
            for hashtag in hashtags:
                start, end = get_indices(hashtag.text, full_text)
                hashtag.indices = (start - 1, end)
            user_mentions.reverse()
            # Create the tweet, and modify the full_text so its more like hte API
            tweet = Tweet(created_at, id_str, full_text, name, screen_name, hashtags, user_mentions,
                          urls)

            tweets.append(tweet)

    if soup.find("div", class_="w-button-more") is not None:
        next_site_head = "https://mobile.twitter.com"
        print("Next page is on the way.")
        next_site_tail = soup.find("div", class_="w-button-more").find("a").get("href")
        return next_site_head + next_site_tail, tweets
    else:
        return "", tweets


def extract(tweet_url: str, save_to: str, job: Dict = None) -> None:
    next_site = tweet_url
    tweet_collector = []
    while next_site:
        html_data = download_html(next_site, job)
        next_site, tweets = parse_html(html_data)
        tweet_collector.extend(tweets)
    # Got an error, if we used data in the current folder
    # "example.json.gz" and not "data/example.json.gz"
    if "/" in save_to:
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
    with gzip.open(save_to, "wt") as filepath:
        for tweet in tweet_collector:
            filepath.write(tweet.to_json())
            filepath.write("\n")
        if job:
            print(f"Saved the search for '{job['keyword']}' from {job['start_date']}")
