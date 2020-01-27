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
from ..request.thread import Thread
from ..tweet.tweet import TweetId
from .conversation_retriever import ConversationRetriever, ConversationRetrieverBatch


class ThreadRetrieverBatch(ConversationRetrieverBatch):
    @overrides
    def _tweet_ids(self) -> Iterable[TweetId]:
        # TODO: ensure all tweets in a thread are by the same user

        # The first conversation batch contains entries for the Tweet with the requested
        # URL and possibly multiple conversation threads where the first on is always
        # the one where the Tweet author responds to himself for the first time:
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
        #                     ]
        #                 },
        #             },
        #             ...
        #         ],
        #         ...
        #     },
        # }
        #
        # Inside of the "conversationThread-" we find the actual thread Tweets:
        # {
        #     "entryId": "conversationThread-1155488356165398528",
        #     "sortIndex": "8067885539403591669",
        #     "content": {
        #         "timelineModule": {
        #             "items": [
        #                 {"entryId": "tweet-1155488356165398528", ...},
        #                 {"entryId": "tweet-1155490920621473792", ...},
        #                 ...
        #                 {"entryId": "conversationThread-11...-show_more_cursor", ...},
        #             ],
        #             ...
        #         }
        #     },
        # }
        # If the thread is over, the "...-show_more_cursor" is not present.
        #
        # All following batches will look like this instead:
        # {
        #     ...
        #     "timeline": {
        #         "id": "Conversation-1155486497451184128",
        #         "instructions": [
        #             {
        #                 "addToModule": {
        #                     "moduleItems": [
        #                         {"entryId": "tweet-1156606255940739078", ...},
        #                         {"entryId": "tweet-1156634771507810306", ...},
        #                         ...
        #                     ]
        #                 }
        #             }
        #         ],
        #     },
        # }
        for entry in self._parse_instructions():
            if entry["entryId"].startswith("tweet-"):
                # Tweets in the thread look like this:
                # {
                #     "entryId": "tweet-1155488356165398528",
                #     "item": {
                #         "content": {
                #             "tweet": {
                #                 "id": "1155488356165398528",
                #                 "displayType": "SelfThread",
                #             }
                #         },
                #         ...
                #     },
                # }

                if "tombstone" in entry["item"]["content"]:
                    # Sometimes Tweets become unavailable over time (for instance
                    # because they were deleted). They sometimes still show up
                    # in results but are only designated with a tombstone. We skip those
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
                    yield entry["item"]["content"]["tweet"]["id"]

            elif entry["entryId"].startswith("conversationThread-") and entry[
                "entryId"
            ].endswith("-show_more_cursor"):
                pass
            else:
                raise RuntimeError(
                    "Unknown entry type in entry-ID: '{}'.".format(entry["entryId"])
                )

    @overrides
    def _next_cursor(self) -> Optional[str]:
        # See the documentation of _tweet_ids_in_batch() on where the cursor entry
        # occurs. It looks like this:
        # {
        #     "entryId": "conversationThread-1155488...-show_more_cursor",
        #     "item": {
        #         "content": {
        #             "timelineCursor": {
        #                 "value": "TBwcFoLAvI3JhYuNIBUCAAAYJmNvbnZlcnNhdGlvbl...",
        #                 "cursorType": "ShowMore",
        #                 "displayTreatment": {"actionText": "5 more replies"},
        #             }
        #         },
        #         ...
        #     },
        # }
        instructions = self._parse_instructions()
        if not instructions:
            return None

        cursor_entry = instructions[-1]
        if cursor_entry["entryId"].startswith("conversationThread-") and cursor_entry[
            "entryId"
        ].endswith("-show_more_cursor"):
            return checked_cast(
                str, cursor_entry["item"]["content"]["timelineCursor"]["value"]
            )
        return None

    def _parse_instructions(self) -> Sequence[Any]:
        # See the documentation of _tweet_ids_in_batch() on what JSON-structures
        # this navigates.
        instructions: Final = cast(
            Sequence[Any], self._json["timeline"]["instructions"]
        )
        if "addEntries" in instructions[0]:
            entries = instructions[0]["addEntries"]["entries"]
            if not (
                len(entries) >= 2
                and entries[1]["entryId"].startswith("conversationThread-")
            ):
                return []
            return cast(Sequence[Any], entries[1]["content"]["timelineModule"]["items"])
        elif "addToModule" in instructions[0]:
            return cast(Sequence[Any], instructions[0]["addToModule"]["moduleItems"])
        else:
            raise RuntimeError("Could not parse conversation instructions.")


class ThreadRetriever(ConversationRetriever[Thread]):
    @classmethod
    @overrides
    def _retriever_batch_type(cls) -> Type[ThreadRetrieverBatch]:
        return ThreadRetrieverBatch
