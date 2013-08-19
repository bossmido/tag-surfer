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
    """
    if not needle:
        return (-1, tuple())

    # `positions` is a list of positions where any characters in `needle`
    # matches in `haystack`
    positions = []
    # `boundaries` is the count of how many characters in `positions`
    # are word boundaries
    boundaries_count = 0

    # If `haystack` has only uppercase characters then it makes no sense
    # to treat an uppercase letter as a word-boundary character
    uppercase_is_word_boundary = True
    if haystack.isupper():
        uppercase_is_word_boundary = False

    needle_len = len(needle)
    needle_idx = 0
    for i in range(len(haystack)):
        if needle_idx == needle_len:
            break

        c = haystack[i]

        # smart search: consider the case only if the character of `needle`
        # is uppercase
        if smart_search and needle[needle_idx].isupper():
            cond = c == needle[needle_idx]
        else:
            cond = c.lower() == needle[needle_idx].lower()

        if cond:
            positions.append(i)
            if (i == 0 or (uppercase_is_word_boundary and c.isupper()) or
                (i > 0 and haystack[i-1] in ('-', '_'))):
                boundaries_count += 1
            needle_idx += 1

    if needle_idx == needle_len:
        return (similarity(haystack, positions, boundaries_count),
                tuple(positions))
    else:
        return (-1, tuple())


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
    positions_sum = 0
    # Generate all `positions` combinations for k = 2
    positions_len = len(positions)
    for i in range(positions_len):
        positions_sum += positions[i]
        for j in range(i, positions_len):
            if i != j:
                diffs_sum += abs(positions[i]-positions[j])
                n += 1

    len_ratio = len(haystack)/positions_len
    if boundaries_count:
        len_ratio /= (boundaries_count + 1)

    if n > 0:
        return diffs_sum/n + positions_sum/positions_len + len_ratio
    else:
        # This branch is executed when len(positions) == 1
        return positions[0] + len_ratio
