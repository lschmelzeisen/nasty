import html
from typing import List


def html_to_api_converter(full_text: str,
                          urls: List["TweetURLMapping"],
                          user_mentions: List["UserMention"],
                          screen_name: str) \
        -> str and List["TweetURLMapping"] and List["UserMention"]:
    """
    This method converts a tweet text from the advanced search method, to a
    lookalike tweet text of the official twitter API.

    Therefore all the external links have to be replaced with the "t.co" links of
    twitter.

    And the user mentions have to be inserted into the html tweet.
    --> This needs to be done with caution, because the user mentions could also
    be the author himself or the mention could be placed inside the tweet and not
    at the beginning of the tweet.

    In both cases, we do not want to add the mention, due to similarities with
    the API output.

    :param full_text: the text of the Tweet
    :param urls: all urls in the tweet, as TweetURLMapping object
    :param user_mentions: all users mentioned in the tweet or replyed to, as UserMention object
    :param screen_name: the authors screen_name (@author)
    :return: the modified string, the modifed urls and modified user_mentions (only indices changed)
    """

    user_mentions.reverse()

    while full_text and full_text[
        0] == " ":  # lstrip ersetzem  / pprint() für komplexe dateien / replace --- "1" --> nochmal drüberschauen
        full_text = full_text[1:]
    for url in urls:
        full_text = full_text.replace(url.display_url, url.url, 1)
    for user_mention in user_mentions:
        if user_mention.screen_name != screen_name and not user_mention.id_str:
            # Unsure about the functionality. Some tweets are wrong.
            if ("@" + user_mention.screen_name) not in full_text:
                full_text = "@" + user_mention.screen_name + " " + full_text

    for url in urls:
        url.indices = get_indices(url.url, full_text)
    for user_mention in user_mentions:
        if user_mention.id_str:
            user_mention.indices = get_indices("@" + user_mention.screen_name, full_text)
    full_text = mod_string_unescape(full_text)
    return full_text, urls, user_mentions


def mod_string_unescape(text: str) -> str:
    """
    This method unescapes html codes of a given string.
    But adds &lt;, &gt; and &amp; , due to match the output of the API
    & needs to be escaped first, since the others contain &.

    :param text:
    :return str:
    """
    text = html.unescape(text)
    text = text.replace("＠", "@")
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    return text


def get_indices(text, full_text):
    start = full_text.index(text)
    return start, start + len(text)
