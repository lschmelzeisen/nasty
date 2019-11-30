import pytest

from nasty.request.replies import Replies
from nasty.request.request import Request
from nasty.request.search import Search
from nasty.request.thread import Thread


@pytest.mark.parametrize(
    "req",
    [
        Search("Trump"),
        Replies("332308211321425920", max_tweets=None),
        Thread("332308211321425920", max_tweets=123, batch_size=456),
    ],
    ids=repr,
)
def test_json_conversion(req: Request) -> None:
    assert req == req.from_json(req.to_json())
