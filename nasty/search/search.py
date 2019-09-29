import re
from datetime import date
from http import HTTPStatus
from logging import getLogger
from typing import Dict, Iterable, Optional

import requests.cookies
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import nasty
from nasty.init import init_nasty
from nasty.search.errors import UnexpectedStatusCodeException
from nasty.search.query import Query
from nasty.search.tweet import Tweet


def search(query: Query,
           max_tweets: Optional[int] = 1000,
           page_size: int = 20) -> Iterable[Tweet]:
    """Searches Tweets matching a query.

    The Tweets contained in the result and their sorting is determined by
    Twitter and will likely change when calling this function with the same
    inputs multiple times. Also in some cases, Twitter stops sending results
    early, even though more matching Tweets would exists. However, there is no
    way to detect this.

    Implemented via Twitter's mobile search web interface. For this we emulate
    what a normal browser would do:
    1) Load an HTML stub from https://mobile.twitter.com/search?q=...
    2) Load JSONs of the actual search results via AJAX requests whenever the
       user scrolls to the bottom of the page from
       https://api.twitter.com/2//search/adaptive.json
    The upside of this approach is that the JSON results have the exact same
    format as the results from the Twitter developer API (and even contain more
    information).

    :param query: The query to search for.
    :param max_tweets: Stop the search after this many tweets have been found.
        Set to None in order to receive as many Tweets as possible. Note that
        this can return quite a lot of tweets, especially if using Filter.LATEST
        and no date range.
    :param page_size: The page size in which Tweets should be queride.

        The normal web interface always queries 20 Tweets per page. Twitter
        interprets this parameter more as a guideline and can either return more
        or less then the requested amount. This does not indicate that no more
        matching Tweets exist after this page.

        Note that by setting anything unequal to 20 here, we make ourselves
        easily distinguishable from normal web browser. Additionally, advanced
        queries like using AND or OR seem to no longer work as intended.

        This parameter can be used to speed up the search performance, by
        reducing the HTTP overhead as less requests have to be performed per
        returned Tweet. If you want to do this, we identified 100 to be a good
        value because increasing it further does seem not return more Tweets per
        request.
    :return: Iterable of tweets that match the query.
    """

    logger = getLogger(nasty.__name__)
    logger.debug('Searching tweets matching {}.'.format(query))

    if max_tweets is not None and max_tweets <= 0:
        return []

    with requests.session() as session:
        # Configure on which status codes we should perform automated retries.
        session.mount('https://', HTTPAdapter(max_retries=Retry(
            total=5, connect=5, redirect=10, backoff_factor=0.1,
            raise_on_redirect=True, raise_on_status=True,
            status_forcelist=[HTTPStatus.REQUEST_TIMEOUT,  # HTTP 408
                              HTTPStatus.CONFLICT,  # HTTP 409
                              HTTPStatus.INTERNAL_SERVER_ERROR,  # HTTP 500
                              HTTPStatus.NOT_IMPLEMENTED,  # HTTP 501
                              HTTPStatus.BAD_GATEWAY,  # HTTP 502
                              HTTPStatus.SERVICE_UNAVAILABLE,  # HTTP 503
                              HTTPStatus.GATEWAY_TIMEOUT])))  # HTTP 504

        # Need to establish a session with Twitter, else we would only get
        # rate limit errors for all requests to api.twitter.com.
        _new_twitter_session(session, query)

        consecutive_rate_limits = 0
        consecutive_empty_results = 0
        num_yielded_tweets = 0
        cursor = None
        while not (max_tweets and num_yielded_tweets == max_tweets):
            # Load the next result page. If we run into rate limit errors,
            # establish a new session. Only stop when this fails multiple times
            # in a row.
            try:
                page = _fetch_search_page(
                    session, query, page_size=page_size, cursor=cursor)
            except UnexpectedStatusCodeException as e:
                if e.status_code == HTTPStatus.TOO_MANY_REQUESTS:  # HTTP 429
                    consecutive_rate_limits += 1
                    if consecutive_rate_limits != 3:
                        _new_twitter_session(session, query)
                        continue
                raise
            consecutive_rate_limits = 0

            # Stop the search process once the returned page no longer contains
            # any Tweets. Ideally, we would like to omit this last request but
            # there seems to be no way to detect this prior to querying.
            # Additionally, Twitter will sometimes stop sending results early,
            # which we also can not detect. Because of this, we only stop
            # searching once we receive empty results multiple times in a row.
            if not _num_tweets_in_page(page):
                consecutive_empty_results += 1
                if consecutive_empty_results == 3:
                    break
                continue
            consecutive_empty_results = 0

            for tweet in _tweets_in_page(page):
                yield Tweet(tweet)

                num_yielded_tweets += 1
                if max_tweets and num_yielded_tweets == max_tweets:
                    break

            cursor = _next_cursor_from_page(page)


def _new_twitter_session(session: requests.Session, query: Query) \
        -> None:
    """Establishes a session with Twitter, so that they answer our requests.

    If we try to directly access https://api.twitter.com/2//search/adaptive.json
    Twitter will respond with a rate limit error, i.e. HTTP 429. To send
    successful request we need to include a bearer token and a guest token in
    our headers. A normal web browser gets these be first loading the displaying
    HTML stub. This function emulates this process and prepares the given
    session object to contain the necessary headers.

    For more information on this process, see:
    - https://tech.b48.club/2019/05/13/how-to-fake-a-source-of-a-tweet.html
    - https://steemit.com/technology/@singhpratyush/
      fetching-url-for-complete-twitter-videos-using-guest-user-access-pattern
    - https://github.com/ytdl-org/youtube-dl/issues/12726#issuecomment-304779835

    Each established session is only good for a given number of requests.
    Information on this can be obtained by checking the X-Rate-Limit-* headers
    in the responses from api.twitter.com. Currently, we do not pay attention to
    these, and just establish a new session once we run into the first rate
    limit error. Cursor parameters, i.e. those that specify the current position
    in the result list seem to persist across sessions.

    Technically, a normal web browser would also receive a few cookies from
    Twitter in this process. Currently, api.twitter.com doesn't seem to check
    for these. In any case, we still set those in case Twitter changes their
    behavior. Note, however, that our requests will still be trivially
    distinguishable from a normal web browsers requests, as they typically sent
    many more headers and cookies, i.e. those from Google Analytics.

    :param session: Session object to modify.
    :param query: Query for which to establish the session for.
    """

    logger = getLogger(nasty.__name__)
    logger.debug('  Establishing new Twitter session.')

    session.headers.clear()
    session.cookies.clear()

    # We use the current Chrome User-Agent string to get the most recent version
    # of the Twitter mobile website.
    session.headers['User-Agent'] = (
        'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
        ' AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/68.0.3440.84 Mobile Safari/537.36'
        ' NASTYbot')

    # The following header shouldn't matter for the actual returned Tweets.
    # Still, since api.twitter.com also returns some localized strings for the
    # UI (e.g. headings), we set this to be sure it matches our query language.
    # If not set, Twitter will guesstimate the language from the IP.
    session.headers['Accept-Language'] = '{};q=0.9'.format(query.lang)

    # Query HTML sub page. Also automatically adds any returned cookies by
    # Twitter via response headers to the session.
    response = session.get('https://mobile.twitter.com/search', params={
        'lang': query.lang,
        'q': query.url_param,
        'src': 'typed_query',
        'f': query.filter.url_param,
    })
    _log_reponse(response)
    if response.status_code != 200:
        raise UnexpectedStatusCodeException(response.url,
                                            HTTPStatus(response.status_code))

    main_js_url = re.findall(
        '(https://abs.twimg.com/responsive-web/web/main.[a-z0-9]+.js)',
        response.text)[0]
    guest_token = re.findall(
        'document\\.cookie = decodeURIComponent\\(\\"gt=([0-9]+);',
        response.text)[0]

    # Queries the JS-script that carries the bearer token. Currently, this does
    # not seem to constant for all users, but we still check in case this
    # changes in the future.
    response = session.get(main_js_url)
    _log_reponse(response)
    if response.status_code != 200:
        raise UnexpectedStatusCodeException(response.url,
                                            HTTPStatus(response.status_code))

    bearer_token = re.findall('s="Web-12",u="([^"]+)"', response.text)[0]

    # Emulate cookie setting that would be performed via Javascript.
    session.cookies.set_cookie(requests.cookies.create_cookie(
        'gt', guest_token, domain='.twitter.com', path='/'))

    # Set the two headers that we need to access api.twitter.com.
    session.headers['Authorization'] = 'Bearer {}'.format(bearer_token)
    session.headers['X-Guest-Token'] = guest_token

    logger.debug('    Guest token: {}. Bearer token: {}.'.format(
        guest_token, bearer_token))


def _fetch_search_page(session: requests.Session,
                       query: Query,
                       page_size: int = 100,
                       cursor: Optional[str] = None) -> Dict:
    """Fetches the next page of search results.

    :param session: A session established with Twitter.
    :param query: The query to search for.
    :param page_size: The number of tweets the returned page should contain.
    :param cursor: ID signaling at which point in the search results we want
        the results to be. The cursor of the next page is always contained in
        the current result.
    :return: JSON carrying instructions in how to change the displayed page. We
        care for this because it also contains the matching Tweets in the same
        JSON format as returned by the Twitter developer API.
    """

    logger = getLogger(nasty.__name__)
    logger.debug('  Fetching search page with cursor "{}".'.format(cursor))

    response = session.get(
        'https://api.twitter.com/2/search/adaptive.json', params={
            # Not sure what most of the parameters with fixed values do. We set
            # them so that they are identical to those sent from the normal
            # web interface.
            'include_profile_interstitial_type': '1',
            'include_blocking': '1',
            'include_blocked_by': '1',
            'include_followed_by': '1',
            'include_want_retweets': '1',
            'include_mute_edge': '1',
            'include_can_dm': '1',
            'include_can_media_tag': '1',
            'skip_status': '1',
            'cards_platform': 'Web-12',
            'include_cards': '1',
            'include_composer_source': 'true',
            'include_ext_alt_text': 'true',
            'include_reply_count': '1',
            'tweet_mode': 'extended',
            'include_entities': 'true',
            'include_user_entities': 'true',
            'include_ext_media_color': 'true',
            'include_ext_media_availability': 'true',
            'send_error_codes': 'true',
            'q': query.url_param,
            'count': page_size,
            'result_filter': query.filter.result_filter,
            'tweet_search_mode': query.filter.tweet_search_mode,
            'query_source': 'typed_query',
            'cursor': cursor,
            'pc': '1',
            'spelling_corrections': '1',
            'ext': 'mediaStats,highlightedLabel,cameraMoment',
        })
    _log_reponse(response)
    if response.status_code != 200:
        raise UnexpectedStatusCodeException(response.url,
                                            HTTPStatus(response.status_code))

    page = response.json()
    logger.debug('    Contained {} Tweets.'.format(
        _num_tweets_in_page(page)))

    return page


def _log_reponse(response: requests.Response):
    logger = getLogger(nasty.__name__)
    status = HTTPStatus(response.status_code)
    logger.debug('    Received {} {} for {}'.format(
        status.value, status.name, response.url))


def _num_tweets_in_page(page: Dict) -> int:
    return len(page['globalObjects']['tweets'])


def _tweets_in_page(page: Dict) -> Iterable[Dict]:
    # Grab ID to Tweet and ID to user mappings.
    tweets = page['globalObjects']['tweets']
    users = page['globalObjects']['users']

    # Iterate over the sorted order of tweet IDs.
    for tweet_id in _tweet_ids_from_entries(_entries_in_page(page)):
        # Look up tweet.
        tweet = tweets[tweet_id]

        # Lookup user object and set for tweet.
        tweet['user'] = users[tweet['user_id_str']]

        # Delete remaining user fields in order to be similar to the Twitter
        # developer API and because the information is stored in the user object
        # anyways.
        tweet.pop('user_id')
        tweet.pop('user_id_str')

        yield tweet


def _entries_in_page(page: Dict) -> Iterable[Dict]:
    # Entries are add/replace operations to the timeline (the list of objects
    # visible to the user).
    for instruction in page['timeline']['instructions']:
        if 'addEntries' in instruction:
            for entry in instruction['addEntries']['entries']:
                yield entry
        elif 'replaceEntry' in instruction:
            yield instruction['replaceEntry']['entry']


def _tweet_ids_from_entries(entries: Iterable[Dict]) -> Iterable[str]:
    for entry in sorted(
            entries, reverse=True, key=lambda entry: entry['sortIndex']):
        # The following determines whether the entry is a Tweet. Alternative
        # would include ads and persons relevant to the search query.
        if 'item' in entry['content']:
            yield entry['content']['item']['content']['tweet']['id']


def _next_cursor_from_page(page: Dict) -> str:
    for entry in _entries_in_page(page):
        if entry['entryId'] == 'sq-cursor-bottom':
            return entry['content']['operation']['cursor']['value']
    raise ValueError('No next cursor value in page.')


if __name__ == '__main__':
    init_nasty()
    logger = getLogger(nasty.__name__)

    query = Query('trump', since=date(2019, 6, 23), until=date(2019, 6, 24))
    for tweet in search(query, max_tweets=1000):
        logger.info(tweet)
