from overrides import overrides

from .._util.typing_ import checked_cast
from ..request.search import Search
from .retriever import Retriever


class SearchRetriever(Retriever):
    def __init__(self, request: Search):
        super().__init__(request)

    @property  # type: ignore  # see https://github.com/python/mypy/issues/1362
    @overrides
    def request(self) -> Search:
        return checked_cast(Search, self._request)
