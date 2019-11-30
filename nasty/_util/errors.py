from http import HTTPStatus

from typing_extensions import Final


class UnexpectedStatusCodeException(Exception):
    def __init__(
        self,
        url: str,
        status_code: HTTPStatus,
        *,
        expected_status_code: HTTPStatus = HTTPStatus.OK,
    ):
        self.url: Final = url
        self.status_code: Final = status_code
        self.expected_status_code: Final = expected_status_code

        super().__init__(
            "Received status code {:d} {:s} (expected {:d} {:s}) for URL "
            '"{:s}".'.format(
                self.status_code.value,
                self.status_code.name,
                self.expected_status_code.value,
                self.expected_status_code.name,
                self.url,
            )
        )
