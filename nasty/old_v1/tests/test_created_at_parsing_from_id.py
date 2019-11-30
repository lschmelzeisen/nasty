#
# Copyright 2019 Lukas Schmelzeisen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest
from datetime import datetime
from unittest import TestCase

from nasty.old.tweet import Tweet


class TestCreatedAtParsingFromId(TestCase):
    def test_manually_calculated_example(self):
        self.assertEqual(
            Tweet.calc_created_at_time_from_id(123567890),
            datetime(
                year=2010,
                month=11,
                day=4,
                hour=1,
                minute=42,
                second=54,
                microsecond=686000,
            ),
        )

    def test_jason_baumgartner_calculated_example(self):
        # TODO: implement me
        self.fail()


if __name__ == "__main__":
    unittest.main()
