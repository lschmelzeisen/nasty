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

from datetime import datetime, timezone

from nasty.tweet.tweet import Tweet, User

tweet_jsons = {
    # Tweet accessed via Search API on 2019-09-27
    "1142944425502543875": {
        "created_at": "Sun Jun 23 23:56:00 +0000 2019",
        "id": 1142944425502543875,
        "id_str": "1142944425502543875",
        "full_text": (
            "It is obvious that Mr. Trump is a terrible judge of character. His "
            "nominees for various high level cabinet positions have been unqualified, "
            "unforthcoming, or engaged in behavior unbecoming of a public servant. His "
            "standards should not be our standards. https://t.co/CHuQqFs5EX"
        ),
        "truncated": False,
        "display_text_range": [0, 276],
        "entities": {
            "hashtags": [],
            "symbols": [],
            "user_mentions": [],
            "urls": [
                {
                    "url": "https://t.co/CHuQqFs5EX",
                    "expanded_url": (
                        "https://www.washingtonpost.com/opinions/global-opinions/the-wh"
                        "ite-house-is-allowing-personal-scandals-to-become-national-emb"
                        "arrassments/2019/06/20/122f4e84-938b-11e9-b570-6416efdc0803_st"
                        "ory.html?utm_term=.790cde3fee18"
                    ),
                    "display_url": "washingtonpost.com/opinions/globa…",
                    "indices": [253, 276],
                }
            ],
        },
        "source": (
            '<a href="https://sproutsocial.com" rel="nofollow">Sprout Social</a>"'
        ),
        "in_reply_to_status_id": None,
        "in_reply_to_status_id_str": None,
        "in_reply_to_user_id": None,
        "in_reply_to_user_id_str": None,
        "in_reply_to_screen_name": None,
        "geo": None,
        "coordinates": None,
        "place": None,
        "contributors": None,
        "is_quote_status": False,
        "retweet_count": 1109,
        "favorite_count": 3709,
        "reply_count": 241,
        "conversation_id": 1142944425502543875,
        "conversation_id_str": "1142944425502543875",
        "favorited": False,
        "retweeted": False,
        "possibly_sensitive": False,
        "possibly_sensitive_editable": True,
        "lang": "en",
        "supplemental_language": None,
        "user": {
            "id": 949934436,
            "id_str": "949934436",
            "name": "Tom Steyer",
            "screen_name": "TomSteyer",
            "location": "San Francisco, CA",
            "description": (
                "Husband & father. Former investor. Signed The Giving Pledge to donate "
                "the majority of my net worth in my lifetime. He/him. 2020 Democrat "
                "for president."
            ),
            "url": "https://t.co/n1r4Xd6IXH",
            "entities": {
                "url": {
                    "urls": [
                        {
                            "url": "https://t.co/n1r4Xd6IXH",
                            "expanded_url": "https://go.tomsteyer.com/ts2020",
                            "display_url": "go.tomsteyer.com/ts2020",
                            "indices": [0, 23],
                        }
                    ]
                },
                "description": {"urls": []},
            },
            "protected": False,
            "followers_count": 245080,
            "fast_followers_count": 0,
            "normal_followers_count": 245080,
            "friends_count": 1086,
            "listed_count": 2764,
            "created_at": "Thu Nov 15 15:28:50 +0000 2012",
            "favourites_count": 3535,
            "utc_offset": None,
            "time_zone": None,
            "geo_enabled": False,
            "verified": True,
            "statuses_count": 8513,
            "media_count": 812,
            "lang": None,
            "contributors_enabled": False,
            "is_translator": False,
            "is_translation_enabled": False,
            "profile_background_color": "666666",
            "profile_background_image_url": (
                "http://abs.twimg.com/images/themes/theme2/bg.gif"
            ),
            "profile_background_image_url_https": (
                "https://abs.twimg.com/images/themes/theme2/bg.gif"
            ),
            "profile_background_tile": False,
            "profile_image_url": (
                "http://pbs.twimg.com/profile_images/1148571376355119104/"
                "EqZutNij_normal.png"
            ),
            "profile_image_url_https": (
                "https://pbs.twimg.com/profile_images/1148571376355119104/"
                "EqZutNij_normal.png"
            ),
            "profile_banner_url": (
                "https://pbs.twimg.com/profile_banners/949934436/1562688733"
            ),
            "profile_image_extensions_media_color": {
                "palette": [
                    {"rgb": {"red": 23, "green": 44, "blue": 73}, "percentage": 50.97},
                    {
                        "rgb": {"red": 202, "green": 158, "blue": 142},
                        "percentage": 29.1,
                    },
                    {"rgb": {"red": 112, "green": 77, "blue": 69}, "percentage": 11.04},
                    {
                        "rgb": {"red": 213, "green": 224, "blue": 232},
                        "percentage": 7.46,
                    },
                    {"rgb": {"red": 18, "green": 39, "blue": 69}, "percentage": 0.3},
                ]
            },
            "profile_image_extensions_alt_text": None,
            "profile_image_extensions_media_availability": None,
            "profile_image_extensions": {
                "mediaStats": {"r": {"missing": None}, "ttl": -1}
            },
            "profile_banner_extensions_media_color": {
                "palette": [
                    {
                        "rgb": {"red": 179, "green": 154, "blue": 132},
                        "percentage": 28.83,
                    },
                    {"rgb": {"red": 71, "green": 48, "blue": 42}, "percentage": 28.18},
                    {
                        "rgb": {"red": 174, "green": 186, "blue": 222},
                        "percentage": 17.33,
                    },
                    {
                        "rgb": {"red": 115, "green": 112, "blue": 117},
                        "percentage": 11.66,
                    },
                    {"rgb": {"red": 155, "green": 92, "blue": 87}, "percentage": 1.96},
                ]
            },
            "profile_banner_extensions_alt_text": None,
            "profile_banner_extensions_media_availability": None,
            "profile_banner_extensions": {
                "mediaStats": {"r": {"missing": None}, "ttl": -1}
            },
            "profile_link_color": "2802A3",
            "profile_sidebar_border_color": "000000",
            "profile_sidebar_fill_color": "FFEBD6",
            "profile_text_color": "605CBA",
            "profile_use_background_image": True,
            "has_extended_profile": False,
            "default_profile": False,
            "default_profile_image": False,
            "pinned_tweet_ids": [1175916938305949696],
            "pinned_tweet_ids_str": ["1175916938305949696"],
            "has_custom_timelines": True,
            "can_dm": None,
            "can_media_tag": None,
            "following": None,
            "follow_request_sent": None,
            "notifications": None,
            "muting": None,
            "blocking": None,
            "blocked_by": None,
            "want_retweets": None,
            "advertiser_account_type": "promotable_user",
            "advertiser_account_service_levels": [
                "dso",
                "media_studio",
                "smb",
                "dso",
                "mms",
                "smb",
                "dso",
            ],
            "profile_interstitial_type": "",
            "business_profile_state": "none",
            "translator_type": "none",
            "followed_by": None,
            "require_some_consent": False,
        },
    }
}


def test_1142944425502543875() -> None:
    tweet = Tweet(tweet_jsons["1142944425502543875"])
    assert (
        datetime(
            year=2019,
            month=6,
            day=23,
            hour=23,
            minute=56,
            second=0,
            tzinfo=timezone.utc,
        )
        == tweet.created_at
    )
    assert "1142944425502543875" == tweet.id
    assert (
        "It is obvious that Mr. Trump is a terrible judge of character. His nominees "
        "for various high level cabinet positions have been unqualified, "
        "unforthcoming, or engaged in behavior unbecoming of a public servant. His "
        "standards should not be our standards. https://t.co/CHuQqFs5EX" == tweet.text
    )
    assert "https://twitter.com/TomSteyer/status/1142944425502543875" == tweet.url
    assert tweet == Tweet.from_json(tweet.to_json())

    user = tweet.user
    assert "949934436" == user.id
    assert "Tom Steyer" == user.name
    assert "TomSteyer" == user.screen_name
    assert "https://twitter.com/TomSteyer" == user.url
    assert user == User.from_json(user.to_json())
