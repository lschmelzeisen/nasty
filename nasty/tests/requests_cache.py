import pickle
from logging import getLogger
from multiprocessing import Lock
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from requests import PreparedRequest, Response, Session
from requests.hooks import default_hooks

lock = Lock()


class RequestsCache:
    """Caches send requests to the web to save time running tests repeatedly."""

    class CacheKey:
        def __init__(self, request: PreparedRequest):
            if request.hooks != default_hooks():
                raise NotImplementedError('Usage of hooks not supported.')

            # Ignoring headers and cookies here since these can change between
            # calls because of Twitter session cookies, but we except the
            # results to be the same.
            self._request_repr = frozenset({
                ('_body_position', request._body_position),
                ('body', request.body),
                ('method', request.method),
                ('url', request.url),
            })

        def __hash__(self):
            return hash(self._request_repr)

        def __eq__(self, other: Any):
            return (type(self) == type(other)) \
                   and (self._request_repr == other._request_repr)

    RESOURCE_DIR = Path(__file__).parent / 'resources'
    CACHE_FILE = RESOURCE_DIR / 'requests_cache.pickle'

    def __init__(self, regenerate: bool = False):
        self._regenerate = regenerate

    def _mock_requests_send(self, orig_session_send: Callable) -> Callable:
        logger = getLogger(__name__)

        # Wrapping a callable here to have access to session in patching method.
        def f(session: Session, request: PreparedRequest, **kwargs) \
                -> Response:
            key = self.CacheKey(request)

            with lock:
                Path.mkdir(self.RESOURCE_DIR, exist_ok=True, parents=True)

                cache = {}
                if self.CACHE_FILE.exists():
                    with self.CACHE_FILE.open('rb') as fin:
                        cache = pickle.load(fin)

                response = cache.get(key)
                if response is not None:
                    logger.debug('Found cache response.')
                    if not self._regenerate:
                        return response

                    logger.debug('Regenerating cached response.')
                    cache.pop(key)

                response = orig_session_send(session, request, **kwargs)
                cache[key] = response

                with self.CACHE_FILE.open('wb') as fout:
                    pickle.dump(cache, fout, pickle.HIGHEST_PROTOCOL)

                return response

        return f

    def __call__(self, func: Callable) -> Callable:
        @patch.object(Session, 'send', self._mock_requests_send(Session.send))
        def f(*args, **kwargs):
            return func(*args, **kwargs)

        return f
