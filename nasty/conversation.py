from typing import Dict, Iterable, Optional
from abc import abstractmethod

from nasty.timeline import Timeline


class Conversation(Timeline):
    def __init__(self,
                 tweet_id: str,
                 max_tweets: Optional[int] = 100,
                 batch_size: Optional[int] = None):
        super().__init__(max_tweets=max_tweets, batch_size=batch_size)
        self.tweet_id = tweet_id

    def _timeline_url(self) -> Dict:
        return {
            'url':
                'https://mobile.twitter.com/_/status/{}'.format(self.tweet_id),
        }

    def _batch_url(self, cursor: Optional[str] = None) -> Dict:
        return {
            'url': ('https://api.twitter.com/2/timeline/conversation/{:s}.json'
                    .format(self.tweet_id)),
            'params': {
                'include_profile_interstitial_type': 1,
                'include_blocking': 1,
                'include_blocked_by': 1,
                'include_followed_by': 1,
                'include_want_retweets': 1,
                'include_mute_edge': 1,
                'include_can_dm': 1,
                'include_can_media_tag': 1,
                'skip_status': 1,
                'cards_platform': 'Web-12',
                'include_cards': 1,
                'include_composer_source': 'true',
                'include_ext_alt_text': 'true',
                'include_reply_count': 1,
                'tweet_mode': 'extended',
                'include_entities': 'true',
                'include_user_entities': 'true',
                'include_ext_media_color': 'true',
                'include_ext_media_availability': 'true',
                'send_error_codes': 'true',
                'count': self.batch_size,
                'cursor': cursor,
                'ext': 'mediaStats,highlightedLabel,cameraMoment',
            }
        }

    # Copy definitions of base class, so that PyCharm doesn't give the warning
    # that we have forgotten to implement abstract methods.

    @abstractmethod
    def _tweet_ids_in_batch(self, batch: Dict) -> Iterable[str]:
        raise NotImplementedError()

    @abstractmethod
    def _next_cursor_from_batch(self, batch: Dict) -> Optional[str]:
        raise NotImplementedError()
