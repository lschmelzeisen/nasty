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
That is sends AJAX requests and parses Twitter's JSON responses.
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

Python **3.6+** is required.
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

To fetch all Tweets about "climate change" written after 14 December 2019 in German::

    import nasty
    from datetime import datetime

    tweet_stream = nasty.Search("climate change",
                                until=datetime(2019, 1, 14),
                                lang="de")
    for tweet in tweet_stream:
        print(tweet.created_at, tweet.text)

Similar functionality is available in the ``nasty.Replies`` and ``nasty.Thread``
classes.
The returned ``tweet_stream`` is an `Iterable
<https://docs.python.org/3/library/typing.html#typing.Iterable>`_ of ``nasty.Tweet``\ s.
The executor functionality is available in the ``nasty.RequestExecutor`` class.

A comprehensive Python API documentation is coming in the future, but the code should
be easy to understand.

Contributing
========================================================================================

Please feel free to submit
`bug reports <https://github.com/lschmelzeisen/nasty/issues>`_ and
`pull requests <https://github.com/lschmelzeisen/nasty/pulls>`_!

`Pipenv <https://pipenv.kennethreitz.org/>`_ is used for managing the Python environment
and tracking dependencies.
After its installation you can use the ``MAKEFILE``-helpers to run the plethora of
axuiliary development tools.

* ``make dev-environ`` to create a new virtual environment for Python and install all
  development dependencies.
* ``make test`` to run all tests and report test coverage.
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

