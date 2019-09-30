import traceback
from datetime import datetime
from typing import Dict

from nasty.util.consts import NASTY_DATE_TIME_FORMAT


class JsonSerializedException:
    def __init__(self, time: datetime, message: str, trace: str):
        self.time = time
        self.message = message
        self.trace = trace

    def __repr__(self):
        return type(self).__name__ + repr(self.to_json())

    def to_json(self) -> Dict:
        return {
            'time': self.time.strftime(NASTY_DATE_TIME_FORMAT),
            'message': self.message,
            'trace': self.trace,
        }

    @classmethod
    def from_json(cls, obj: Dict) -> 'JsonSerializedException':
        return cls(time=datetime.strptime(obj['time'], NASTY_DATE_TIME_FORMAT),
                   message=obj['message'],
                   trace=obj['trace'])

    @classmethod
    def from_exception(cls, exception: Exception) \
            -> 'JsonSerializedException':
        return cls(time=datetime.now(),
                   message='{}: {}'.format(type(exception).__name__,
                                           str(exception)),
                   trace=traceback.format_tb(exception.__traceback__))
