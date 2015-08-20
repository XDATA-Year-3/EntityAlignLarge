#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metric


def longestCommonSubstring(s1, s2):
    """
    Return the longest common substring between two strings.

    :param s1: the first string
    :param s2: the second string
    :return: the longest common substring.
    """
    if len(s2) > len(s1):
        s1, s2 = s2, s1
    lens2p1 = len(s2) + 1
    for l in xrange(len(s2), 0, -1):
        for s in xrange(lens2p1 - l):
            substr = s2[s: s + l]
            if substr in s1:
                return substr
    return ''


def substringSimilarity(s1, s2):
    """
    Determine the longest common substring between two strings and normalize
    the results to a scale of 0 to 1.

    :param s1: the first string
    :param s2: the second string
    :return: the normalized result.  1 is a perfect match.
    """
    return 2.0 * len(longestCommonSubstring(s1, s2)) / (len(s1) + len(s2))


class MetricSubstring(metric.Metric):
    name = 'substring'

    def __init__(self, **kwargs):
        super(MetricSubstring, self).__init__(**kwargs)
        self.onEntities = True
        self.saveWork = True

    def calc(self, ga, work, **kwargs):
        """
        Calculate the substring top-k relations.

        :param ga: the entity for which we are computing the metric.
        :returns: the top-k table of relations.
        """
        metric.topKSetsToLists(work)
        return work['topk']

    def calcEntity(self, ga, gb, work={}, state={}, **kwargs):
        """
        Calculate the substring similarity between these two entities.  If
        appopriate, add this to the top-k list.

        :param ga: the entity for which we are computing the metric.
        :param gb: the secondary entity.
        :param work: an object for working on the metric.  This includes the
                     top-k data.
        :param state: the state dictionary.
        """
        # We actually calculate the BEST substring similarity between any name
        # of ga with any name of gb and use that.
        sim = 0
        for gaName in ga['name']:
            for gbName in gb['name']:
                # Note: both gaName and gbName are lowercase.  We may wish to
                # also find the substring match between fullnames.
                sim = max(sim, substringSimilarity(gaName, gbName))
        if sim:
            metric.trackTopK(work, sim, gb['_id'], metric.topKCategories(gb),
                             state)


metric.loadMetric(MetricSubstring)
