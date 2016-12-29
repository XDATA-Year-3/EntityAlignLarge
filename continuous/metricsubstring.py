#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metric


def longestCommonSubstring(s1, s2, low=0):
    """
    Return the longest common substring between two strings.

    :param s1: the first string
    :param s2: the second string
    :param low: one less than the length of the shortest string we need to
                consider.
    :return: the longest common substring.
    """
    if len(s2) > len(s1):
        s1, s2 = s2, s1
    while len(s2) > low:
        if s2[0] in s1:
            break
        s2 = s2[1:]
    while len(s2) > low:
        if s2[-1] in s1:
            break
        s2 = s2[:-1]
    lens2p1 = len(s2) + 1
    for l in xrange(len(s2), low, -1):
        for s in xrange(lens2p1 - l):
            substr = s2[s: s + l]
            if substr in s1:
                return substr
    return ''


def substringSimilarity(s1, s2, low=0):
    """
    Determine the longest common substring between two strings and normalize
    the results to a scale of 0 to 1.

    :param s1: the first string
    :param s2: the second string
    :param low: the lowest value we need to consider.
    :return: the normalized result.  1 is a perfect match.
    """
    lens1s2 = len(s1) + len(s2)
    return (2.0 * len(longestCommonSubstring(s1, s2, int(low * lens1s2 / 2))) /
            (lens1s2))


class MetricSubstring(metric.Metric):
    name = 'substring'

    def __init__(self, **kwargs):
        super(MetricSubstring, self).__init__(**kwargs)
        self.onEntities = True
        self.entityFields = {
            'name': True,
            'fullname': True,
            'service': True,
            'msgs.service': True,
            'msgs.subset': True
        }
        self.normalizeNames = True
        self.saveWork = True

    def calc(self, ga, work, **kwargs):
        """
        Calculate the substring top-k relations.

        :param ga: the entity for which we are computing the metric.
        :returns: the top-k table of relations.
        """
        res = {}
        for key in ('name', 'fullname', 'name_fullname'):
            metric.topKSetsToLists(work[key])
            if 'topk' in work[key]:
                res[key] = work[key]['topk']
        return res

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
        cat = metric.topKCategories(gb)
        lowName = metric.trackTopKWorst(work['name'], cat, 0)
        lowFull = metric.trackTopKWorst(work['fullname'], cat, 0)
        lowBoth = metric.trackTopKWorst(work['name_fullname'], cat, 0)
        simName = simFull = simBoth = 0
        gaNames = ga['normname']
        gbNames = gb['normname']
        gaFullnames = ga['normfullname']
        gbFullnames = gb['normfullname']
        for gaName in gaNames:
            for gbName in gbNames:
                # Note: both gaName and gbName are lowercase.
                simName = max(simName, substringSimilarity(
                    gaName, gbName, lowName))
            if simName < 1:
                for gbName in gbFullnames:
                    simBoth = max(simBoth, substringSimilarity(
                        gaName, gbName, lowBoth))
        for gaName in gaFullnames:
            for gbName in gbFullnames:
                simFull = max(simFull, substringSimilarity(
                    gaName, gbName, lowFull))
            if simFull < 1 and simName < 1:
                for gbName in gbNames:
                    simBoth = max(simBoth, substringSimilarity(
                        gaName, gbName, lowBoth))
        simBoth = max(simBoth, simName, simFull)
        if simName and simName >= lowName:
            metric.trackTopK(work['name'], simName, gb['_id'],
                             cat, state)
        if simFull and simFull >= lowFull:
            metric.trackTopK(work['fullname'], simFull, gb['_id'],
                             cat, state)
        if simBoth and simBoth >= lowBoth:
            metric.trackTopK(work['name_fullname'], simBoth, gb['_id'],
                             cat, state)

    def calcEntityPrep(self, ga, work={}, **kwargs):
        """
        This is called before calcEntity is called on each second entity.

        :param ga: the entity for which we are computing the metric.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        metric.normalizeNames(ga)
        for key in ('name', 'fullname', 'name_fullname'):
            if key not in work:
                work[key] = {}


metric.loadMetric(MetricSubstring)
