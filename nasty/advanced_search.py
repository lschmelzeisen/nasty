import html
from datetime import date, datetime, timedelta
from logging import getLogger
from typing import List, Optional, Tuple
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import nasty
from nasty.tweet import Hashtag, Tweet, TweetUrlMapping, UserMention


# Custom exception for if our current user_agent fails
class UserAgentException(Exception):
    pass


def perform_advanced_search(keyword: str, date: date, lang: str) -> List[Tweet]:
    tweets = []

    next_cursor = None
    while True:
        page = _download_advanced_search_page(
            keyword, date, date + timedelta(days=1), lang, next_cursor)
        tweets_on_page, next_cursor = \
            _extract_tweets_from_advanced_search_page(page)
        tweets.extend(tweets_on_page)

        if not next_cursor:
            break

    if not tweets:
        logger = getLogger(nasty.__name__)
        logger.debug('Found no tweets for this search. '
                     'Maybe you need to change user agents.')

    return tweets


def _download_advanced_search_page(keyword: str,
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
    with requests.Session() as session:
        session.mount('https://', HTTPAdapter(max_retries=Retry(
            total=5, connect=5, redirect=10, backoff_factor=0.1,
            raise_on_redirect=True, raise_on_status=True,
            status_forcelist=[404, 408, 409, 500, 501, 502, 503, 504])))

        # We mask ourselves behind an ancient User-Agent string here in order to
        # avoid Twitter responding with its modern website version which
        # requires running Javascript to load the actual content. The older
        # version we get with the following contains all content in HTML and is
        # thus easier crawled. However, this breaks from time to time and the
        # user-agent string might need to be updated.
        # user_agent = 'Mozilla/4.0 (compatible; MSIE 5.00; Windows 98)'
        # user_agent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
        user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; it-IT; ' \
                     'rv:1.8.1.7) Gecko/20070914 Firefox/2.0.0.7'

        # The following line throws an exception in case of connection problems,
        # or timeouts.
        request = session.get(
            url, headers={'User-Agent': user_agent}, timeout=5)
        if request.status_code != 200:
            raise ValueError('Unexpected status code: {}.'
                             .format(request.status_code))

    return request.text


def _extract_tweets_from_advanced_search_page(page: str) \
        -> Tuple[List[Tweet], Optional[str]]:
    """Takes a downloaded advanced search page and extracts
        all contained Tweets.

    :param page: The advanced search page to extract Tweets from. This needs to
        be an HTML document of the search results page of the old version of
        Twitter.
    :return: Tuple of extracted tweets and next_cursor. next_cursor is
        the parameter to pass to download_download_advanced_search_page() to
        download the next page or None if no next page exists.
    """

    # We use the "html5lib" parser here, since other parsers fail to preserve
    # whitespace exactly. For example, only html5lib parses "&#10;&#10;" to the
    # correct "\n\n", other just to "\n".
    soup = BeautifulSoup(page, features='html5lib')

    tweet_tables = soup.find_all('table', class_='tweet')
    tweets = [_extract_tweet_from_tweet_table(t)
              for t in tweet_tables
              # TODO: can we document why the following line is needed?
              # This line was needed for the search of random individual tweets
              # It saved the case a deleted tweet was found
              if not t.find('td', class_='tombstone-tweet-text')]

    next_cursor = None
    more_button = soup.find('div', class_='w-button-more')
    if more_button:
        next_page_url = more_button.find('a').get('href')
        next_cursor = next_page_url[next_page_url.find('next_cursor=')
                                    + len('next_cursor='):]

        # If there is a more_button, we should not see "noresults"
        # if we see "noresults" it indicates that our user-agent get's blocked
        no_result = soup.find('div', class_='noresults')
        if no_result:
            raise UserAgentException

    return tweets, next_cursor


def _extract_tweet_from_tweet_table(tweet_table: Tag) -> Tweet:
    """Extracts a Tweet from its HTML table representation.

    Currently, extracts the following attributes:
    - date
    - id
    - text
    - author and his @tag
    - UserMentions, Hashtags and URLs/Media
    """

    id_str, created_at = _extract_tweet_meta_from_tweet_table(tweet_table)
    name, screen_name = \
        _extract_author_information_from_tweet_table(tweet_table)
    hashtags = _extract_hashtags_from_tweet_table(tweet_table)
    url_mappings = _extract_url_mappings_from_tweet_table(tweet_table)
    user_mentions = _extract_user_mentions_from_tweet_table(tweet_table)
    full_text = _extract_text_from_tweet_table(
        tweet_table, screen_name, url_mappings, user_mentions)

    _look_up_and_set_indices(full_text, hashtags, url_mappings, user_mentions)

    return Tweet(created_at, id_str, full_text, name, screen_name, hashtags,
                 user_mentions, url_mappings)


def _extract_tweet_meta_from_tweet_table(tweet_table: Tag) \
        -> Tuple[str, datetime]:
    # HTML collected and tested at: 2019-07-09
    # <td class="timestamp">
    #   <a name="tweet_1142868564866719744"
    #      href="/MoshTimes/status/1142868564866719744?p=p">
    #     23. Juni
    #   </a>
    # </td>

    # the time can be calculated with tweet_id, using that instead
    # created_at = raw_tweet.find("td", class_="timestamp") \
    #     .contents[1].string

    # HTML collected and tested at: 2019-07-09
    # <div class="tweet-text" data-id="1142868564866719744">
    #   <div class="dir-ltr" dir="ltr">
    #     Tweet Text, entities (links, mentions, hashtags)
    #   </div>
    # </div>

    id_str = tweet_table.find('div', class_='tweet-text').get('data-id')
    created_at = Tweet.calc_created_at_time_from_id(id_str)

    return id_str, created_at


def _extract_author_information_from_tweet_table(tweet_table: Tag) \
        -> Tuple[str, str]:
    # HTML collected and tested at: 2019-07-09
    # <a href="/MoshTimes?p=s">
    #   <strong class="fullname">Moshville Times</strong>
    #   <div class="username">
    #     <span>@</span>MoshTimes
    #   </div>
    # </a>

    name = tweet_table.find('strong', class_='fullname').text.strip()
    screen_name = \
        tweet_table.find('div', class_='username').text.strip()[len('@'):]

    return name, screen_name


def _extract_hashtags_from_tweet_table(tweet_table: Tag) -> List[Hashtag]:
    # HTML collected and tested at: 2019-07-09
    # <a href="/hashtag/Testtweet?src=hash"
    #    data-query-source="hashtag_click"
    #    class="twitter-hashtag dir-ltr"
    #    dir="ltr">
    #   #Testtweet
    # </a>

    return [Hashtag(h.text[len('#'):], (0, 0))
            for h in tweet_table.find_all('a', class_='twitter-hashtag')]


def _extract_url_mappings_from_tweet_table(tweet_table: Tag) \
        -> List[TweetUrlMapping]:
    # More examples for the entities are in github
    # => 09-ClassesRewrite-Parallelism in "Tweet Entities.html"

    # HTML collected and tested at: 2019-07-09
    # <a href="https://t.co/I8NMVQeekO"
    #    rel="nofollow noopener"
    #    dir="ltr"
    #    data-expanded-url="https://twitter.com/OHiwi2/status/1146162915491364866"
    #    data-url="https://twitter.com/OHiwi2/status/1146162915491364866"
    #    class="twitter_external_link dir-ltr tco-link"
    #    target="_blank"
    #    title="https://twitter.com/OHiwi2/status/1146162915491364866">
    #   twitter.com/OHiwi2/status/...
    # </a>

    # HTML collected and tested at: 2019-07-09
    # <a href="https://t.co/c076qpkzt2"
    #    data-pre-embedded="true"
    #    rel="nofollow"
    #    data-entity-id="1146165309189087233"
    #    dir="ltr"
    #    data-url="https://twitter.com/OHiwi2/status/1146165689390120960/video/1"
    #    data-tco-id="c076qpkzt2"
    #    class="twitter_external_link dir-ltr tco-link has-expanded-path"
    #    target="_top"
    #    data-expanded-path="/OHiwi2/status/1146165689390120960/video/1">
    #   pic.twitter.com/c076qpkzt2
    # </a>

    return [TweetUrlMapping(u.get('href'), u.get('data-url'), u.text, (0, 0))
            for u in tweet_table.find_all('a', class_='twitter_external_link')]


def _extract_user_mentions_from_tweet_table(tweet_table: Tag) \
        -> List[UserMention]:
    # HTML collected and tested at: 2019-07-09
    # <span class="tweet-reply-context username">
    #   Reply to
    #   <a href="/TJCobain">@TJCobain</a>
    #   <a href="/TJ_Cobain">@TJ_Cobain</a>
    #   and
    #   <a href="/angelgab0525/status/1142583459698761728/reply">
    #     5 others
    #   </a>
    # </span>

    # HTML collected and tested at: 2019-07-09
    # <a href="/OHiwi2"
    #    class="twitter-atreply dir-ltr"
    #    dir="ltr"
    #    data-mentioned-user-id="1117712996795658241"
    #    data-screenname="OHiwi2">
    #   @OHiwi2
    # </a>

    user_mentions = []

    reply_names = tweet_table.find('div',
                                   class_='tweet-reply-context username')
    if reply_names is not None:
        for reply in reply_names.find_all('a'):
            if reply.text.startswith('@'):
                user_mentions.append(UserMention(
                    reply.text[len('@'):], '', (0, 0)))

    # Reverse mentions collected until here to match order in Twitter API when
    # we prepend them to the full text.
    user_mentions.reverse()

    user_mentions.extend(
        UserMention(u.text[len('@'):], u.get('data-mentioned-user-id'), (0, 0))
        for u in tweet_table.find_all('a', class_='twitter-atreply'))

    return user_mentions


def _extract_text_from_tweet_table(tweet_table: Tag,
                                   screen_name: str,
                                   url_mappings: List[TweetUrlMapping],
                                   user_mentions: List[UserMention]) -> str:
    full_text = tweet_table.find('div', class_='dir-ltr').text.strip()

    for url in url_mappings:
        full_text = full_text.replace(url.display_url, url.url, 1)

    prepended_user_mentions = ''.join(
        '@' + user_mention.screen_name + ' '
        for user_mention in reversed(user_mentions)
        if (user_mention.screen_name != screen_name
            and not user_mention.id
            and ('@' + user_mention.screen_name) not in full_text))

    full_text = _twitter_api_unescape(prepended_user_mentions + full_text)

    return full_text


def _twitter_api_unescape(text: str) -> str:
    """
    This method unescapes html codes of a given string. But adds &lt;, &gt; and
    &amp; , due to match the output of the API & needs to be escaped first,
    since the others contain &.
    """
    text = html.unescape(text)
    text = text.replace('＠', '@')
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _look_up_and_set_indices(full_text: str,
                             hashtags: List[Hashtag],
                             url_mappings: List[TweetUrlMapping],
                             user_mentions: List[UserMention]) -> None:
    for hashtag in hashtags:
        hashtag.indices = _indices('#' + hashtag.text, full_text)
    for url in url_mappings:
        url.indices = _indices(url.url, full_text)
    for user_mention in user_mentions:
        if user_mention.id:
            user_mention.indices = _indices("@" + user_mention.screen_name,
                                            full_text)


def _indices(needle: str, haystack: str) -> Tuple[int, int]:
    try:
        start = haystack.index(needle)
    except ValueError as exc:
        print(exc.__traceback__)
        start = -1
    return start, start + len(needle)
