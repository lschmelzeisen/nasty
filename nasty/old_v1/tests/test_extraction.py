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

from codecs import open
from pathlib import Path
from unittest import TestCase

from advanced_search import _extract_tweets_from_advanced_search_page
from tweet import Tweet

data = "can't copy it here. to many errors. so reading from file"
html_file = (
    Path().absolute().parent.parent.parent.parent
    / "html-examples"
    / "AdvancedSearch - Tweet_fragment_2.html"
)
with open(html_file, "r", encoding="UTF-8") as html:
    html_data = html.read()


class TestExtraction(TestCase):
    def test_if_an_error_raised(self):
        _extract_tweets_from_advanced_search_page(html_data)

    def test_if_tweet_object_matches(self):
        # TODO: Fill Tweet object with info
        expected = Tweet(
            "Sun Jun 23 18:54:33 +0000 2019",
            "1142868564866719744",
            "Album News: Napalm Death, Oakenform, @Eradikator, @KamikazeZombie\n\nhttps://t.co/d9TZnVlYGT\n\n#metal #heavymetal #music #MoshvilleTimes @officialND https://t.co/A5tbK1x8Z8'",
            "MoshTimes",
            "MoshvilleTimes",
            [],
            [],
            [],
        )
        got, _ = _extract_tweets_from_advanced_search_page(html_data)

        # Created_at test
        self.assertEqual(expected.created_at, got[0].created_at)

        # id test
        self.assertEqual(expected.id, got[0].id)

        # full_text test
        self.assertEqual(expected.full_text, got[0].full_text)

        # name test
        self.assertEqual(expected.name, got[0].name)

        # screen_name test
        self.assertEqual(expected.screen_name, got[0].screen_name)

        # TODO: Those three are list of object, should not work right now
        # hashtags test
        self.assertEqual(expected.hashtags, got[0].hashtags)

        # user_mentions test
        self.assertEqual(expected.user_mentions, got[0].user_mentions)

        # urls test
        self.assertEqual(expected.urls, got[0].urls)
