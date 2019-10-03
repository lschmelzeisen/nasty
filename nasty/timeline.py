import re
from http import HTTPStatus
from logging import getLogger
from typing import Dict, Iterable, Optional

import requests
import requests.cookies
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from nasty.errors import UnexpectedStatusCodeException
from nasty.tweet import Tweet


# TODO: abstract base class

class Timeline:
    """Crawls all Tweets belonging to a specific Twitter timeline view.

    Implemented via Twitter's mobile web interface. For this we emulate what a
    normal browser would do:
    1) Load the HTML stub belonging to a timeline page. We say stub here,
       because the HTML doesn't contained any contents, i.e., there are no
       Tweets in it.
    2) Load batches of displayed Tweets via AJAX requests on page load and
       whenever the user scrolls to the bottom of the page.
    The upside of this approach is that the JSON results have the exact same
    format as the results from the Twitter developer API (and even contain
    more information).
    """

    DEFAULT_BATCH_SIZE = 20

    def __init__(self,
                 max_tweets: Optional[int] = None,
                 batch_size: int = DEFAULT_BATCH_SIZE):
        self.max_tweets = max_tweets
        self.batch_size = batch_size

    def _timeline_url(self) -> Dict:
        raise NotImplementedError()

    def _batch_url(self, cursor: Optional[str] = None) -> Dict:
        raise NotImplementedError()

    def __iter__(self) -> Iterable[Tweet]:
        if self.max_tweets is not None and self.max_tweets <= 0:
            return []

        with requests.Session() as session:
            # Configure on which status codes we should perform automated
            # retries.
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
            self._establish_twitter_session(session)

            consecutive_rate_limits = 0
            consecutive_empty_results = 0
            num_yielded_tweets = 0
            cursor = None
            while not (self.max_tweets
                       and num_yielded_tweets == self.max_tweets):
                # Load the next result batch. If we run into rate limit errors,
                # establish a new session. Only stop when this fails multiple
                # times in a row.
                try:
                    batch = self._fetch_batch(session, cursor=cursor)
                except UnexpectedStatusCodeException as e:
                    if (e.status_code
                            == HTTPStatus.TOO_MANY_REQUESTS):  # HTTP 429
                        consecutive_rate_limits += 1
                        if consecutive_rate_limits != 3:
                            self._establish_twitter_session(session)
                            continue
                    raise
                consecutive_rate_limits = 0

                # Stop the iteration once the returned batch no longer contains
                # any Tweets. Ideally, we would like to omit this last request
                # but there seems to be no way to detect this prior to having
                # the last batch loaded. Additionally, Twitter will sometimes
                # stop sending results early, which we also can not detect.
                # Because of this, we only stop loading once we receive empty
                # batches multiple times in a row.
                if not self._num_tweets_in_batch(batch):
                    consecutive_empty_results += 1
                    if consecutive_empty_results == 3:
                        break
                    continue
                consecutive_empty_results = 0

                for tweet in self._tweets_in_batch(batch):
                    yield Tweet(tweet)

                    num_yielded_tweets += 1
                    if (self.max_tweets
                            and num_yielded_tweets == self.max_tweets):
                        break

                cursor = self._next_cursor_from_batch(batch)

    def _establish_twitter_session(self, session: requests.Session) -> None:
        """Establishes a session with Twitter, so that they answer our requests.

        If we try to directly access request the first batch of a query, Twitter
        will respond with a rate limit error, i.e. HTTP 429. To receive actual
        responses we need to include a bearer token and a guest token in our
        headers. A normal web browser gets these be first loading the displaying
        HTML stub. This function emulates this process and prepares the given
        session object to contain the necessary headers.

        For more information on this process, see:
        - https://tech.b48.club/2019/05/13/how-to-fake-a-source-of-a-tweet.html
        - https://steemit.com/technology/@singhpratyush/fetching-url-for-complete-twitter-videos-using-guest-user-access-pattern
        - https://github.com/ytdl-org/youtube-dl/issues/12726#issuecomment-304779835

        Each established session is only good for a given number of requests.
        Information on this can be obtained by checking the X-Rate-Limit-*
        headers in the responses from api.twitter.com. Currently, we do not pay
        attention to these, and just establish a new session once we run into
        the first rate limit error. Cursor parameters, i.e. those that specify
        the current position in the result list seem to persist across sessions.

        Technically, a normal web browser would also receive a few cookies from
        Twitter in this process. Currently, api.twitter.com doesn't seem to
        check for these. In any case, we still set those in case Twitter changes
        their behavior. Note, however, that our requests will still be trivially
        distinguishable from a normal web browsers requests, as they typically
        sent many more headers and cookies, i.e. those from Google Analytics.
        Further we include the string "NASTYbot" in our User-Agent header to
        make it trivial for Twitter to rate-limit us, should they decide to.

        :param session: Session object to modify.
        """

        logger = getLogger(__name__)
        logger.debug('  Establishing new Twitter session.')

        session.headers.clear()
        session.cookies.clear()

        # We use the current Chrome User-Agent string to get the most recent
        # version of the Twitter mobile website.
        session.headers['User-Agent'] = (
            'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)'
            ' AppleWebKit/537.36 (KHTML, like Gecko)'
            ' Chrome/68.0.3440.84 Mobile Safari/537.36'
            ' NASTYbot')

        # The following header shouldn't matter for the actual returned Tweets.
        # Still, since api.twitter.com also returns some localized strings for
        # the UI (e.g. headings), we set this to English, so these strings are
        # always the same. If not set, Twitter will guesstimate the language
        # from the IP.
        session.headers['Accept-Language'] = 'en_US,en'

        # Query HTML stub page. Also automatically adds any returned cookies by
        # Twitter via response headers to the session.
        response = session.get(**self._timeline_url())
        self._verify_and_log_response(response)

        main_js_url = re.findall(
            '(https://abs.twimg.com/responsive-web/web/main.[a-z0-9]+.js)',
            response.text)[0]
        guest_token = re.findall(
            'document\\.cookie = decodeURIComponent\\(\\"gt=([0-9]+);',
            response.text)[0]

        # Queries the JS-script that carries the bearer token. Currently, this
        # does not seem to constant for all users, but we still check in case
        # this changes in the future.
        response = session.get(main_js_url)
        self._verify_and_log_response(response)

        bearer_token = re.findall('s="Web-12",u="([^"]+)"', response.text)[0]

        # Emulate cookie setting that would be performed via Javascript.
        session.cookies.set_cookie(requests.cookies.create_cookie(
            'gt', guest_token, domain='.twitter.com', path='/'))

        # Set the two headers that we need to access api.twitter.com.
        session.headers['Authorization'] = 'Bearer {}'.format(bearer_token)
        session.headers['X-Guest-Token'] = guest_token

        logger.debug('    Guest token: {}. Bearer token: {}.'.format(
            guest_token, bearer_token))

    def _fetch_batch(self,
                     session: requests.Session,
                     cursor: Optional[str] = None) -> Dict:
        """Fetches the next batch of Tweets in the timeline.

        :param session: A session established with Twitter.
        :param cursor: ID signaling at which position in the timeline we want
            the results to be. The cursor of the next batch is always contained
            in the current result.
        :return: JSON with instructions in how to change the displayed timeline.
            We care for this because it also contains the matching Tweets in the
            same JSON format as returned by the Twitter developer API.
        """

        logger = getLogger(__name__)
        logger.debug('  Fetching search batch with cursor "{}".'.format(cursor))

        response = session.get(**self._batch_url(cursor))
        self._verify_and_log_response(response)

        batch = response.json()
        logger.debug('    Contained {} Tweets.'.format(
            self._num_tweets_in_batch(batch)))

        return batch

    @classmethod
    def _verify_and_log_response(cls, response: requests.Response):
        logger = getLogger(__name__)
        status = HTTPStatus(response.status_code)
        logger.debug('    Received {} {} for {}'.format(
            status.value, status.name, response.url))

        if response.status_code != 200:
            raise UnexpectedStatusCodeException(
                response.url, HTTPStatus(response.status_code))

    @classmethod
    def _num_tweets_in_batch(cls, batch: Dict) -> int:
        """Determines how many Tweets were contained in a batch.

        This is just an upper bound of actual timeline length, because Tweets
        might contain quoted Tweets which would also add to this."""
        return len(batch['globalObjects']['tweets'])

    @classmethod
    def _tweets_in_batch(cls, batch: Dict) -> Iterable[Dict]:
        # Grab ID to Tweet and ID to user mappings.
        tweets = batch['globalObjects']['tweets']
        users = batch['globalObjects']['users']

        # Iterate over the sorted order of tweet IDs.
        for tweet_id in cls._tweet_ids_from_entries(
                cls._entries_in_batch(batch)):
            # Look up tweet.
            tweet = tweets[tweet_id]

            # Lookup user object and set for tweet.
            tweet['user'] = users[tweet['user_id_str']]

            # Delete remaining user fields in order to be similar to the Twitter
            # developer API and because the information is stored in the user
            # object anyways.
            tweet.pop('user_id')
            tweet.pop('user_id_str')

            yield tweet

    @classmethod
    def _entries_in_batch(cls, batch: Dict) -> Iterable[Dict]:
        # Entries are add/replace operations to the timeline (the list of
        # objects visible to the user).
        for instruction in batch['timeline']['instructions']:
            if 'addEntries' in instruction:
                for entry in instruction['addEntries']['entries']:
                    yield entry
            elif 'replaceEntry' in instruction:
                yield instruction['replaceEntry']['entry']

    @classmethod
    def _tweet_ids_from_entries(cls, entries: Iterable[Dict]) -> Iterable[str]:
        for entry in sorted(
                entries, reverse=True, key=lambda entry: entry['sortIndex']):
            # The following determines whether the entry is a Tweet. Alternative
            # would include ads and persons relevant to the search query.
            if 'item' in entry['content']:
                yield entry['content']['item']['content']['tweet']['id']

    @classmethod
    def _next_cursor_from_batch(cls, batch: Dict) -> str:
        for entry in cls._entries_in_batch(batch):
            if entry['entryId'] == 'sq-cursor-bottom':
                return entry['content']['operation']['cursor']['value']
        raise ValueError('No next cursor value in batch.')
