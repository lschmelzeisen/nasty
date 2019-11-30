from overrides import overrides

from .conversation_retriever import ConversationRetriever
from .._util.typing_ import checked_cast
from ..request.thread import Thread


class ThreadRetriever(ConversationRetriever):
    def __init__(self, request: Thread):
        super().__init__(request)

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def request(self) -> Thread:
        return checked_cast(Thread, self._request)
