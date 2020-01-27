#
# Copyright 2019-2020 Lukas Schmelzeisen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import re
from abc import ABC, abstractmethod
from http import HTTPStatus
from logging import getLogger
from os import getenv
from time import sleep
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

import requests
from overrides import overrides
from requests.adapters import HTTPAdapter
from typing_extensions import Final, final
from urllib3 import Retry

from .._util.errors import UnexpectedStatusCodeException
from .._util.typing_ import checked_cast
from ..request.request import Request
from ..tweet.tweet import Tweet, TweetId, UserId
from ..tweet.tweet_stream import TweetStream

logger = getLogger(__name__)

crawl_delay: Optional[float] = None


class RetrieverTweetStream(TweetStream):
    def __init__(self, update_callback: Callable[[], bool]):
        self._update_callback: Final = update_callback
        self._tweets: Sequence[Tweet] = []
        self._tweets_position = 0

    def update_tweets(self, tweets: Sequence[Tweet]) -> None:
        self._tweets = tweets
        self._tweets_position = 0

    @overrides
    def __next__(self) -> Tweet:
        if self._tweets_position == len(self._tweets):
            if not self._update_callback():
                raise StopIteration()

        self._tweets_position += 1
        return self._tweets[self._tweets_position - 1]


class RetrieverBatch(ABC):
    def __init__(self, json: Mapping[str, Mapping[str, object]]):
        self._json: Final = json
        self.tweets: Final = self._tweets()
        self.next_cursor: Final = self._next_cursor()

    @final
    def _tweets(self) -> Sequence[Tweet]:
        id_to_tweet_json: Final = cast(
            Mapping[TweetId, Mapping[str, object]],
            self._json["globalObjects"]["tweets"],
        )
        id_to_user_json: Final = cast(
            Mapping[UserId, object], self._json["globalObjects"]["users"]
        )

        result = []
        for tweet_id in self._tweet_ids():
            if tweet_id not in id_to_tweet_json:
                # For conversation it can sometimes happen that a Tweet-ID is returned
                # without accompanying meta information. I have no idea why this happens
                # or how to fix it.
                logger.warning(
                    "Found Tweet-ID {} in timeline, but did not receive "
                    "Tweet meta information.".format(tweet_id)
                )
                # TODO: move this to a ConversationRetrieverBatch
                # TODO: add way to expose this over api
                continue

            tweet_json = dict(id_to_tweet_json[tweet_id])
            tweet_json["user"] = id_to_user_json[
                checked_cast(UserId, tweet_json["user_id_str"])
            ]

            # Delete remaining user fields in order to be similar to the Twitter
            # developer API and because the information is stored in the user object
            # anyways.
            tweet_json.pop("user_id", None)  # present on Search, not on Conversation
            tweet_json.pop("user_id_str")

            result.append(Tweet(tweet_json))
        return result

    @abstractmethod
    def _tweet_ids(self) -> Iterable[TweetId]:
        raise NotImplementedError()

    @abstractmethod
    def _next_cursor(self) -> Optional[str]:
        raise NotImplementedError()


_T_Request = TypeVar("_T_Request", bound=Request)


class Retriever(Generic[_T_Request], ABC):
    """Retrieves Tweets belonging to a specific Twitter timeline view.

    Implemented via Twitter's mobile web interface. For this we emulate what a normal
    browser would do:
    1) Load the HTML stub belonging to a timeline page. We say stub here, because the
       HTML doesn't contained any contents, i.e., there are no Tweets in it.
    2) Load batches of displayed Tweets via AJAX requests on page load and whenever the
       user scrolls to the bottom of the page.
    The upside of this approach is that the JSON results have the exact same format as
    the results from the Twitter developer API (and even contain more information).
    """

    def __init__(self, request: _T_Request):
        self._tweet_stream: Final = self._tweet_stream_type()(self._update_tweet_stream)
        self._request: Final = request
        self._session: Final = requests.Session()
        self._request_finished = False
        self._retrieved_tweets = 0
        self._cursor: Optional[str] = None

        # Configure on which status codes we should perform automated retries.
        self._session.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=5,
                    connect=5,
                    redirect=10,
                    backoff_factor=0.1,
                    raise_on_redirect=True,
                    raise_on_status=True,
                    status_forcelist=[
                        HTTPStatus.REQUEST_TIMEOUT,  # HTTP 408
                        HTTPStatus.CONFLICT,  # HTTP 409
                        HTTPStatus.INTERNAL_SERVER_ERROR,  # HTTP 500
                        HTTPStatus.NOT_IMPLEMENTED,  # HTTP 501
                        HTTPStatus.BAD_GATEWAY,  # HTTP 502
                        HTTPStatus.SERVICE_UNAVAILABLE,  # HTTP 503
                        HTTPStatus.GATEWAY_TIMEOUT,  # HTTP 504
                    ],
                )
            ),
        )

        self._fetch_new_twitter_session()

    @classmethod
    def _tweet_stream_type(cls) -> Type[RetrieverTweetStream]:
        return RetrieverTweetStream

    @classmethod
    @abstractmethod
    def _retriever_batch_type(cls) -> Type[RetrieverBatch]:
        raise NotImplementedError()

    @property
    def tweet_stream(self) -> RetrieverTweetStream:
        return self._tweet_stream

    @abstractmethod
    def _timeline_url(self) -> Mapping[str, object]:
        raise NotImplementedError()

    @abstractmethod
    def _batch_url(self) -> Mapping[str, object]:
        raise NotImplementedError()

    def _update_tweet_stream(self) -> bool:  # noqa: C901
        # TODO: try to reduce complexity and get red of noqa

        if self._request_finished:
            return False

        consecutive_rate_limits = 0
        consecutive_forbidden = 0
        consecutive_empty_batches = 0
        batch = None
        while True:
            try:
                batch = self._fetch_batch()
            except UnexpectedStatusCodeException as e:
                if e.status_code == HTTPStatus.TOO_MANY_REQUESTS:  # HTTP 429
                    consecutive_rate_limits += 1
                    if consecutive_rate_limits != 3:
                        self._fetch_new_twitter_session()
                        continue
                    logger.info("Received 3 consecutive TOO MANY REQUESTS responses.")
                elif e.status_code == HTTPStatus.FORBIDDEN:  # HTTP 403
                    consecutive_forbidden += 1
                    if consecutive_forbidden != 3:
                        self._fetch_new_twitter_session()
                        continue
                    logger.info("Received 3 consecutive FORBIDDEN responses.")
                raise
            consecutive_rate_limits = 0

            # Stop the iteration once the returned batch no longer contains any Tweets.
            # Ideally, we would like to omit this last request but there seems to be no
            # way to detect this prior to having the last batch loaded. Additionally,
            # Twitter will sometimes stop sending results early, which we also can not
            # detect. Because of this, we only stop loading once we receive empty
            # batches multiple times in a row.
            if not batch.tweets:
                consecutive_empty_batches += 1
                if consecutive_empty_batches != 3:
                    continue
                logger.info("Received 3 consecutive empty batches.")
                return False

            break

        tweets = batch.tweets
        if self._request.max_tweets:
            tweets = tweets[: self._request.max_tweets - self._retrieved_tweets]
        self._retrieved_tweets += len(tweets)
        if (
            self._request.max_tweets
            and self._request.max_tweets == self._retrieved_tweets
        ):
            self._request_finished = True
        self.tweet_stream.update_tweets(tweets)

        self._cursor = batch.next_cursor
        if self._cursor is None:
            self._request_finished = True
        return True

    @final
    def _fetch_new_twitter_session(self) -> None:
        """Establishes a session with Twitter, so that they answer our requests.

        If we try to directly access request the first batch of a query, Twitter will
        respond with a rate limit error, i.e. HTTP 429. To receive actual responses we
        need to include a bearer token and a guest token in our headers. A normal web
        browser gets these be first loading the displaying HTML stub. This function
        emulates this process and prepares the given session object to contain the
        necessary headers.

        For more information on this process, see:
        - https://tech.b48.club/2019/05/13/how-to-fake-a-source-of-a-tweet.html
        - https://steemit.com/technology/@singhpratyush/
          fetching-url-for-complete-twitter-videos-using-guest-user-access-pattern
        - https://github.com/ytdl-org/youtube-dl/issues/12726#issuecomment-304779835

        Each established session is only good for a given number of requests.
        Information on this can be obtained by checking the X-Rate-Limit-* headers in
        the responses from api.twitter.com. Currently, we do not pay attention to these,
        and just establish a new session once we run into the first rate limit error.
        Cursor parameters, i.e. those that specify the current position in the result
        list seem to persist across sessions.

        Technically, a normal web browser would also receive a few cookies from Twitter
        in this process. Currently, api.twitter.com doesn't seem to check for these. In
        any case, we still set those in case Twitter changes their behavior. Note,
        however, that our requests will still be trivially distinguishable from a
        normal web browsers requests, as they typically sent many more headers and
        cookies, i.e. those from Google Analytics. Further we include the string
        "NASTYbot" in our User-Agent header to make it trivial for Twitter to
        rate-limit us, should they decide to.
        """

        logger.debug("  Establishing new Twitter session.")

        self._session.headers.clear()
        self._session.cookies.clear()

        # We use the current Chrome User-Agent string to get the most recent version of
        # the Twitter mobile website.
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/68.0.3440.84 Mobile Safari/537.36"
            " NASTYbot"
        )

        # The following header should not matter for the actual returned Tweets. Still,
        # since api.twitter.com also returns some localized strings for the UI (e.g.
        # headings), we set this to English, so these strings are always the same. If
        # not set, Twitter will guesstimate the language from the IP.
        self._session.headers["Accept-Language"] = "en_US,en"

        # Query HTML stub page. Also automatically adds any returned cookies by Twitter
        # via response headers to the session.
        response = self._session_get(**self._timeline_url())
        main_js_url = re.findall(
            "(https://abs.twimg.com/responsive-web/web/main.[a-z0-9]+.js)",
            response.text,
        )[0]
        guest_token = re.findall(
            'document\\.cookie = decodeURIComponent\\(\\"gt=([0-9]+);', response.text
        )[0]

        # Queries the JS-script that carries the bearer token. Currently, this does not
        # seem to constant for all users, but we still check in case this changes in the
        # future.
        response = self._session_get(main_js_url)
        bearer_token = re.findall('.="Web-12",.="([^"]+)"', response.text)[0]

        # Emulate cookie setting that would be performed via Javascript.
        self._session.cookies.set_cookie(  # type: ignore
            requests.cookies.create_cookie(
                "gt", guest_token, domain=".twitter.com", path="/"
            )
        )

        # Set the two headers that we need to access api.twitter.com.
        self._session.headers["Authorization"] = "Bearer {}".format(bearer_token)
        self._session.headers["X-Guest-Token"] = guest_token

        logger.debug(
            "    Guest token: {}. Bearer token: {}.".format(guest_token, bearer_token)
        )

    @final
    def _fetch_batch(self) -> RetrieverBatch:
        return self._retriever_batch_type()(
            self._session_get(**self._batch_url()).json()
        )

    @final
    def _session_get(self, url: str, **kwargs: Any) -> requests.Response:
        if not getenv("NASTY_DISRESPECT_ROBOTSTXT"):
            global crawl_delay
            if crawl_delay is None:
                response = self._session.get("https://mobile.twitter.com/robots.txt")

                for line in response.text.splitlines():
                    if line.lower().startswith("crawl-delay:"):
                        crawl_delay = float(line[len("crawl-delay:") :])
                        break
                else:
                    raise RuntimeError("Could not determine crawl-delay.")

                logger.debug(
                    "    Determined crawl-delay of {:.2f}s.".format(crawl_delay)
                )

            sleep(crawl_delay)

        response = self._session.get(url, **kwargs)

        status = HTTPStatus(response.status_code)
        logger.debug(
            "    Received {} {} for {}".format(status.value, status.name, response.url)
        )
        if response.status_code != HTTPStatus.OK.value:
            raise UnexpectedStatusCodeException(
                response.url, HTTPStatus(response.status_code)
            )

        return response
