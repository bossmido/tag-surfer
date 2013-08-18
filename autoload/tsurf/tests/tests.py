# -*- coding: utf-8 -*-
"""
tests.py
~~~~~~~~

Tests for tsurf.
"""

import unittest

from tsurf.utils import search
from tsurf.ext import search as _search


# tests for the modules 'tsurf.utils.search' and 'tsurf.ext.search'
# ===========================================================================

class TestSearch(unittest.TestCase):

    def setUp(self):

        # dictionary form:
        #    input               expected output
        #   {(needle, haystack): (score: match positions), ..}

        self.search_tests = {
            ("whatever", "") : (-1, tuple()),
            ("whatever", "what") : (-1, tuple()),
            ("", "superLong_identifier") : (-1, tuple()),
            ("noticl", "superLong_identifier") : (-1, tuple()),
            ("sup", "superLong_identifier") : (60.0000, (0,1,2)),
            ("sul", "superLong_identifier") : (60.0000, (0,1,5)),
            ("sui", "superLong_identifier") : (85.0000, (0,1,10)),
            ("sud", "superLong_identifier") : (120.0000, (0,1,11)),
            ("peri", "superLong_identifier") : (92.7778, (2,3,4,10)),
            ("pong", "superLong_identifier") : (139.1667, (2,6,7,8)),
            ("plong", "superLong_identifier") : (82.6667, (2,5,6,7,8)),
        }

        self.smart_search_tests = {
            ("whatever", "") : (-1, tuple()),
            ("whatever", "what") : (-1, tuple()),
            ("", "superLong_identifier") : (-1, tuple()),
            ("noticl", "superLong_identifier") : (-1, tuple()),
            ("sup", "superLong_identifier") : (60.0000, (0,1,2)),
            ("suP", "superLong_identifier") : (-1, tuple()),
            ("sul", "superLong_identifier") : (60.0000, (0,1,5)),
            ("suL", "superLong_identifier") : (60.0000, (0,1,5)),
            ("sud", "superLong_identifier") : (120.0000, (0,1,11)),
            ("plong", "superLong_identifier") : (82.6667, (2,5,6,7,8)),
            ("pLong", "superLong_identifier") : (82.6667, (2,5,6,7,8)),
            ("pLOng", "superLong_identifier") : (-1, tuple()),
        }

    def test__search(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = _search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = _search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])


def run():
    unittest.main(module=__name__)
