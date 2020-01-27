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

from typing import Any, Iterable, Mapping, Optional, Sequence, Type, cast

from overrides import overrides
from typing_extensions import Final

from .._util.typing_ import checked_cast
from ..request.search import Search, SearchFilter
from ..tweet.tweet import TweetId
from .retriever import Retriever, RetrieverBatch


class SearchRetrieverBatch(RetrieverBatch):
    @overrides
    def _tweet_ids(self) -> Iterable[TweetId]:
        instructions: Final = cast(
            Sequence[Any], self._json["timeline"]["instructions"]
        )

        # Search results are contained in instructions. The first batch of a search will
        # look like this:
        # {
        #     ...
        #     "timeline": {
        #         "id": "search-6602913952152093875",
        #         "instructions": [
        #             {
        #                 "addEntries": {
        #                     "entries": [
        #                         {"entryId": "sq-I-t-1155486497451184128", ...},
        #                         {"entryId": "sq-I-t-1194473608061607936", ...},
        #                         {"entryId": "sq-M-1-d7721393", ...},
        #                         {"entryId": "sq-E-1981039365", ...},
        #                         ...
        #                         {"entryId": "sq-cursor-top", ...},
        #                         {"entryId": "sq-cursor-bottom", ...},
        #                     ]
        #                 }
        #             }
        #         ],
        #         ...
        #     },
        # }
        #
        # We need to separate the following entity types:
        # - "sq-I-t-..." are the Tweets matching the search query.
        # - "sq-M-..." contain supplementary information like user profiles that are
        #   somehow related to the matching Tweets (usually occurs once).
        # - "sq-E-..." seem to contain suggested live events (occur rarely).
        # - "sq-cursor-..." entries contain the cursors to fetch the next batch.
        #
        # All following batches will look similar except that the "sq-cursor-..."
        # entries are now differently placed:
        # {
        #     ...
        #     "timeline": {
        #         "id": "search-6602913956034868792",
        #         "instructions": [
        #             {
        #                 "addEntries": {
        #                     "entries": [
        #                         {"entryId": "sq-I-t-1157704001112219650", ...},
        #                         {"entryId": "sq-I-t-1156734175040266240", ...},
        #                         ...
        #                     ]
        #                 }
        #             },
        #             {
        #                 "replaceEntry": {
        #                     "entryIdToReplace": "sq-cursor-top",
        #                     "entry": {"entryId": "sq-cursor-top", ...},
        #                 }
        #             },
        #             {
        #                 "replaceEntry": {
        #                     "entryIdToReplace": "sq-cursor-bottom",
        #                     "entry": {"entryId": "sq-cursor-bottom", ...},
        #                 }
        #             },
        #         ],
        #         ...
        #     },
        # }

        for entry in instructions[0]["addEntries"]["entries"]:
            if entry["entryId"].startswith("sq-I-t-"):
                # Matching Tweet entries look like this:
                # {
                #     "entryId": "sq-I-t-1155486497451184128",
                #     "sortIndex": "999970",
                #     "content": {
                #         "item": {
                #             "content": {
                #                 "tweet": {
                #                     "id": "1155486497451184128",
                #                     "displayType": "Tweet",
                #                     "highlights": {...},
                #                 }
                #             },
                #             ...
                #         }
                #     },
                # }
                yield checked_cast(
                    TweetId, entry["content"]["item"]["content"]["tweet"]["id"]
                )
            elif entry["entryId"].startswith("sq-M-"):
                pass
            elif entry["entryId"].startswith("sq-E-"):
                pass
            elif entry["entryId"].startswith("sq-cursor-"):
                pass
            else:
                raise RuntimeError(
                    "Unknown entry type in entry-ID '{}'.".format(entry["entryId"])
                )

    @overrides
    def _next_cursor(self) -> Optional[str]:
        instructions: Final = cast(
            Sequence[Any], self._json["timeline"]["instructions"]
        )

        # As documented in _tweet_ids_in_batch(), the cursor objects can occur either
        # as part of "addEntries" or replaceEntry". We are only interested in
        # sq-cursor-bottom and I'm not sure what sq-cursor-top is for. The actual cursor
        # entry will look like this:
        # {
        #     "entryId": "sq-cursor-bottom",
        #     "sortIndex": "0",
        #     "content": {
        #         "operation": {
        #             "cursor": {"value": "scroll:thGAVUV...", "cursorType": "Bottom"}
        #         }
        #     },
        # }

        cursor_entry = None
        if instructions[0]["addEntries"]["entries"]:
            cursor_entry = instructions[0]["addEntries"]["entries"][-1]
        if not cursor_entry or cursor_entry["entryId"] != "sq-cursor-bottom":
            cursor_entry = instructions[-1]["replaceEntry"]["entry"]
        if cursor_entry["entryId"] != "sq-cursor-bottom":
            raise RuntimeError("Could not locate cursor entry.")
        return cast(
            Optional[str], cursor_entry["content"]["operation"]["cursor"]["value"]
        )


class SearchRetriever(Retriever[Search]):
    @classmethod
    @overrides
    def _retriever_batch_type(cls) -> Type[SearchRetrieverBatch]:
        return SearchRetrieverBatch

    @overrides
    def _timeline_url(self) -> Mapping[str, object]:
        return {
            "url": "https://mobile.twitter.com/search",
            "params": {
                "lang": self._request.lang,
                "q": self._q_url_param(),
                "src": "typed_query",
                "f": self._f_url_param(),
            },
        }

    @overrides
    def _batch_url(self) -> Mapping[str, object]:
        return {
            "url": "https://api.twitter.com/2/search/adaptive.json",
            "params": {
                # Not sure what most of the parameters with fixed values do. We set them
                # so that they are identical to those sent via the normal web interface.
                "include_profile_interstitial_type": "1",
                "include_blocking": "1",
                "include_blocked_by": "1",
                "include_followed_by": "1",
                "include_want_retweets": "1",
                "include_mute_edge": "1",
                "include_can_dm": "1",
                "include_can_media_tag": "1",
                "skip_status": "1",
                "cards_platform": "Web-12",
                "include_cards": "1",
                "include_composer_source": "true",
                "include_ext_alt_text": "true",
                "include_reply_count": "1",
                "tweet_mode": "extended",
                "include_entities": "true",
                "include_user_entities": "true",
                "include_ext_media_color": "true",
                "include_ext_media_availability": "true",
                "send_error_codes": "true",
                "q": self._q_url_param(),
                "count": self._request.batch_size,
                "result_filter": self._result_filter_url_param(),
                "tweet_search_mode": self._tweet_search_mode_url_param(),
                "query_source": "typed_query",
                "cursor": self._cursor,
                "pc": "1",
                "spelling_corrections": "1",
                "ext": "mediaStats,highlightedLabel,cameraMoment",
            },
        }

    def _q_url_param(self) -> str:
        """Transforms the stored query into the form that can be submitted to Twitter as
        an URL param.

        Does not perform URL escaping.
        """
        result = self._request.query
        if self._request.since:
            result += " since:" + self._request.since.isoformat()
        if self._request.until:
            result += " until:" + self._request.until.isoformat()
        result += " lang:" + self._request.lang
        return result

    def _f_url_param(self) -> Optional[str]:
        return {
            SearchFilter.LATEST: "live",
            SearchFilter.PHOTOS: "image",
            SearchFilter.VIDEOS: "video",
        }.get(self._request.filter, None)

    def _result_filter_url_param(self) -> Optional[str]:
        return {SearchFilter.PHOTOS: "image", SearchFilter.VIDEOS: "video"}.get(
            self._request.filter, None
        )

    def _tweet_search_mode_url_param(self) -> Optional[str]:
        return {SearchFilter.LATEST: "live"}.get(self._request.filter, None)
