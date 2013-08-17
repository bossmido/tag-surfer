# -*- coding: utf-8 -*-
"""
tests.py
~~~~~~~~

Tests for tsurf.
"""

from __future__ import division
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

        self.fuzzy_search_tests = {
            ("whatever", "") : (-1, tuple()),
            ("whatever", "what") : (-1, tuple()),
            ("", "superLong_identifier") : (-1, tuple()),
            ("noticl", "superLong_identifier") : (-1, tuple()),
            ("sup", "superLong_identifier") : (9, (0,1,2)),
            ("sul", "superLong_identifier") : (12, (0,1,5)),
            ("spot", "superLong_identifier") : (18.1667, (0,2,6,14)),
            ("if", "superLong_identifier") : (29, (10,16)),
        }

        self.smart_search_tests = {
            ("whatever", "") : (-1, tuple()),
            ("whatever", "what") : (-1, tuple()),
            ("", "superLong_identifier") : (-1, tuple()),
            ("noticl", "superLong_identifier") : (-1, tuple()),
            ("sup", "superLong_identifier") : (9, (0,1,2)),
            ("sul", "superLong_identifier") : (12, (0,1,5)),
            ("spot", "superLong_identifier") : (-1, tuple()),
            ("if", "superLong_identifier") : (-1, tuple()),
            ("peri", "superLong_identifier") : (13.9167, (2,3,4,10)),
            ("Li", "superLong_identifier") : (22.5, (5,10)),
        }

    def test__fuzzy_search(self):
        for input, expected in self.fuzzy_search_tests.items():
            score, positions = search.fuzzy_search(*(input))
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__smart_search(self):
        for input, expected in self.smart_search_tests.items():
            score, positions = search.smart_search(*(input))
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__fuzzy_search_ext(self):
        for input, expected in self.fuzzy_search_tests.items():
            score, positions = _search.fuzzy_search(*(input))
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__smart_search_ext(self):
        for input, expected in self.smart_search_tests.items():
            score, positions = _search.smart_search(*(input))
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])


def run():
    unittest.main(module=__name__)
