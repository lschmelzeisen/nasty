========================================================================================
NASTY Advanced Search Tweet Yielder
========================================================================================

.. image:: https://raw.githubusercontent.com/lschmelzeisen/nasty/master/assets/textlogo.png
    :alt: Logo
    :width: 420
    :height: 200
    :align: center

|

**NASTY** is a tool/library for retrieving Tweets via the Twitter Web UI.
Instead of using the `Twitter Developer API <https://developer.twitter.com/>`_ it
works by acting like a normal web browser accessing Twitter.
That is, it sends AJAX requests and parses Twitter's JSON responses.
This approach makes it substantially different from the
`other <https://github.com/bisguzar/twitter-scraper>`_
`popular <https://github.com/Jefferson-Henrique/GetOldTweets-python>`_
`crawlers <https://github.com/jonbakerfish/TweetScraper>`_ and allows for the following
features:

* Search for Tweets by keyword (and filter by latest/top/photos/videos, date of
  authorship, and language).
* Retrieve all direct replies to a Tweet.
* Retrieve all Tweets threaded under a Tweet.
* Return fully-hydrated JSON-objects of Tweets that exactly match the `extended mode of
  the developer API <https://developer.twitter.com/en/docs/tweets/tweet-updates>`_
* Operate in batch mode to execute a large set of requests, abort at any time, and rerun
  both uncompleted and failed requests.
* Transform collected Tweets into sets of Tweet-IDs for publishing datasets.
  Automatically download full Tweet information from sets of Tweet-IDs.
* Written in tested, linted, and fully type-checked Python code.

Installation
========================================================================================

**Python 3.6**, **3.7**, **3.8** and **PyPy** are currently supported.
Install via::

    $ pip install nasty

Command Line Interface
========================================================================================

To get help for the command line interface use the ``--help`` option::

    $ nasty --help
    usage: nasty [-h] [-v] [search|replies|thread|batch|idify|unidify] ...

    NASTY Advanced Search Tweet Yielder.

    Commands:
      The following commands (and abbreviations) are available, each supporting
      the help option. For example, try out `nasty search --help`.

      <COMMAND>
        search (s)         Retrieve Tweets using the Twitter advanced search.
        replies (r)        Retrieve all directly replying Tweets to a Tweet.
        thread (t)         Retrieve all Tweets threaded under a Tweet.
        batch (b)          Execute previously created batch of requests.
        idify (i, id)      Reduce Tweet-collection to Tweet-IDs (for publishing).
        unidify (u, unid)  Collect full Tweet information from Tweet-IDs (via
                           official Twitter API).

    General Arguments:
      -h, --help           Show this help message and exit.
      -v, --version        Show program's version number and exit.
      --log-level <LEVEL>  Logging level (DEBUG, INFO, WARN, ERROR.)

You can also get help for the individual sub commands.
For example, try out ``nasty search --help``.

search
----------------------------------------------------------------------------------------

You can search for Tweets about "climate change"::

    $ nasty search --query "climate change"

NASTY's output are lines of JSON objects, one per retrieved Tweet.
Each Tweet-JSON has the following format (pretty-printed and abbreviated for clarity,
many other interesting features are also available, such as referenced entities, etc.)::

    {
        "created_at": "Wed Jan 11 04:52:08 +0000 2017",
        "id_str": "8190441963...",
        "full_text": Thank you for everything..."
        "retweet_count": 795...,
        "favorite_count": 1744...,
        "reply_count": 22...,
        "lang": "en",
        "user": {
            "id_str": "15367...",
            "name": "Presi...",
            "screen_name": "POTUS...",
            "location": "Washing...",
            "description": "This is an archive...",
            ...
        },
        ...
    }

By default this returns ``TOP`` Tweets according to Twitter's own ranking rules.
Alternatively you can also request the very ``LATEST`` Tweets via::

    $ nasty search --query "climate change" --filter LATEST

Other possible values for ``--filter`` are ``PHOTOS`` and ``VIDEOS``.

By default only English Tweets are found.
For example, to instead search for German Tweets::

    $ nasty search --query "climate change" --lang "de"

Additionally, you can specifically search for Tweets created after and/or before
specific dates::

    $ nasty search --query "climate change" --since 2019-01-01 --until 2019-01-31

replies
----------------------------------------------------------------------------------------

You can fetch all direct replies to the `Tweet with ID 332308211321425920
<https://twitter.com/realDonaldTrump/status/332308211321425920>`_::

    $ nasty replies --tweet-id 332308211321425920

thread
----------------------------------------------------------------------------------------

You can fetch all Tweets threaded under the `Tweet with ID 332308211321425920
<https://twitter.com/realDonaldTrump/status/332308211321425920>`_::

    $ nasty thread --tweet-id 332308211321425920

batch
----------------------------------------------------------------------------------------

NASTY supports appending requests to a batch file instead of executing them
immediately, so that they can executed in batch mode later.
The benefits of this include being able to track the progress of a large set of
requests, aborting at any time, and rerunning both completed and failed requests.

To append a request to a batch file, use the ``--to-batch`` argument on any of
the above requests, for example::

    $ nasty search --query "climate change" --to-batch batch.jsonl

To run all files stored in a jobs file and write the output to directory ``out/``::

    $ nasty batch --batch-file batch.jsonl --results-dir out/

When this command finished a tally of successful, skippend, and failed requests is
printed.
If any request failed, you may retry execution with the same command.
Requests that succeeded will automatically be skipped.

idify / unidify
----------------------------------------------------------------------------------------

The `Twitter Developer Policy
<https://developer.twitter.com/en/developer-terms/agreement-and-policy#id8>`_ states
that for sharing collected Tweets with others, only Tweet-IDs may be (publicly)
distributed (see `Legal and Moral Considerations`_ for more information).

To transform lines of Tweet-JSON-objects into lines of Tweet-IDs, use ``nasty idify``.
For example::

    $ nasty search --query "climate change" | nasty idify > climate-change-tweet-ids.txt

To perform the reverse, that is getting full Tweet information from just Tweet-IDs, use
``nasty unidify``::

    $ cat climate-change-tweet-ids.txt | nasty unidify

Note that ``unidify`` is implemented using the `Twitter Developer API
<https://developer.twitter.com/>`_, since for this specific case, the available free API
covers all needed functionality and rate-limits are not to limiting.
Additionally, this means, that this specific functionality is officially supported by
Twitter, meaning the API should be stable over time (thus making it ideal for
reproducing shared datasets of Tweets).

The downside is that you need to apply for API keys from Twitter (see `Twitter
Developers: Getting Started
<https://developer.twitter.com/en/docs/basics/getting-started>`_).
After you have optained your keys, provide them to NASTY via the environment variables
``NASTY_CONSUMER_KEY`` and ``NASTY_CONSUMER_SECRET``.
For convenience, you may use the ``config.example.sh`` shell script to do this::

    $ cp config.example.sh config.sh
    $ # Edit config.sh to contain your consumer key and secret
    $ source config.sh

Idify/unidify also support operating on batch results (and keep meta information, that
is which Tweets were the results of which requests).
To idify batch results in directory ``out/``::

    $ nasty idify --in-dir out/ --out-dir out-idified/

To do the reverse::

    $ nasty unidify --in-dir out-idified/ --out-dir out/

Python API
========================================================================================

To fetch all Tweets about "climate change" written after 14 January 2019 in German::

    import nasty
    from datetime import datetime

    tweet_stream = nasty.Search("climate change",
                                until=datetime(2019, 1, 14),
                                lang="de").request()
    for tweet in tweet_stream:
        print(tweet.created_at, tweet.text)

Similar functionality is available in the ``nasty.Replies`` and ``nasty.Thread``
classes.
The returned ``tweet_stream`` is an `Iterable
<https://docs.python.org/3/library/typing.html#typing.Iterable>`_ of ``nasty.Tweet``\ s.

The batch functionality is available in the ``nasty.Batch`` class.
To read the output of a batch execution (for example, from ``nasty batch``) written
to directory ``out/``::

    import nasty
    from pathlib import Path

    results = nasty.BatchResults(Path("out/"))
    for entry in results:
        print("Tweets that matched query '{}' (completed at {}):"
              .format(entry.request.query, entry.completed_at))
        for tweet in results.tweets(entry):
            print("-", tweet)

A comprehensive Python API documentation is coming in the future.
For now, the existing code should be relatively easy to understand.

Legal and Moral Considerations
========================================================================================

At the time of writing, the
`Twitter Terms of Service (TOS) <https://twitter.com/en/tos>`_ specify the following of
relevance to this project:

    You may not do any of the following while accessing or using the Services: [...]
    access or search or attempt to access or search the Services by any means
    (automated or otherwise) other than through our currently available, published
    interfaces that are provided by Twitter (and only pursuant to the applicable terms
    and conditions), unless you have been specifically allowed to do so in a separate
    agreement with Twitter (NOTE: crawling the Services is permissible if done in
    accordance with the provisions of the robots.txt file, however, scraping the
    Services without the prior consent of Twitter is expressly prohibited)

The text does not detail what separates *crawling* from *scraping* but states that
obeying the ``robots.txt`` is a necessity.
These are, for the subdomains we access:

* https://mobile.twitter.com/robots.txt
* https://api.twitter.com/robots.txt

For ``mobile.twitter.com`` the URLs NASTY accesses are allowed for any user-agent but
require waiting a delay of one second between successive requests.
For ``api.twitter.com`` accessing any URL is forbidden for any user-agent, except the
``Googlebot``, who may access everything.
No crawl delay is specified here.
NASTY implements a one second delay between any URL requests (even those to
``api.twitter.com``), but because it does automatically request URLs from the latter
subdomain and because it is not the ``Googlebot``, NASTY does technically violate the
``robots.txt``.
Therefore, **NASTY does violate the Twitter TOS**.

This of course begs the question of whether it is morally justified to allow one of the
world's most wealthy companies (here, Google) to automatically retrieve all of your web
site's user-generated content while simultaneously disallowing anyone else from doing the
same thing.
Keep in mind, that Twitter is not any web site, but among other things hosts much of the
world's political discussion
(`example <https://twitter.com/realdonaldtrump/status/1213919480574812160>`_) to which,
naturally, every citizen should have free and unfiltered access.

Luckily, using NASTY is still perfectly legal in many cases:

* It is unclear (and dependent on jurisdiction) to whom the TOS apply.
  Since using NASTY does not require signing into Twitter or opening it manually in
  a web browser, a court may decide that the user never agreed to the TOS and is
  therefore not bound to its conditions.

* A jurisdiction may guarantee certain rights that can not be overruled by TOS.
  Especially common are laws that allow to for web scraping in academic and personal
  contexts.

  For example, in Germany up to 75% of any publicly accessible database (here, Twitter)
  may copied for academic research.
  For more details, see `Klawonn, T. (2019). "Urheberrechtliche Grenzen des Web Scrapings
  (Web Scraping under German Copyright Law)". Available at SSRN 3491192.
  <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3491192>`_

  Also in the United States, `some courts have affirmed the right to scrape publicly
  available information
  <http://cdn.ca9.uscourts.gov/datastore/opinions/2019/09/09/17-16783.pdf>`_.

Note, that the above does not imply that it is legal or moral to publicly share a
dataset that you created using NASTY.
Specifically, the `Twitter Developer Policy
<https://developer.twitter.com/en/developer-terms/agreement-and-policy#id8>`_ state:

    If you provide Twitter Content to third parties, including downloadable datasets of
    Twitter Content or an API that returns Twitter Content, you will only distribute or
    allow download of Tweet IDs, Direct Message IDs, and/or User IDs.

Use the ``nasty idify`` command on retrieved Tweets, before sharing them publicly.

Last, it should be mentioned that NASTY is a tool specifically created for personal and
academic contexts, where the funds to pay for enterprise access to the Twitter API are
usually not available.
If you operate in a commercial context, you should `pay for the services where possible
<https://developer.twitter.com/en/products/products-overview>`_.

For more discussion on the topic, see `Perry Stephenson (2018). "Is it okay to scrape
Twitter?" <https://perrystephenson.me/2018/08/11/is-it-okay-to-scrape-twitter/>`_

Contributing
========================================================================================

Please feel free to submit
`bug reports <https://github.com/lschmelzeisen/nasty/issues>`_ and
`pull requests <https://github.com/lschmelzeisen/nasty/pulls>`_!

There are the ``Makefile``-helpers to run the plethora of auxiliary development tools.
See ``make help`` for detailed descriptions.
The most important commands are::

    usage: make <target>

    Targets:
      help        Show this help message.
      devinstall  Install NASTY in editable mode with all test and dev dependencies (in the currently active environment).
      test        Run all tests and report test coverage.
      check       Run linters and perform static type-checking.
      format      Auto format all code.
      publish     Build and check source and binary distributions.
      clean       Remove all created cache/build files, test/coverage reports, and virtual environments.

Acknowledgements
========================================================================================

* `Raphael Menges <https://github.com/raphaelmenges>`_ designed the NASTY-bird logo.
* `Steffen Jünger <https://github.com/sjuenger>`_ and `Matthias Wellstein
  <https://github.com/mwellstein>`_ wrote the initial still HTML-based crawler
  prototype.

License
========================================================================================

Copyright 2019-2020 Lukas Schmelzeisen.
Licensed under the
`Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_.

