from overrides import overrides

from .conversation_retriever import ConversationRetriever
from .._util.typing_ import checked_cast
from ..request.replies import Replies


class RepliesRetriever(ConversationRetriever):
    def __init__(self, request: Replies):
        super().__init__(request)

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def request(self) -> Replies:
        return checked_cast(Replies, self._request)
