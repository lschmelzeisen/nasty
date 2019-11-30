#
# Copyright 2019 Lukas Schmelzeisen
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

from logging import getLogger
from typing import Any, Dict, Iterable, Optional

from nasty.jobs import Job
from nasty.retrieval.conversation import Conversation
from nasty.retrieval.timeline import Timeline


class Replies(Conversation):
    """Retrieve all direct replies to a Tweet."""

    class Work(Timeline.Work):
        def __init__(
            self, tweet_id: str, max_tweets: Optional[int], batch_size: Optional[int]
        ):
            super().__init__("replies", max_tweets, batch_size)
            self.tweet_id = tweet_id

        def to_timeline(self) -> Timeline:
            return Replies(self.tweet_id, self.max_tweets, self.batch_size)

        def to_json(self) -> Dict[str, Any]:
            obj = {
                "type": self.type,
                "tweet_id": self.tweet_id,
            }

            if self.max_tweets is not None:
                obj["max_tweets"] = self.max_tweets
            if self.batch_size is not None:
                obj["batch_size"] = self.batch_size

            return obj

        @classmethod
        def from_json(cls, obj: Dict[str, Any]) -> Timeline.Work:
            assert obj["type"] == "replies"
            return cls(obj["tweet_id"], obj.get("max_tweets"), obj.get("batch_size"))

    def __init__(
        self,
        tweet_id: str,
        max_tweets: Optional[int] = 100,
        batch_size: Optional[int] = None,
    ):
        """"Constructs a new replies view.

        See the base class for documentation of the tweet_id, max_tweets, and
        batch_size parameters.
        """

        super().__init__(
            tweet_id=tweet_id, max_tweets=max_tweets, batch_size=batch_size
        )
        self.num_tombstones = None

        logger = getLogger(__name__)
        logger.debug("Fetching replies of Tweet {}.".format(self.tweet_id))

    def to_job(self) -> Job:
        return Job(self.Work(self.tweet_id, self.max_tweets, self.batch_size))

    def _tweet_ids_in_batch(self, batch: Dict) -> Iterable[str]:
        # Replies are nested in conversation threads contained in instructions.
        # Batches look like this:
        # { ...
        #   "timeline": {
        #     "id": "Conversation-1155486497451184128",
        #     "instructions": [
        #       { "addEntries": {
        #           "entries": [
        #             { "entryId": "tweet-1155486497451184128", ... },
        #             { "entryId": "conversationThread-1155488356165398528",
        #                ... },
        #             { "entryId": "conversationThread-1156602033438384128",
        #                ... },
        #             { "entryId": "conversationThread-1155505742373253120",
        #               ... },
        #             ...
        #             { "entryId": "cursor-bottom-8067885539403591668", ... }]}
        #       },
        #       ... ]
        #    ... }}
        #
        # The Tweet that corresponds to the requested ID has a "tweet-..." entry
        # in the first batch (this is missing from following batches), with
        # multiple "conversationThread-..." entries following and a
        # "cursor-bottom-..." entry at the end, which contains the contain the
        # cursor needed to fetch the next batch. Seldom it will be a
        # "cursor-showMoreThreads-..." or a 'cursor-showMoreThreadsPrompt-..."
        # reply. If no more replies exist the cursor entry will also not exist.
        instructions = batch["timeline"]["instructions"]

        for entry in instructions[0]["addEntries"]["entries"]:
            if entry["entryId"].startswith("tweet-"):
                # We do not want to return the Tweet with the requested ID
                # because it is not a reply to itself.
                pass

            elif entry["entryId"].startswith("conversationThread-"):
                # Conversation thread entries look like this:
                #  { "entryId": "conversationThread-1155488356165398528",
                #    "sortIndex": "8067885539403591669",
                #    "content": {
                #      "timelineModule": {
                #        "items": [
                #          { "entryId": "tweet-1155488356165398528",
                #            "item": {
                #              "content": {
                #                "tweet": {
                #                  "id": "1155488356165398528",
                #                  "displayType": "SelfThread" }},
                #           { "entryId": "tweet-1155490920621473792",
                #             "item": {
                #               "content": {
                #                 "tweet": {
                #                   "id": "1155490920621473792",
                #                   "displayType": "SelfThread" }},
                #              ... }}
                #          ... ]}}}
                # That is, a conversation is a list of Tweet entries. Here the
                # first entry is a direct reply to the requested Tweet and all
                # following entries are replies to the previous entry.
                reply_tweet = entry["content"]["timelineModule"]["items"][0]

                if "tombstone" in reply_tweet["item"]["content"]:
                    # Sometimes Tweets become unavailable over time (for
                    # instance because they were deleted). They sometimes still
                    # show up in results but are only designated with a
                    # tombstone. We skip those when returning results.
                    # { "entryId": "tweet-1079406406644715520",
                    #   "item": {
                    #     "content": {
                    #       "tombstone": {
                    #         "displayType": "Inline",
                    #         "tombstoneInfo": {
                    #           "text": "",
                    #           "richText": {
                    #             "text": "This Tweet is unavailable.",
                    #             "entities": [],
                    #             "rtl": false }}
                    #         "epitaph": "Suspended" }}
                    #     ... }}
                    if self.num_tombstones is None:
                        self.num_tombstones = 0
                    self.num_tombstones += 1

                else:
                    yield reply_tweet["item"]["content"]["tweet"]["id"]

            elif entry["entryId"].startswith("label-"):
                # Sometimes additional replies can be loaded in the UI via a
                # "Load more replies" button. These replies appear under a
                # "More replies" label, which is added by this entry.
                # { "entryId": "label-8127279332145703061",
                #   "sortIndex": "8127279332145703061",
                #   "content": {
                #     "item": {
                #       "content": {
                #         "label": {
                #           "text": "More replies",
                #           "displayType": "InlineHeader" }}}}}
                pass
            elif entry["entryId"].startswith("cursor-bottom-"):
                pass
            elif entry["entryId"].startswith("cursor-showMoreThreads-"):
                pass
            elif entry["entryId"].startswith("cursor-showMoreThreadsPrompt-"):
                pass
            else:
                raise RuntimeError(
                    "Unknown entry type in entry-ID: {}".format(entry["entryId"])
                )

    def _next_cursor_from_batch(self, batch: Dict) -> Optional[str]:
        # See the documentation of _tweet_ids_in_batch() on where the cursor
        # entry occurs. It looks like this:
        # { "entryId": "cursor-bottom-8067885539403591668",
        #   "sortIndex": "8067885539403591668",
        #   "content": {
        #     "operation": {
        #       "cursor": {
        #         "value": "LBkWgMC1tbaij4kgJQISAAA=",
        #         "cursorType": "Bottom" }}}}
        instructions = batch["timeline"]["instructions"]
        cursor_entry = instructions[0]["addEntries"]["entries"][-1]
        if cursor_entry["entryId"].startswith("cursor-bottom"):
            return cursor_entry["content"]["operation"]["cursor"]["value"]

        # Seldom the cursor entry looks like this instead:
        # { "entryId": "cursor-showMoreThreads-8067885539403590108",
        #   "sortIndex": "8067885539403590108",
        #   "content": {
        #     "operation": {
        #       "cursor": {
        #         "value": "LBn2nQGAwLW1tqKPiSCAgLfZ/NqJjSCAwKf...",
        #         "cursorType": "ShowMoreThreads",
        #         "displayTreatment": {
        #           "actionText": "Show more replies" }}}}}
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
            return cursor_entry["content"]["operation"]["cursor"]["value"]

        return None
