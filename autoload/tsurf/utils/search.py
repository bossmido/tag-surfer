# -*- coding: utf-8 -*-
"""
tsurf.utils.search
~~~~~~~~~~~~~~~~~~

This module defines search functions used by the Finder class
for searching tags that match the user search query.
"""

from __future__ import division


def fuzzy_search(needle, haystack):
    """To returns the positions at which each character in `needle` matches
    in `haystack`."""
    if not needle:
        return (-1, tuple())

    positions = []
    for i, c in enumerate(haystack):
        if not needle:
            break
        if c.lower() == needle[0].lower():
            positions.append(i)
            needle = needle[1:]

    if not needle:
        return (compute_score(haystack, positions), tuple(positions))
    else:
        return (-1, tuple())


def smart_search(needle, haystack, start=-1, positions=None):
    """To returns the positions at which each character in `needle` matches
    in `haystack`.

    How it works:

      This function implements a mix of fuzzy and a naive
      case-insensitive search.
      A match can start everywhere and can be "splitted" among different
      tokens. A token is:

        - Any string subsequence tha starts at position 0.
        - Any string subsequence that starts with an uppercase letter.
        - Any string subsequence that starts after any of the
          characters ' ', '_', '-', '.'

    Examples:

      >>> _match_positions("hello", "Hello world")
      [0,1,2,3,4]  # [h][e][l][l][o] world

      >>> _match_positions("hew", "HelloWorld")
      [0,1,5]  # [H][e]llo[W]orld

      >>> _match_positions("hwor", "Hello_world")
      [0,6,7,8]  # [H]ello_[w][o][r]ld

      >>> _match_positions("hor", "Hello_world")
      []  # Hello_world

      >>> _match_positions("llwo", "Hello world")
      [2,3,6,7]  # He[l][l]o [w][o]rld
    """
    if positions is None:
        positions = []

    if not needle or start >= len(haystack)-1:
        return (-1, tuple())

    a_token_starts = True
    last_successful_match = -1
    _needle = needle

    for i, c in enumerate(haystack):

        if i <= start:
            continue

        if not _needle:
            break

        if (c.lower() == _needle[0].lower()
            and (not positions or i-1 in positions or a_token_starts)):
            last_successful_match = i
            positions.append(i)
            _needle = _needle[1:]

        a_token_starts = False

        # Note about the `not haystack.isupper()` check.
        # This checks if `haystack` contains only uppercase letters.
        # If this is the case, then we do not consider un upeprcase letter
        # as the start of a new token.

        cond1 = c in ('_', '-', '.')
        cond2 = i < len(haystack)-1 and haystack[i+1].isupper()
        if cond1 or (cond2 and not haystack.isupper()):
            a_token_starts = True

    if not _needle:
        return (compute_score(haystack, positions), tuple(positions))
    elif last_successful_match > -1:
        return smart_search(needle, haystack, last_successful_match, positions)
    else:
        return (-1, tuple())


def compute_score(haystack, positions):
    """To compute the score given the match positions and the haystack
    string length. The lower the better."""
    if not positions:
        return -1

    n = 0
    sum_diffs = 0
    sum_positions = 0
    # Generate all `positions` combinations for k = 2
    len_pos = len(positions)
    for i in range(len_pos):
        sum_positions += positions[i]
        for j in range(i, len_pos):
            if i != j:
                sum_diffs += abs(positions[i]-positions[j])
                n += 1

    ratio = len(haystack)/len_pos

    if n > 0:
        return sum_diffs/n + sum_positions/len_pos + ratio
    else:
        # This branch is executed when len(positions) == 1 (and `diffs` is empty)
        return positions[0] + ratio
