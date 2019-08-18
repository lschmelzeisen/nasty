"""
Class collection containing the main Tweet class.
As well as a class for Hashtag, UserMention and TweetURLMapping
"""
import datetime
import gzip
import json
import os
import uuid
import warnings
from datetime import date, timedelta
from pathlib import Path
from time import sleep
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup


class Hashtag:
    """The Hashtag class. Hashtag has it's text and the indices."""

    def __init__(self, text: str, indices: Tuple[int, int]):
        # e.g. "brexit"
        self.text = text
        # e.g. (16,22)
        self.indices = indices

    def __str__(self):
        return self.__dict__.__str__()


class UserMention:
    """The UserMention class. Got a @screen_name,
    if mentioned and not only answered too the user_id and the indices"""

    def __init__(self, screen_name: str, id_str: str, indices: Tuple[int, int]):
        # e.g. OHiwi-2
        self.screen_name = screen_name
        # e.g. "1117712996795658241"
        self.id_str = id_str
        # e.g. (14, 21)
        self.indices = indices

    def __str__(self):
        return self.__dict__.__str__()


class TweetURLMapping:
    """The TweetURLMapping class. Got the short url, the url and the displayed
    url + indices"""

    def __init__(self,
                 url: str,
                 expanded_url: str,
                 display_url: str,
                 indices: Tuple[int, int]):
        # e.g. "https:\/\/t.co\/Dw84m8xRGw" | short t.co link
        self.url = url
        # e.g. "http:\/\/google.com" | the whole unchanged link
        self.expanded_url = expanded_url
        # e.g. "google.com" | the displayed part of the whole unchanged link
        self.display_url = display_url
        # e.g. (18,41)
        self.indices = indices

    def __str__(self):
        return self.__dict__.__str__()


class Tweet:
    """
    The main Tweet class.
    Got all information we can currently get from extracting it out of html
    data. That is: creation date, id, the text, hashtags, user mentions, urls,
    the authors name and short name.
    """

    # adv: bool   <= declares if its from API or ADVsearch. Want that?

    def __init__(self,
                 created_at: str,
                 tweet_id: str,
                 full_text: str,
                 name: str,
                 screen_name: str,
                 hashtags: List[Hashtag],
                 user_mentions: List[UserMention],
                 urls: List[TweetURLMapping],
                 evaluation: List[str] = list()) -> None:
        tweet_id = str(tweet_id)
        self.created_at = created_at
        self.id_str = tweet_id
        self.full_text = full_text
        self.hashtags = hashtags
        self.user_mentions = user_mentions
        self.urls = urls
        self.name = name
        self.screen_name = screen_name
        self.evaluation = evaluation

    # Quick hacky implementation, will fix soon.
    @classmethod
    def run_job(cls, keyword: str, date: date, lang: str) -> List['Tweet']:
        since = date
        until = date + timedelta(days=1)
        url = (f"https://mobile.twitter.com/search?q={keyword}"
               f"%20since%3A{since}"
               f"%20until%3A{until}"
               f"%20lang%3A{lang}&src=typed_query")
        next_site = url
        tweet_collector = []
        while next_site:
            html_data = download_html(next_site, job=None)
            next_site, tweets = parse_html(html_data)
            tweet_collector.extend(tweets)
        return tweet_collector

    # ATM we dont need this def, since __init__ has optional arguments
    @classmethod
    def extract(cls, tweet_url: str, search_pattern: str, job: Dict = None) \
            -> None:
        """Takes a url and saves tweets to hard drive with a specific UUID
        The metadata of the tweet is saved in "UUID.meta.json"
        The actual data of the tweet is saved un "UUID.data.jsonl.gz" """

        next_site = tweet_url
        tweet_collector = []
        while next_site:
            html_data = download_html(next_site, job)
            next_site, tweets = parse_html(html_data)
            tweet_collector.extend(tweets)
        # Got an error, if we used data in the current folder
        # "example.jsonl.gz" and not "data/example.jsonl.gz"

        # This one is great.. do not delete it again, without reason :P
        # Not a fan of the "out/" twice down below.
        os.makedirs(os.path.dirname("out/"), exist_ok=True)

        # Generating an (hopefully ;) ) unique UUID filepath
        temp = str(uuid.uuid4())
        with open(f"out/{temp}.meta.json", "wt") as idMeta:

            save_to = f"out/{temp}.data.jsonl.gz"

            job["creation_time"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
            if tweet_collector:
                job["crawl_complete"] = True
            else:
                job["crawl_complete"] = False
            job["error"] = "[]"

            idMeta.write(json.dumps(job, indent=2))
            idMeta.write("\n")

        with gzip.open(save_to, "wt") as filepath:
            for tweet in tweet_collector:
                filepath.write(tweet.to_json())
                filepath.write("\n")
            if job:
                print(f"Saved the search for '{job['keyword']}' from "
                      f"{job['date']}")

    # ATM we dont need this def, since __init__ has optional arguments
    @classmethod
    def build_from_html(cls, html_data: str, save_to: str = None) \
            -> List["Tweet"]:
        """
        Returns tweets and saves them if you pass a filepath.
        :param html_data: html data, given as str
        :param save_to: (optional) If given saves to the datapath
        :return: List of Tweets
        """
        _, tweets = parse_html(html_data)
        if save_to:
            with gzip.open(save_to, "wt") as filepath:
                for tweet in tweets:
                    filepath.write(tweet.to_json())
                    filepath.write("\n")
        return tweets

    @classmethod
    def build_from_line(cls, line: str or Dict) -> "Tweet":
        if isinstance(line, str):
            line = json.loads(line)
        created_at = line["created_at"]
        id_str = line["id_str"]
        full_text = line["full_text"]
        name = line["user"]["name"]
        screen_name = line["user"]["screen_name"]
        hashtags = []
        user_mentions = []
        urls = []
        for hashtag in line["entities"]["hashtags"]:
            hashtags.append(Hashtag(hashtag["text"], hashtag["indices"]))
        for user_mention in line["entities"]["user_mentions"]:
            user_mentions.append(
                UserMention(user_mention["screen_name"], user_mention["id_str"],
                            user_mention["indices"]))
        for url in line["entities"]["urls"]:
            urls.append(TweetURLMapping(url["url"], url["expanded_url"],
                                        url["display_url"],
                                        url["indices"]))
        try:
            evaluation = line["evaluation"]
        except KeyError:
            return cls(created_at, id_str, full_text, name, screen_name,
                       hashtags, user_mentions, urls)
        else:
            return cls(created_at, id_str, full_text, name, screen_name,
                       hashtags, user_mentions, urls, evaluation)

    def __str__(self) -> str:
        string = f"created_at: {self.created_at}\n" \
                 f"id_str: {self.id_str}\n" \
                 f"full_text: {self.full_text}\n" \
                 f"user: {self.name}, {self.screen_name}\n" \
                 f"hashtags {to_dict_list(self.hashtags)}\n" \
                 f"user_mentions: {to_dict_list(self.user_mentions)}\n" \
                 f"urls: {to_dict_list(self.urls)}\n"
        if self.evaluation:
            string += f"evaluation: {self.evaluation}"
        return string

    def to_json(self) -> Dict:
        """Return a json serializable dict of this tweet"""
        user = {"name": self.name, "screen_name": self.screen_name}
        entities = {"hashtags": to_dict_list(self.hashtags),
                    "user_mentions": to_dict_list(self.user_mentions),
                    "urls": to_dict_list(self.urls)}
        json_dict = dict()
        json_dict["created_at"] = self.created_at
        json_dict["id_str"] = self.id_str
        json_dict["full_text"] = self.full_text
        json_dict["entities"] = entities
        json_dict["user"] = user
        if self.evaluation:
            json_dict["evaluation"] = self.evaluation
        return json.dumps(json_dict)


def build_from_json(read_from: str or Path) -> List[Tweet]:
    """Return a list of tweets from a json.gz file. API or HTML saved data"""
    with gzip.open(read_from, "rt") as json_file:
        tweets = []
        for line in json_file:
            tweets.append(Tweet.build_from_line(line))
        return tweets


def to_dict_list(entities: List) -> List[Dict]:
    """Collects every entity of one type and form a list of dicts. Manly for
    toString cases."""
    temp = []
    for entity in entities:
        temp.append(entity.__dict__)
    return temp


def only_whitespaces(text):
    """This methods scans for text that only contains whitespaces."""
    for character in text:
        if character != " ":
            return False
    return True


def download_html(tweet_url: str, job: Dict = None) -> str:
    """
    Downloads the site of a given URL with an older User-Agent.

    :param tweet_url: The URL as str you want to get downloaded
    :param job: (optional) If Job is given and it fails, it will save the fail
        data
    :return:
    """
    print(tweet_url)
    # Needed to change. The old didn't return tweets. So try this if you the
    # parser does not have tweets in it's tweets list, while you see them on the
    # website
    # headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.00; '
    #                          'Windows 98)'}
    # headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; '
    #                          'Windows NT 5.1)'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; it-IT; '
                             'rv:1.8.1.7) Gecko/20070914 Firefox/2.0.0.7'}
    tries = 0
    max_retries = 5

    while tries < max_retries:
        try:
            req = requests.get(tweet_url, headers=headers, timeout=5)
        except requests.exceptions.ConnectionError:
            tries += 1
            sleep(5)
            if tries == max_retries and job is not None:
                failed_jobs_collector(
                    job, reason="requests.exceptions.ConnectionError")
        except requests.exceptions.Timeout:
            tries += 1
            sleep(5)
            if tries == max_retries and job is not None:
                failed_jobs_collector(job, reason="requests.exceptions.Timeout")
        else:
            if req.status_code == 404:
                warnings.warn(
                    "The url did not resolve to a valid site. Error 404")
            elif req.status_code == 200:
                return req.text


def create_time(tweet_id: str) -> str:
    tweet_id = int(tweet_id)
    time = (tweet_id >> 22) + 1288834974657
    time = datetime.datetime.utcfromtimestamp(time / 1000) \
        .strftime("%a %b %d %H:%M:%S +0000 %Y")
    return time


def parse_html(html_data: str) -> Tuple[str, List[Tweet]]:
    """
    This method parses the html data.
    It filters for the old/mobile twitter site and collects the following
    entries:
    - date
    - id
    - text
    - author and his @tag
    - UserMentions, Hashtags and URLs/Media
    :param html_data: html data, given as str
    :return: The url of the next site and a list of tweets from this site
    """

    from nasty.string_modification import get_indices, html_to_api_converter

    # If download_html fails, e.g. due to connection lost,
    # BeautifulSoup raises a error for None as data
    if not html_data:
        warnings.warn("Empty or None html data in parse_html")
        return "", []
    # BeautifulSoup parser our html data. The chosen parser is "html5lib"
    # since otherwise you get fails at: &#10;&#10; => \n instead of => \n\n
    soup = BeautifulSoup(html_data, features="html5lib")
    tweet_list = soup.find_all("table", class_="tweet")

    tweets = []
    # This block parses the name, screen_name (@x), created_at, text and id from
    # a normal tweet.
    # e.g. one of the replies
    # for includes if len(tweet_list) == 0, thanks to range()
    for raw_tweet in tweet_list:
        if raw_tweet.find("td", class_="tombstone-tweet-text") is None:

            # HTML collected and tested at: 2019-07-09
            # <a href="/MoshTimes?p=s">
            #   <strong class="fullname">
            #       Moshville Times
            #   </strong>
            # <div class="username"><span>@</span>MoshTimes</div></a>
            name = raw_tweet.find("strong", class_="fullname") \
                .contents[0].string
            # .find().content => ['\n      ', <span>@</span>, 'oste8minutes\n    ']
            screen_name = raw_tweet.find("div", class_="username") \
                              .contents[2].string[:-5]

            # HTML collected and tested at: 2019-07-09
            # <td class="timestamp">
            #   <a name="tweet_1142868564866719744"
            #   href="/MoshTimes/status/1142868564866719744?p=p">
            #       23. Juni
            #   </a>
            # </td>

            # the time can be calculated with tweet_id, using that instead
            # created_at = raw_tweet.find("td", class_="timestamp") \
            #     .contents[1].string

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

            created_at = create_time(id_str)
            # More examples for the entities are in github
            # => 09-ClassesRewrite-Parallelism in "Tweet Entities.html"
            entities_wrapper = raw_tweet_text.find("div", class_="dir-ltr")

            # HTML collected and tested at: 2019-07-09
            # <a href="/hashtag/Testtweet?src=hash"
            # data-query-source="hashtag_click"
            # class="twitter-hashtag dir-ltr"dir="ltr">
            # #Testtweet
            # </a>
            hashtags_list = entities_wrapper.find_all(
                "a", class_="twitter-hashtag dir-ltr")
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
            urls_list = entities_wrapper.find_all(
                "a", class_="twitter_external_link dir-ltr tco-link")

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

            # Since we don't differentiate between links and uploaded media, we
            # just add the media
            urls_list += entities_wrapper \
                .find_all("a", class_="twitter_external_link dir-ltr tco-link "
                                      "has-expanded-path")
            urls = []
            for url in urls_list:
                urls.append(TweetURLMapping(url.get("href"),
                                            url.get("data-url"),
                                            url.text, (0, 0)))

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
            reply_names = raw_tweet.find("div",
                                         class_="tweet-reply-context username")
            user_mentions = []
            if reply_names is not None:
                reply_names = reply_names.find_all("a")
                for reply in reply_names:
                    if not only_whitespaces(reply.text[1:]):
                        user_mentions.append(
                            UserMention(reply.text[1:], "", (0, 0)))

            # HTML collected and tested at: 2019-07-09
            # <a href="/OHiwi2"
            # class="twitter-atreply dir-ltr"
            # dir="ltr"
            # data-mentioned-user-id="1117712996795658241"
            # data-screenname="OHiwi2">
            #   @OHiwi2
            # </a>
            user_mentions_list = entities_wrapper.find_all(
                "a", class_="twitter-atreply dir-ltr")
            for user in user_mentions_list:
                user_mentions.append(
                    UserMention(user.text[1:],
                                user.get("data-mentioned-user-id"), (0, 0)))

            # Modify string, get right indices for urls and user_mentions
            full_text, urls, user_mentions = html_to_api_converter(
                full_text, urls, user_mentions, screen_name)
            # Now also get indices of hashtags
            for hashtag in hashtags:
                start, end = get_indices(hashtag.text, full_text)
                hashtag.indices = (start - 1, end)
            user_mentions.reverse()
            # Create the tweet, and modify the full_text so its more like the
            # API
            tweet = Tweet(created_at, id_str, full_text, name, screen_name,
                          hashtags, user_mentions, urls)

            tweets.append(tweet)

    if soup.find("div", class_="w-button-more") is not None:
        next_site_head = "https://mobile.twitter.com"
        print("Next page is on the way.")
        next_site_tail = soup.find("div", class_="w-button-more") \
            .find("a").get("href")
        return next_site_head + next_site_tail, tweets
    return "", tweets


def failed_jobs_collector(job: Dict, reason: str) -> None:
    """Saves a failed job. Used to try it again later and see reason why it
    failed."""
    job["creation_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    job["crawl_complete"] = False
    job["error"] = reason
    with open("failedJobs.jsonl", "a") as failed:
        failed.write(json.dumps(job))
        failed.write("\n")
