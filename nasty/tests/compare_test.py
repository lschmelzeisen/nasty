import unittest
import sys
import gzip
import os

from nasty.__main__ import main
from nasty.api_loader import load
from typing import List

from nasty.tweet import Tweet, UserMention


class Test(unittest.TestCase):
    def test_compare_ape(self):
        sys.argv.append("-k")
        sys.argv.append("ape")
        sys.argv.append("-t")
        sys.argv.append("2019-01-01")
        sys.argv.append("2019-01-02")
        sys.argv.append("--log-level")
        sys.argv.append("INFO")
        main(sys.argv[1:])
        # main(["-k", "ape", "-t", "2019-01-01", "2019-01-02"]) Alternative way
        execute_compare_test()


def execute_compare_test() -> bool:
    todo_path = "nasty-twitter-crawler/nasty/out/"
    for filename in os.listdir(todo_path):
        if "data.jsonl.gz" in filename:
            from_filename = "nasty-twitter-crawler/nasty/out/" + filename
            to_filename = "nasty-twitter-crawler/nasty/tests/api_data/" + filename
            load(from_filename, to_filename)
            with gzip.open(from_filename, "rt") as html:
                with gzip.open(to_filename, "rt") as api:
                    if not compare(html.read(), api.read()):
                        return False
                        # The crawled data is not deleted in this case,
                        # so that one can debug it.
                    else:
                        os.remove(from_filename)
                        os.remove(to_filename)
    return True


def compare(html_tweets: List[Tweet], api_tweets: List[Tweet]) -> None:
    """
    Compares the tweets out of two lists of Tweet Objects.

    The Tweets have to be modified before they are handed over to this method.
    No Modification is done by this method.

    Additionally the two lists of elements are being sorted by their ID.

    :param html_tweets: Gets a list of tweet objects from advancedSearch handed over.
    :param api_tweets: Gets a list of tweet objects from the official API handed over.
    :return None:
    """

    html_tweets = sort_by_id(html_tweets)
    api_tweets = sort_by_id(api_tweets)

    for (html_tweet, api_tweet) in zip(html_tweets, api_tweets):
        if not (compare_text(html_tweet.full_text, api_tweet.full_text,
                             html_tweet.id_str, api_tweet.id_str,
                             html_tweet.user_mentions)):
            return False
    return True


def sort_by_id(tweet_objects: [Tweet]) -> List:
    """
    This method sorts a list of tweet objects by their ID's ascending.

    :param tweet_objects:
    :return None:
    """
    data = list()
    print(tweet_objects)

    for line in tweet_objects:
        data.append(line)
    data.sort(key=lambda k: k.id_str)

    return data


def compare_text(html_text: str, api_text: str, html_id: str, api_id: str,
                 html_mentions: List[UserMention]) -> "Boolean":
    """
    This function compares two lists of strings (from tweets).
    The tweets of the HTML-Crawling must be unescaped of HTML Codes.
    But "<",">","&" need to be replaced again with "&lt;", "&gt;" und "&amp;"
    in order to match the results by the API.

    Additionally this method needs the ID of the html and API tweets for /
    debugging and also the mentions of the html tweet, for the improvised method.

    In the moment there is an improvised method, that deletes all user
    mentions, if there are more than 2.

    If there is a difference between a pair of tweets,
    the method will print their texts and ID's out.

    :param html_text:
    :param api_text:
    :param html_id:
    :param api_id:
    :param html_mentions:
    :return None:
    """
    if html_id != api_id:
        raise Exception("The id's of the tweets are not the same.\n Identifier: compare_text")

    for user in html_mentions:
        if "\n      others\n      \n  " in user.screen_name:
            list_texts = improvised_reply(html_text, api_text, html_mentions)
            html_text = list_texts[0]
            api_text = list_texts[1]
            break

    if html_text != api_text:
        print(
            f"_________Fail_ID: {html_id} _________\n{html_text}\n==================\n{api_text}\n")
        return False
    else:
        return True


def improvised_reply(html_text: str, api_text: str, mentions: [str]) -> [str, str]:
    """
    This is an improvised method for swapping out "@" mentions in twitter tweets.
    At the moment we can not get all user mentions, if there are more than 2
    in a tweet.

    While we work on a better solution, we just delete the user mentions in the
    effected tweets.

    :param html_text: The html tweet.
    :param api_text: The API tweet.
    :param mentions: The user mentions of the tweet. --> This need to be deleted/
    in the html tweet.
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
    Da wir aus der HTML Datei nicht wissen, welche User alle erwähnt werden, können wir in
    diesem Fehlerfall nur alle "@" Mentions löschen.
    """

    for mention in mentions:  # HTML Modification Part I
        # --> Deleting all mentioned users in the html text.
        # (Most importantly deleting the "others" menntion)
        html_text = html_text.replace("@" + mention.screen_name + " ", "")  # HTML Modification
        html_text = html_text.replace(mention.screen_name + " ", "")  # HTML Modification

    splitted_text = html_text.split(" ")  # HTML Modification Part II
    sum_splitted = []

    for text in splitted_text:  # HTML Modification ---> Deleting all "@" mentions. (unfortunately)
        if "@" in text:
            text = ""
        else:
            sum_splitted.append(text)
    html_text = " ".join(sum_splitted)  # For the HTML it works fine.

    splitted_text_2 = api_text.split(" ")  # API Modification Start
    sum_splitted_2 = []

    for text in splitted_text_2:  # API Modification  --> Deleting all "@" mentions. (unfortunately)
        if "@" in text:
            text = ""
        else:
            sum_splitted_2.append(text)
    api_text = " ".join(sum_splitted_2)  # For the API it works fine.

    return [html_text, api_text]


if __name__ == '__main__':
    unittest.main()
