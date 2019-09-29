import unittest
from datetime import date

from nasty.init import init_nasty
from nasty.search.query import Query


class TestQueryJsonConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_trump(self):
        query = Query('trump')
        self.assertEqual(query, Query.from_json(Query.to_json(query)))

    def test_trump_since_until(self):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual(query, Query.from_json(Query.to_json(query)))

    def test_trump_filter_lang(self):
        query = Query('trump', filter=Query.Filter.LATEST, lang='de')
        self.assertEqual(query, Query.from_json(Query.to_json(query)))


class TestQueryFilterJsonConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_query_filter(self):
        for filter in Query.Filter:
            self.assertEqual(filter, Query.Filter.from_json(filter.to_json()))


class TestUrlParamConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_nasty()

    def test_trump(self):
        query = Query('trump')
        self.assertEqual('trump lang:en', query.url_param)

    def test_trump_since_until(self):
        query = Query('trump', since=date(2019, 1, 1), until=date(2019, 1, 2))
        self.assertEqual('trump since:2019-01-01 until:2019-01-02 lang:en',
                         query.url_param)

    def test_trump_filter_lang(self):
        query = Query('trump', filter=Query.Filter.LATEST, lang='de')
        self.assertEqual('trump lang:de', query.url_param)


if __name__ == '__main__':
    unittest.main()
