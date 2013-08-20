# -*- coding: utf-8 -*-
"""
tsurf.utils.search
~~~~~~~~~~~~~~~~~~

This module defines the search function used by the Finder class
for searching tags that match the user search query.
"""

from __future__ import division


def search(needle, haystack, smart_search):
    """To search for `needle` in `haystack`.

    Returns a tuple of two elements: a number and another tuple.
    The number is a measure of the similarity between `needle` and `haystack`,
    whereas the other tuple contains the positions where the match occurs in
    `haystack`.

    If there are multiple matches, the one with the highest similarity
    (lowest value) is returned.
    """
    if not needle:
        return (-1, tuple())

    # If `haystack` has only uppercase characters then it makes no sense
    # to treat an uppercase letter as a word-boundary character
    uppercase_is_word_boundary = True
    if haystack.isupper():
        uppercase_is_word_boundary = False

    # `possible_matches` keeps track of all possible matches of `needle`
    # along `haystack`
    possible_matches = []

    for i, c in enumerate(haystack):

        # add a new active match if we encounter along `haystack`
        # a possible "start of match" for `needle`
        if match(c, needle[0], smart_search):
            possible_matches.append(
                {"needle": needle, "positions": [], "boundaries_count": 0})

        for possible_match in possible_matches:

            if not possible_match["needle"]:
                continue

            if match(c, match["needle"][0], smart_search):

                possible_match["positions"].append(i)

                if (i == 0 or (uppercase_is_word_boundary and c.isupper()) or
                    (i > 0 and haystack[i-1] in ('-', '_'))):
                    possible_match["boundaries_count"] += 1

                possible_match["needle"] = possible_match["needle"][1:]

    matches = filter(lambda m: not m["needle"], possible_matches)
    if matches:
        return min((similarity(haystack, m["positions"], m["boundaries_count"]), tuple(m["positions"]))
                    for m in matches)
    else:
        return (-1, tuple())


def match(c1, c2, smart_search):
    """To check if the two characters `c1` and `c2` are equals.

    smart_search == True: consider the case only if `c2` is uppercase.
    """
    if smart_search and c2.isupper():
        return c1 == c2
    else:
        return c1.lower() == c2.lower()


def similarity(haystack, positions, boundaries_count):
    """ To compute the similarity between two strings given `haystack` and the
    positions where `needle` matches in `haystack`.

    Returns a number that indicate the similarity between the two strings.
    The lower it is, the more similar the two strings are.
    """
    if not positions:
        return -1

    n = 0
    diffs_sum = 0
    # Generate all `positions` combinations for k = 2
    positions_len = len(positions)
    for i in range(positions_len):
        for j in range(i, positions_len):
            if i != j:
                diffs_sum += abs(positions[i]-positions[j])
                n += 1

    len_ratio = len(haystack)/positions_len
    if boundaries_count:
        len_ratio /= (boundaries_count + 1)

    if n > 0:
        return diffs_sum/n + len_ratio
    else:
        # This branch is executed when len(positions) == 1
        return positions[0] + len_ratio
