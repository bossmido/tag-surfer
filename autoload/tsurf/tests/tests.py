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
            ("whatever", "androidManifest") : (-1, tuple()),
            ("", "androidManifest") : (-1, tuple()),
            ("am", "androidManifest") : (9.5, (0,7)),
            ("ma", "androidManifest") : (4.75, (7,8)),
            ("ama", "androidManifest") : (7, (0,7,8)),
            ("aMa", "androidManifest") : (7, (0,7,8)),
            ("amA", "androidManifest") : (7, (0,7,8)),
            ("man", "androidManifest") : (3.8333, (7,8,9)),
            ("ani", "androidManifest") : (5.8333, (0,1,5)),
            ("anif", "androidManifest") : (5.4167, (8,9,10,11)),
            ("ai", "androidManifest") : (8.75, (0,5)),
            ("aif", "androidManifest") : (7, (8,10,11)),
        }

        self.smart_search_tests = {
            ("", "androidManifest_Smart") : (-1, tuple()),
            ("am", "androidManifest_Smart") : (10.5, (0,7)),
            ("ma", "androidManifest_Smart") : (6.25, (7,8)),
            ("mar", "androidManifest_Smart") : (8.3333, (17,18,19)),
            ("ama", "androidManifest_Smart") : (7.6667, (0,7,8)),
            ("aMa", "androidManifest_Smart") : (7.6667, (0,7,8)),
            ("amA", "androidManifest_Smart") : (-1, tuple()),
            ("aMA", "androidManifest_Smart") : (-1, tuple()),
            ("ams", "androidManifest_Smart") : (11, (0,7,13)),
            ("amS", "androidManifest_Smart") : (12.4167, (0,7,16)),
            ("man", "androidManifest_Smart") : (4.8333, (7,8,9)),
            ("ani", "androidManifest_Smart") : (6.8333, (0,1,5)),
            ("anif", "androidManifest_Smart") : (6.9167, (8,9,10,11)),
            ("ai", "androidManifest_Smart") : (10.25, (0,5)),
            ("aif", "androidManifest_Smart") : (9, (8,10,11)),
        }

    def test__search(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = search.search(needle, haystack, False)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = _search.search(needle, haystack, False)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = _search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])


def run():
    unittest.main(module=__name__)
