# coding=utf-8

import unittest

from tornado_mock.httpclient import _queries_match


class RoutesMatchTest(unittest.TestCase):
    def test_equal_queries(self):
        self.assertTrue(_queries_match('q=1', 'q=1'), 'Equal queries must match')

    def test_not_equal_queries(self):
        self.assertFalse(_queries_match('q=1', 'a=1'), 'Not equal queries must not match')

    def test_parameter_order(self):
        self.assertTrue(_queries_match('a=2&q=1', 'q=1&a=2'), 'Queries with different parameters order must match')

    def test_destination_query_is_less_specific(self):
        self.assertTrue(
            _queries_match('q=1', 'a=2&q=1'), 'More specific route must match less specific'
        )

    def test_destination_query_is_more_specific(self):
        self.assertFalse(
            _queries_match('a=2&q=1', 'q=1'), 'Less specific route must not match more specific'
        )
