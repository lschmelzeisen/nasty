import unittest
from datetime import datetime
from unittest import TestCase

from nasty.tweet import Tweet


class TestCreatedAtParsingFromId(TestCase):
    def test_manually_calculated_example(self):
        self.assertEqual(Tweet.calc_created_at_time_from_id(123567890),
                         datetime(year=2010, month=11, day=4,
                                  hour=1, minute=42, second=54,
                                  microsecond=686000))

    def test_jason_baumgartner_calculated_example(self):
        # TODO: implement me
        self.fail()


if __name__ == '__main__':
    unittest.main()
