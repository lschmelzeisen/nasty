import unittest
from datetime import date
from nasty.advanced_search import perform_advanced_search

from nasty.api_loader import download_api_tweets_from_html_tweets
from typing import List

from nasty.tweet import Tweet, UserMention


class Test(unittest.TestCase):
    def test_compare_ape(self):
        keyword = "ape"
        day = date(year=2017, month=11, day=23)
        language = "en"
        tweet_list = perform_advanced_search(keyword, day, language)
        api_tweets = download_api_tweets_from_html_tweets(tweet_list)
        result_dict = _compare(tweet_list, api_tweets)
        print(result_dict)
        self.assertEqual(0, result_dict["tweets_not_equal"])

    def test_compare_metal(self):
        keyword = "metal"
        day = date(year=2018, month=11, day=23)
        language = "en"
        tweet_list = perform_advanced_search(keyword, day, language)
        api_tweets = download_api_tweets_from_html_tweets(tweet_list)
        result_dict = _compare(tweet_list, api_tweets)
        print(result_dict)
        self.assertEqual(0, result_dict["tweets_not_equal"])

    def test_compare_climate(self):
        keyword = "climate"
        day = date(year=2020, month=1, day=1)
        language = "en"
        tweet_list = perform_advanced_search(keyword, day, language)
        api_tweets = download_api_tweets_from_html_tweets(tweet_list)
        result_dict = _compare(tweet_list, api_tweets)
        print(result_dict)
        self.assertEqual(-1, result_dict["tweets_not_equal"])

    def test_compare_uncommon(self):
        keyword = "fgjkdfgjhkddgjldgslövnaölreubnvöaurubvjnkaluebnvnlöauoahj" \
                  "gljgdfsjkgjlknsbnlkjfsdbgslkjghjfdnbjkdnfbjdkfgblkfn nljn" \
                  "drjklhgnjdflbrdtrjotshlgudfkjhbngbdfgjkbndlrghjkgabkncfbj"
        day = date(year=2018, month=11, day=23)
        language = "en"
        tweet_list = perform_advanced_search(keyword, day, language)
        api_tweets = download_api_tweets_from_html_tweets(tweet_list)
        result_dict = _compare(tweet_list, api_tweets)
        print(result_dict)
        self.assertEqual(-1, result_dict["tweets_not_equal"])


def _compare(html_tweets: List[Tweet], api_tweets: List[Tweet]) -> dict:
    """
    Compares the tweets out of two lists of Tweet Objects.

    The Tweets have to be modified before they are handed over to this method.
    No Modification is done by this method.

    Additionally the two lists of elements are being sorted by their ID.

    The function returns a dictionary, which stores information about the
    comparison test.
    The tweets_not_equal variable is minus one, so if no tweet gets compared
    and nothing is changed in the dict, the test will fail.

    :param html_tweets:
    Gets a list of tweet objects from advancedSearch handed over.
    :param api_tweets:
    Gets a list of tweet objects from the official API handed over.
    :return dict:
    """
    dict_result = {"tweets_equal": 0,
                   "tweets_equal_mentions": 0,
                   "tweets_not_equal": -1}

    html_tweets = _sort_by_id(html_tweets)
    api_tweets = _sort_by_id(api_tweets)

    for (html_tweet, api_tweet) in zip(html_tweets, api_tweets):
        if len(html_tweets) == len(api_tweets):
            if dict_result["tweets_not_equal"] == -1:
                dict_result["tweets_not_equal"] = 0

            result = _compare_text(html_tweet.full_text, api_tweet.full_text,
                                   html_tweet.id, api_tweet.id,
                                   html_tweet.user_mentions)
            dict_result[result] += 1

    return dict_result


def _sort_by_id(tweet_objects: List[Tweet]) -> List[Tweet]:
    """
    This method sorts a list of tweet objects by their ID's ascending.

    :param tweet_objects: List[Tweet]
    :return List[Tweet]:
    """
    data = sorted(tweet_objects, key=lambda i: i.id)

    return data


def _compare_text(html_text: str, api_text: str, html_id: str, api_id: int,
                  html_mentions: List[UserMention]) -> str:
    """
    This function compares two lists of strings (from tweets).
    The tweets of the HTML-Crawling must be unescaped of HTML Codes.
    But "<",">","&" need to be replaced again with "&lt;", "&gt;" und "&amp;"
    in order to match the results by the API.

    Additionally this method needs the ID of the html and API tweets for /
    debugging and also the mentions of the html tweet,
    for the improvised method.

    In the moment there is an improvised method, that deletes all user
    mentions, if there are more than 2.

    If there is a difference between a pair of tweets,
    the method will print their texts and ID's out.

    The method returns a string, which gives information about if the
    comparison has been successful, successful without user mentions
    or not successful.

    :param html_text:
    :param api_text:
    :param html_id:
    :param api_id:
    :param html_mentions:
    :return str:
    """
    api_id = str(api_id)
    # To convert the ID of the API to string, so that html and API ID's can be
    # compared.

    if html_id != api_id:
        raise Exception("The id's of the tweets are not the same.\n "
                        "Identifier: compare_text")

    flag_mention = 0
    for user in html_mentions:
        if "\n      others\n      \n  " in user.screen_name:
            flag_mention = 1
            list_texts = _improvised_reply(html_text, api_text, html_mentions)
            html_text = list_texts[0]
            api_text = list_texts[1]
            break

    if html_text == api_text:
        if flag_mention == 1:
            return "tweets_equal_mentions"
        else:
            return "tweets_equal"
    else:
        # Checking, if the tweets are only unequal,
        # because of the user mentions.
        [html_text, api_text] = _delete_mentions(html_text, api_text)
        if html_text == api_text:
            return "tweets_equal_mentions"
        else:
            print(
                f"_________Fail_ID: {html_id} _________\n{html_text}\n"
                f"==================\n{api_text}\n"
                f"_________UserMentions: {html_mentions}\n")

            return "tweets_not_equal"


def _delete_mentions(html_text: str, api_text: str) -> [str, str]:
    """
    This method deletes all "@mentions" in the html text and api text,
    so that they can be compared without the @mentions

    :param html_text: str
    :param api_text: str
    :return: [str,str]
    """
    html_text_edited = "Improvised tweet text:"
    for word in html_text.split():
        if "@" not in word:
            html_text_edited = html_text_edited + " " + word

    api_text_edited = "Improvised tweet text:"
    for word in api_text.split():
        if "@" not in word:
            api_text_edited = api_text_edited + " " + word

    return [html_text_edited, api_text_edited]


def _improvised_reply(html_text: str, api_text: str,
                      mentions: [str]) -> [str, str]:
    """
    This is an improvised method for swapping out @mentions in twitter tweets.
    At the moment we can not get all user mentions, if there are more than 2
    in a tweet.

    While we work on a better solution, we just delete the user mentions in the
    effected tweets.

    :param html_text: The html tweet.
    :param api_text: The API tweet.
    :param mentions: The user mentions of the tweet.
    --> This need to be deleted/in the html tweet.
    :return [str, str]:
    """
    print(
        f"Working on a better solution .... "
        f"This tweet had to be improvised\n--------------------------/"
        f"\n{api_text}\n--------------------------\n")

    """
    Working on a better solution .... This tweet had to be improvised
    @TJCobain @TJ_Cobain @TheTJStore @iScenario @itsarkheops @ZipFNM @XR_Ape I hope I win


    _________Fail_ID: 1142583459698761728_________
    @XR_Ape I hope I win
    ==================
    I hope I win

    15.07.2019 12:42
    In diesem Tweet ist ein gelöschter User als mention angeführt.
    Da wir aus der HTML Datei nicht wissen, welche User alle 
    erwähnt werden, können wir in diesem Fehlerfall nur alle 
    "@" Mentions löschen.
    """
    for mention in mentions:  # HTML Modification Part I
        # --> Deleting all mentioned users in the html text.
        # (Most importantly deleting the "others" menntion)
        html_text = html_text.replace("@" + mention.screen_name + " ", "")
        # HTML Modification
        html_text = html_text.replace(mention.screen_name + " ", "")
        # HTML Modification

    splitted_text = html_text.split(" ")  # HTML Modification Part II
    sum_splitted = []

    for text in splitted_text:
        # HTML Modification ---> Deleting all "@" mentions. (unfortunately)
        if "@" in text:
            text = ""
        else:
            sum_splitted.append(text)
    html_text = " ".join(sum_splitted)
    # For the HTML it works fine.

    splitted_text_2 = api_text.split(" ")
    # API Modification Start
    sum_splitted_2 = []

    for text in splitted_text_2:
        # API Modification  --> Deleting all "@" mentions. (unfortunately)
        if "@" in text:
            text = ""
        else:
            sum_splitted_2.append(text)
    api_text = " ".join(sum_splitted_2)  # For the API it works fine.

    return [html_text, api_text]


if __name__ == '__main__':
    unittest.main()
