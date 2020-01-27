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

from typing import Any, Iterable, Optional, Sequence, Type, cast

from overrides import overrides
from typing_extensions import Final

from .._util.typing_ import checked_cast
from ..request.replies import Replies
from ..tweet.tweet import TweetId
from .conversation_retriever import ConversationRetriever, ConversationRetrieverBatch


class RepliesRetrieverBatch(ConversationRetrieverBatch):
    @overrides
    def _tweet_ids(self) -> Iterable[TweetId]:
        instructions: Final = cast(
            Sequence[Any], self._json["timeline"]["instructions"]
        )

        # Replies are nested in conversation threads contained in instructions. Batches
        # look like this:
        # {
        #     ...
        #     "timeline": {
        #         "id": "Conversation-1155486497451184128",
        #         "instructions": [
        #             {
        #                 "addEntries": {
        #                     "entries": [
        #                         {"entryId": "tweet-1155486497451184128", ...},
        #                         {"entryId": "conversationThread-11554883561...", ...},
        #                         {"entryId": "conversationThread-11566020334...", ...},
        #                         {"entryId": "conversationThread-11555057423...", ...},
        #                         ...
        #                         {"entryId": "cursor-bottom-8067885539403591668", ...},
        #                     ]
        #                 }
        #             },
        #             ...
        #         ],
        #         ...
        #     },
        # }
        #
        # The Tweet that corresponds to the requested ID has a "tweet-..." entry in the
        # first batch (this is missing from following batches), with multiple
        # "conversationThread-..." entries following and a "cursor-bottom-..." entry at
        # the end, which contains the contain the cursor needed to fetch the next batch.
        # Seldom it will be a "cursor-showMoreThreads-..." or a
        # "cursor-showMoreThreadsPrompt-..." reply. If no more replies exist the cursor
        # entry will also not exist.

        for entry in instructions[0]["addEntries"]["entries"]:
            if entry["entryId"].startswith("tweet-"):
                # We do not want to return the Tweet with the requested ID because it is
                # not a reply to itself.
                pass

            elif entry["entryId"].startswith("conversationThread-"):
                # Conversation thread entries look like this:
                # {
                #     "entryId": "conversationThread-1155488356165398528",
                #     "sortIndex": "8067885539403591669",
                #     "content": {
                #         "timelineModule": {
                #             "items": [
                #                 {
                #                     "entryId": "tweet-1155488356165398528",
                #                     "item": {
                #                         "content": {
                #                             "tweet": {
                #                                 "id": "1155488356165398528",
                #                                 "displayType": "SelfThread",
                #                             }
                #                         }
                #                     },
                #                 },
                #                 {
                #                     "entryId": "tweet-1155490920621473792",
                #                     "item": {
                #                         "content": {
                #                             "tweet": {
                #                                 "id": "1155490920621473792",
                #                                 "displayType": "SelfThread",
                #                             }
                #                         }
                #                     },
                #                 },
                #                 ...
                #             ]
                #         }
                #     },
                # }
                # That is, a conversation is a list of Tweet entries. Here the first
                # entry is a direct reply to the requested Tweet and all following
                # entries are replies to the previous entry.
                reply_tweet = entry["content"]["timelineModule"]["items"][0]

                if "tombstone" in reply_tweet["item"]["content"]:
                    # Sometimes Tweets become unavailable over time (for instance
                    # because they were deleted). They sometimes still show up in
                    # results but are only designated with a tombstone. We skip those
                    # when returning results.
                    # {
                    #     "entryId": "tweet-1079406406644715520",
                    #     "item": {
                    #         "content": {
                    #             "tombstone": {
                    #                 "displayType": "Inline",
                    #                 "tombstoneInfo": {
                    #                     "text": "",
                    #                     "richText": {
                    #                         "text": "This Tweet is unavailable.",
                    #                         "entities": [],
                    #                         "rtl": False,
                    #                     },
                    #                 },
                    #                 "epitaph": "Suspended",
                    #             }
                    #         },
                    #         ...
                    #     },
                    # }
                    self.num_tombstones += 1

                else:
                    yield checked_cast(
                        TweetId, reply_tweet["item"]["content"]["tweet"]["id"]
                    )

            elif entry["entryId"].startswith("label-"):
                # Sometimes additional replies can be loaded in the UI via a "Load more
                # replies" button. These replies appear under a "More replies" label,
                # which is added by this entry.
                # {
                #     "entryId": "label-8127279332145703061",
                #     "sortIndex": "8127279332145703061",
                #     "content": {
                #         "item": {
                #             "content": {
                #                 "label": {
                #                     "text": "More replies",
                #                     "displayType": "InlineHeader",
                #                 }
                #             }
                #         }
                #     },
                # }
                pass
            elif entry["entryId"].startswith("cursor-bottom-"):
                pass
            elif entry["entryId"].startswith("cursor-showMoreThreads-"):
                pass
            elif entry["entryId"].startswith("cursor-showMoreThreadsPrompt-"):
                pass
            else:
                raise RuntimeError(
                    "Unknown entry type in entry-ID: '{}'.".format(entry["entryId"])
                )

    @overrides
    def _next_cursor(self) -> Optional[str]:
        instructions: Final = cast(
            Sequence[Any], self._json["timeline"]["instructions"]
        )

        # See the documentation of _tweet_ids_in_batch() on where the cursor entry
        # occurs. It looks like this:
        # {
        #     "entryId": "cursor-bottom-8067885539403591668",
        #     "sortIndex": "8067885539403591668",
        #     "content": {
        #         "operation": {
        #             "cursor": {
        #                 "value": "LBkWgMC1tbaij4kgJQISAAA=",
        #                 "cursorType": "Bottom",
        #             }
        #         }
        #     },
        # }

        cursor_entry = instructions[0]["addEntries"]["entries"][-1]
        if cursor_entry["entryId"].startswith("cursor-bottom"):
            return checked_cast(
                str, cursor_entry["content"]["operation"]["cursor"]["value"]
            )

        # Seldom the cursor entry looks like this instead:
        # {
        #     "entryId": "cursor-showMoreThreads-8067885539403590108",
        #     "sortIndex": "8067885539403590108",
        #     "content": {
        #         "operation": {
        #             "cursor": {
        #                 "value": "LBn2nQGAwLW1tqKPiSCAgLfZ/NqJjSCAwKf...",
        #                 "cursorType": "ShowMoreThreads",
        #                 "displayTreatment": {"actionText": "Show more replies"},
        #             }
        #         }
        #     },
        # }
        # This is very likely related to Twitter's UI of Show more replies, but
        # I don't know what the difference to regular replies is.
        #
        # In even rarer cases, it looks like this:
        # { "entryId": "cursor-showMoreThreadsPrompt-8127279332145704315",
        #   "sortIndex": "8127279332145704315",
        #   "content": {
        #     "operation": {
        #       "cursor": {
        #         "value": "LBn2QICAqL24y8K2HoTArbHpyZO2HoCApqXKh5...",
        #         "cursorType": "ShowMoreThreadsPrompt",
        #         "displayTreatment": {
        #           "actionText": "Show",
        #           "labelText": "Show additional replies, including those "
        #                        "that may contain offensive content" }}}}}
        elif cursor_entry["entryId"].startswith(
            "cursor-showMoreThreads-"
        ) or cursor_entry["entryId"].startswith("cursor-showMoreThreadsPrompt-"):
            return checked_cast(
                str, cursor_entry["content"]["operation"]["cursor"]["value"]
            )

        return None


class RepliesRetriever(ConversationRetriever[Replies]):
    @classmethod
    @overrides
    def _retriever_batch_type(cls) -> Type[RepliesRetrieverBatch]:
        return RepliesRetrieverBatch
