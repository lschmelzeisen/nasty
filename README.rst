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

* Search for tweets by keyword (and filter by latest/top/photos/videos, date of
  authorship, and language).
* Retrieve all direct replies to a Tweet.
* Retrieve all Tweets threaded under a Tweet.
* Return fully-hydrated JSON-objects of Tweets that exactly match the `extended mode of
  the developer API <https://developer.twitter.com/en/docs/tweets/tweet-updates>`_
* Operate in batch mode to run a large set of requests, abort at any time, and rerun
  both uncompleted and failed requests.
* Written in tested and fully type-checked Python code.

Installation
========================================================================================

**Python 3.6**, **3.7**, **3.8** and **PyPy** are currently supported.
Install via::

    pip install nasty

Command Line Interface
========================================================================================

To get help for the command line interface use the ``--help`` option::

    $ nasty --help
    usage: nasty [-h] [-v] [search|replies|thread|executor] ...

    NASTY Advanced Search Tweet Yielder.

    Commands:
      <COMMAND>
        search (s)         Retrieve Tweets using the Twitter advanced search.
        replies (r)        Retrieve all directly replying Tweets to a Tweet.
        thread (t)         Retrieve all Tweets threaded under a Tweet.
        executor (e)       Execute previously submitted requests.

    General Arguments:
      -h, --help           Show this help message and exit.
      -v, --version        Show program's version number and exit.
      --log-level <LEVEL>  Logging level (DEBUG, INFO, WARN, ERROR.)

You can also get help for the individual sub commands, that is via ``nasty search
--help``, etc.

Search
----------------------------------------------------------------------------------------

You can search for Tweets about "climate change"::

    $ nasty search --query "climate change"

By default this returns ``TOP`` tweets according to Twitter's own ranking rules.
Alternatively you can also request the very ``LATEST`` Tweets via::

    $ nasty search --query "climate change" --filter LATEST

Other possible values for ``--filter`` are ``PHOTOS`` and ``VIDEOS``.

By default only English tweets are found.
For example, to instead search for German Tweets::

    $ nasty search --query "climate change" --lang "de"

Additionally, you can specifically search for Tweets created after and/or before
specific dates::

    $ nasty search --query "climate change" --since 2019-01-01 --until 2019-01-31

Replies
----------------------------------------------------------------------------------------

You can fetch all direct replies to the `Tweet with ID 332308211321425920
<https://twitter.com/realDonaldTrump/status/332308211321425920>`_::

    $ nasty replies --tweet-id 332308211321425920

Thread
----------------------------------------------------------------------------------------

You can fetch all Tweets threaded under the `Tweet with ID 332308211321425920
<https://twitter.com/realDonaldTrump/status/332308211321425920>`_::

    $ nasty thread --tweet-id 332308211321425920

Executor
----------------------------------------------------------------------------------------

NASTY further supports writing requests to a jobs file to be executed in batch mode
later.
The benefits of this include being able to track the progress of a large set of
requests, aborting at any time, and rerunning both completed and failed requests.
The mechanism for this is called the executor in NASTY.

To write down a request to a jobs file, use the ``--to-executor`` argument on any of
the above requests, for example::

    $ nasty search --query "climate change" --to-executor jobs.jsonl

To run all files stored in a jobs file and write the output to directory ``out``::

    $ nasty executor --executor-file jobs.jsonl --out-dir out/

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
The executor functionality is available in the ``nasty.RequestExecutor`` class.

A comprehensive Python API documentation is coming in the future, but the code should
be easy to understand.

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

Note, that the above does not imply that it is legal or moral to publicly share a
dataset that you created using NASTY.
Specifically, the `Twitter Developer Policy
<https://developer.twitter.com/en/developer-terms/agreement-and-policy#id8>`_ state:

    If you provide Twitter Content to third parties, including downloadable datasets of
    Twitter Content or an API that returns Twitter Content, you will only distribute or
    allow download of Tweet IDs, Direct Message IDs, and/or User IDs.

A feature that automatically removes anything but IDs from crawled output is in the
works for NASTY.

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

There are the ``Makefile``-helpers to run the plethora of axuiliary development tools:

* ``make venv`` to create a new virtual environment using Python 3.6 in `./.venv`.
  Activate it with ``. .venv/bin/activate``.
* ``make devinstall`` to install nasty in editable mode with all test and dev
  dependencies.
* ``make test`` to run all tests and report test coverage.
* ``make test-tox`` to run all tests against all supported Python versions and run
  linters.
* ``make check`` to run linters and perform static type-checking.
* ``make format`` to format all source code according to the project guidelines.
* ``make publish`` to build the source and binary distributions and upload to `TestPyPI
  <https://test.pypi.org/>`_.
* ``make clean`` to remove all generated files.

Acknowledgements
========================================================================================

* `Raphael Menges <https://github.com/raphaelmenges>`_ designed the NASTY-bird logo.
* `Steffen Jünger <https://github.com/sjuenger>`_ and `Matthias Wellstein
  <https://github.com/mwellstein>`_ wrote the initial still HTML-based crawler
  prototype.

License
========================================================================================

Copyright 2019 Lukas Schmelzeisen.
Licensed under the
`Apache License, Version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>`_.

