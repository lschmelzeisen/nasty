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


class Thread(Conversation):
    """Retrieve the remaining thread of a Tweet.

    A thread of a Tweet is a reply to the Tweet, a reply to the reply, and so
    on. As at each hierarchy level, multiple sibling replies can exist, this
    API depends on Twitter's own display rules. Usually, if a person is replying
    to themselves, this will always form the thread.

    See: https://help.twitter.com/en/using-twitter/create-a-thread
    """

    class Work(Timeline.Work):
        def __init__(
            self, tweet_id: str, max_tweets: Optional[int], batch_size: Optional[int]
        ):
            super().__init__("thread", max_tweets, batch_size)
            self.tweet_id = tweet_id

        def to_timeline(self) -> Timeline:
            return Thread(self.tweet_id, self.max_tweets, self.batch_size)

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
            assert obj["type"] == "thread"
            return cls(obj["tweet_id"], obj.get("max_tweets"), obj.get("batch_size"))

    def __init__(
        self,
        tweet_id: str,
        max_tweets: Optional[int] = 100,
        batch_size: Optional[int] = None,
    ):
        """"Constructs a new thread view.

        See the base class for documentation of the tweet_id, max_tweets, and
        batch_size parameters.
        """

        super().__init__(
            tweet_id=tweet_id, max_tweets=max_tweets, batch_size=batch_size
        )
        self.num_tombstones = None

        logger = getLogger(__name__)
        logger.debug("Fetching thread of Tweet {}.".format(self.tweet_id))

    def to_job(self):
        return Job(self.Work(self.tweet_id, self.max_tweets, self.batch_size))

    def _tweet_ids_in_batch(self, batch: Dict) -> Iterable[str]:
        # The first conversation batch contains entries for the Tweet with the
        # requested URL and possibly multiple conversation threads where the
        # first on is always the one where the Tweet author responds to himself
        # for the first time:
        # { ...
        #   "timeline": {
        #     "id": "Conversation-1155486497451184128",
        #     "instructions": [
        #       { "addEntries": {
        #           "entries": [
        #             { "entryId": "tweet-1155486497451184128", ... },
        #             { "entryId": "conversationThread-1155488356165398528",
        #                ... },
        #       },
        #       ... ]
        #    ... }}
        #
        # Inside of the "conversationThread-" we find the actual thread Tweets:
        # { "entryId": "conversationThread-1155488356165398528",
        #   "sortIndex": "8067885539403591669",
        #   "content": {
        #     "timelineModule": {
        #       "items": [
        #         { "entryId": "tweet-1155488356165398528", ... },
        #         { "entryId": "tweet-1155490920621473792", ... },
        #         ...
        #         { "entryId": "conversationThread-1155488...-show_more_cursor",
        #           ... }]
        #       ... }}}
        # If the thread is over the "...-show_more_cursor" is not present.
        #
        # All following batches will look like this instead:
        # { ...
        #   "timeline": {
        #     "id": "Conversation-1155486497451184128",
        #     "instructions": [
        #       { "addToModule": {
        #           "moduleItems": [
        #             { "entryId": "tweet-1156606255940739078", ... },
        #             { "entryId": "tweet-1156634771507810306", ... },
        #             ... ]}}]}}
        for entry in self._parse_batch_instructions(batch):
            if entry["entryId"].startswith("tweet-"):
                # Tweets in the thread look like this:
                # { "entryId": "tweet-1155488356165398528",
                #   "item": {
                #     "content": {
                #       "tweet": {
                #         "id": "1155488356165398528",
                #         "displayType": "SelfThread" }}
                #     ... }}

                if "tombstone" in entry["item"]["content"]:
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
                    yield entry["item"]["content"]["tweet"]["id"]

            elif entry["entryId"].startswith("conversationThread-") and entry[
                "entryId"
            ].endswith("-show_more_cursor"):
                pass
            else:
                raise RuntimeError(
                    "Unknown entry type in entry-ID: {}".format(entry["entryId"])
                )

    def _next_cursor_from_batch(self, batch: Dict) -> Optional[str]:
        # See the documentation of _tweet_ids_in_batch() on where the cursor
        # entry occurs. It looks like this:
        # { "entryId": "conversationThread-1155488...-show_more_cursor",
        #   "item": {
        #    "content": {
        #      "timelineCursor": {
        #        "value": "TBwcFoLAvI3JhYuNIBUCAAAYJmNvbnZlcnNhdGlvbl...",
        #        "cursorType": "ShowMore",
        #        "displayTreatment": {
        #          "actionText": "5 more replies" }}}
        #       ... }}
        cursor_entry = self._parse_batch_instructions(batch)[-1]
        if cursor_entry["entryId"].startswith("conversationThread-") and cursor_entry[
            "entryId"
        ].endswith("-show_more_cursor"):
            return cursor_entry["item"]["content"]["timelineCursor"]["value"]
        return None

    @classmethod
    def _parse_batch_instructions(cls, batch: Dict) -> Iterable[Dict]:
        # See the documentation of _tweet_ids_in_batch() on what JSON-structures
        # this navigates.
        instructions = batch["timeline"]["instructions"]
        if "addEntries" in instructions[0]:
            entries = instructions[0]["addEntries"]["entries"]
            if not (
                len(entries) >= 2
                and entries[1]["entryId"].startswith("conversationThread-")
            ):
                return []
            return entries[1]["content"]["timelineModule"]["items"]
        elif "addToModule" in instructions[0]:
            return instructions[0]["addToModule"]["moduleItems"]
        else:
            raise RuntimeError("Could parse conversation instructions.")
