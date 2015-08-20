#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metric


# This is a straightforward implementation of a well-known algorithm, and thus
# probably shouldn't be covered by copyright to begin with. But in case it is,
# the author (Magnus Lie Hetland) has, to the extent possible under law,
# dedicated all copyright and related and neighboring rights to this software
# to the public domain worldwide, by distributing it under the CC0 license,
# version 1.0. This software is distributed without any warranty. For more
# information, see <http://creativecommons.org/publicdomain/zero/1.0>
def levenshtein(a, b):
    """
    Calculates the Levenshtein distance between a and b.

    :param a: one string to compare.
    :param b: the second string to compare.
    :returns: the Levenshtein distance between the two strings.
    """
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n

    current = range(n + 1)
    for i in range(1, m + 1):
        previous, current = current, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete = previous[j] + 1, current[j - 1] + 1
            change = previous[j - 1]
            if a[j - 1] != b[i - 1]:
                change = change + 1
            current[j] = min(add, delete, change)

    return current[n]


def levenshteinSimilarity(s1, s2):
    """
    Calculate and normalize the Levenshtein metric to a result of 0 (poor) to 1
    (perfect).

    :param s1: the first string
    :param s2: the second string
    :return: the normalized result.  1 is a perfect match.
    """
    totalLen = float(len(s1) + len(s2))
    return (totalLen - levenshtein(s1, s2)) / totalLen


class MetricLevenshtein(metric.Metric):
    name = 'levenshtein'

    def __init__(self, **kwargs):
        super(MetricLevenshtein, self).__init__(**kwargs)
        self.onEntities = True
        self.saveWork = True

    def calc(self, ga, work, **kwargs):
        """
        Calculate the Levenshtein top-k relations.

        :param ga: the entity for which we are computing the metric.
        :returns: the top-k table of relations.
        """
        metric.topKSetsToLists(work)
        return work['topk']

    def calcEntity(self, ga, gb, work={}, state={}, **kwargs):
        """
        Calculate the Levenshtein similarity between these two entities.  If
        appopriate, add this to the top-k list.

        :param ga: the entity for which we are computing the metric.
        :param gb: the secondary entity.
        :param work: an object for working on the metric.  This includes the
                     top-k data.
        :param state: the state dictionary.
        """
        # We actually calculate the BEST levenshtein similarity between any
        # name of ga with any name of gb and use that.
        sim = 0
        for gaName in ga['name']:
            for gbName in gb['name']:
                sim = max(sim, levenshteinSimilarity(gaName, gbName))
        if sim:
            metric.trackTopK(work, sim, gb['_id'], metric.topKCategories(gb),
                             state)


metric.loadMetric(MetricLevenshtein)
