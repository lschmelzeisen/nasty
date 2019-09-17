import unittest
from unittest import TestCase
from pathlib import Path
from codecs import open
from tweet import Tweet
from advanced_search import _extract_tweets_from_advanced_search_page

data = "can't copy it here. to many errors. so reading from file"
html_file = Path().absolute().parent.parent.parent.parent / "html-examples" / "AdvancedSearch - Tweet_fragment_2.html"
with open(html_file, "r", encoding="UTF-8") as html:
    html_data = html.read()


class TestExtraction(TestCase):

    def test_if_an_error_raised(self):
        _extract_tweets_from_advanced_search_page(html_data)

    def test_if_tweet_object_matches(self):
        # TODO: Fill Tweet object with info
        expected = Tweet("Sun Jun 23 18:54:33 +0000 2019",
                         "1142868564866719744",
                         "Album News: Napalm Death, Oakenform, @Eradikator, @KamikazeZombie\n\nhttps://t.co/d9TZnVlYGT\n\n#metal #heavymetal #music #MoshvilleTimes @officialND https://t.co/A5tbK1x8Z8'",
                         "MoshTimes",
                         "MoshvilleTimes",
                         [],
                         [],
                         [])
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
