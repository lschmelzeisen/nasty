import datetime
import warnings
from datetime import date, timedelta
from logging import getLogger
from typing import List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import nasty
from nasty.string_modification import get_indices, html_to_api_converter
from nasty.tweet import Hashtag, Tweet, TweetURLMapping, UserMention


def perform_advanced_search(keyword: str, date: date, lang: str) -> List[Tweet]:
    tweets = []

    next_cursor = None
    while True:
        html_data = download_advanced_search_page(
            keyword, date, date + timedelta(days=1), lang, next_cursor)
        next_page_url, tweets_on_page = parse_html(html_data)
        tweets.extend(tweets_on_page)

        if not next_page_url:
            break
        next_cursor = next_page_url[
                      next_page_url.find('next_cursor=') + len('next_cursor='):]

    return tweets


def download_advanced_search_page(keyword: str,
                                  start_date: date,
                                  end_date: date,
                                  lang: str,
                                  next_cursor: Optional[str] = None) -> str:
    logger = getLogger(nasty.__name__)
    logger.debug('Download advanced search page (keyword: "{}", time-range: '
                 '"{}" to "{}", lang: "{}", next-cursor: "{}").'
                 .format(keyword, start_date.isoformat(), end_date.isoformat(),
                         lang, next_cursor))

    url = 'https://mobile.twitter.com/search?q='
    url += quote_plus('{} since:{} until:{} lang:{}'.format(
        keyword, start_date.isoformat(), end_date.isoformat(), lang))
    if next_cursor:
        url += '&next_cursor=' + next_cursor

    # Configure retry behaviour. See the following for some explanation:
    # https://stackoverflow.com/a/35504626/211404
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(
        total=5, connect=5, redirect=10, backoff_factor=0.1,
        raise_on_redirect=True, raise_on_status=True,
        status_forcelist=[404, 408, 409, 500, 501, 502, 503, 504])))

    # We mask ourselves behind an ancient User-Agent string here in order to
    # avoid Twitter responding with its modern website version which requires
    # running Javascript to load the actual content. The older version we get
    # with the following contains all content in HTML and is thus easier
    # crawled. However, this breaks from time to time and the user-Agent string
    # might need to be updated.
    # user_agent = 'Mozilla/4.0 (compatible; MSIE 5.00; Windows 98)'
    # user_agent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; it-IT; ' \
                 'rv:1.8.1.7) Gecko/20070914 Firefox/2.0.0.7'

    request = session.get(url, headers={'User-Agent': user_agent}, timeout=5)
    if request.status_code != 200:
        raise ValueError('Unexpected status code: {}.'
                         .format(request.status_code))

    return request.text


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

    def only_whitespaces(text):
        """This methods scans for text that only contains whitespaces."""
        for character in text:
            if character != " ":
                return False
        return True

    def create_time(tweet_id: str) -> str:
        tweet_id = int(tweet_id)
        time = (tweet_id >> 22) + 1288834974657
        time = datetime.datetime.utcfromtimestamp(time / 1000) \
            .strftime("%a %b %d %H:%M:%S +0000 %Y")
        return time

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
