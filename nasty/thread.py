from logging import getLogger
from typing import Dict, Iterable, Optional

from nasty.conversation import Conversation


class Thread(Conversation):
    def __init__(self,
                 tweet_id: str,
                 max_tweets: Optional[int] = 100,
                 batch_size: Optional[int] = None):
        super().__init__(
            tweet_id=tweet_id, max_tweets=max_tweets, batch_size=batch_size)
        self.num_tombstones = None

        logger = getLogger(__name__)
        logger.debug('Fetching thread of Tweet {}.'.format(self.tweet_id))

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
            if entry['entryId'].startswith('tweet-'):
                # Tweets in the threat look like this:
                # { "entryId": "tweet-1155488356165398528",
                #   "item": {
                #     "content": {
                #       "tweet": {
                #         "id": "1155488356165398528",
                #         "displayType": "SelfThread" }}
                #     ... }}

                if 'tombstone' in entry['item']['content']:
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
                    yield entry['item']['content']['tweet']['id']

            elif (entry['entryId'].startswith('conversationThread-')
                  and entry['entryId'].endswith('-show_more_cursor')):
                pass
            else:
                raise RuntimeError('Unknown entry type in entry-ID: {}'
                                   .format(entry['entryId']))

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
        if (cursor_entry['entryId'].startswith('conversationThread-')
                and cursor_entry['entryId'].endswith('-show_more_cursor')):
            return cursor_entry['item']['content']['timelineCursor']['value']
        return None

    @classmethod
    def _parse_batch_instructions(cls, batch: Dict) -> Iterable[Dict]:
        # See the documentation of _tweet_ids_in_batch() on what JSON-structures
        # this navigates.
        instructions = batch['timeline']['instructions']
        if 'addEntries' in instructions[0]:
            entries = instructions[0]['addEntries']['entries']
            if not (len(entries) >= 2 and entries[1]['entryId'].startswith(
                    'conversationThread-')):
                return []
            return entries[1]['content']['timelineModule']['items']
        elif 'addToModule' in instructions[0]:
            return instructions[0]['addToModule']['moduleItems']
        else:
            raise RuntimeError('Could parse conversation instructions.')

# 1183715553057239040

# The requested Tweet entry look like this:
# { "entryId": "tweet-1155486497451184128",
#   "sortIndex": "8067885539403591679",
#   "content": {
#     "item": {
#       "content": {
#         "tweet": {
#           "id": "1155486497451184128",
#           "displayType": "SelfThread",
#           "hasModeratedReplies": false }}}}}
