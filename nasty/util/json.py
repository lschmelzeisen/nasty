import traceback
from datetime import datetime
from typing import Any, Dict, List

from nasty.util.consts import NASTY_DATE_TIME_FORMAT


class JsonSerializedException:
    def __init__(self,
                 time: datetime,
                 type: str,
                 message: str,
                 trace: List[str]):
        self.time = time
        self.type = type
        self.message = message
        self.trace = trace

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def __eq__(self, other: Any) -> bool:
        return (type(self) == type(other)) and (self.__dict__ == other.__dict__)

    def to_json(self) -> Dict[str, Any]:
        obj = {}
        obj['time'] = self.time.strftime(NASTY_DATE_TIME_FORMAT)
        obj['type'] = self.type
        obj['message'] = self.message
        obj['trace'] = self.trace
        return obj

    @classmethod
    def from_json(cls, obj: Dict[str, Any]) -> 'JsonSerializedException':
        return cls(time=datetime.strptime(obj['time'], NASTY_DATE_TIME_FORMAT),
                   type=obj['type'],
                   message=obj['message'],
                   trace=obj['trace'])

    @classmethod
    def from_exception(cls, exception: Exception) \
            -> 'JsonSerializedException':
        return cls(time=datetime.now(),
                   type=type(exception).__name__,
                   message='{}: {}'.format(type(exception).__name__,
                                           str(exception)),
                   # rstrip/split() to be easier to read in formatted JSON.
                   trace=[frame.rstrip().split('\n') for frame in
                          traceback.format_tb(exception.__traceback__)])
