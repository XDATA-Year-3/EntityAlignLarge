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
        self.entityFields = {
            'name': True,
            'fullname': True,
            'service': True,
            'msgs.service': True,
            'msgs.subset': True
        }
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
        simName = simFull = simBoth = 0
        for gaName in ga['name']:
            for gbName in gb['name']:
                # Note: both gaName and gbName are lowercase.  We may wish to
                # also find the substring match between fullnames.
                simName = max(simName, substringSimilarity(gaName, gbName))
            for gbName in gb['fullname']:
                simBoth = max(simBoth, substringSimilarity(gaName,
                                                           gbName.lower()))
        for gaName in ga['fullname']:
            for gbName in gb['fullname']:
                # Note: both gaName and gbName are lowercase.  We may wish to
                # also find the substring match between fullnames.
                simFull = max(simName, substringSimilarity(
                    gaName.lower(), gbName.lower()))
            for gbName in gb['name']:
                simBoth = max(simBoth, substringSimilarity(gaName.lower(),
                                                           gbName))
        simBoth = max(simBoth, simName, simFull)
        if simName:
            metric.trackTopK(work['name'], simName, gb['_id'],
                             metric.topKCategories(gb), state)
        if simFull:
            metric.trackTopK(work['fullname'], simFull, gb['_id'],
                             metric.topKCategories(gb), state)
        if simBoth:
            metric.trackTopK(work['name_fullname'], simBoth, gb['_id'],
                             metric.topKCategories(gb), state)

    def calcEntityPrep(self, ga, work={}, **kwargs):
        """
        This is called before calcEntity is called on each second entity.

        :param ga: the entity for which we are computing the metric.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        for key in ('name', 'fullname', 'name_fullname'):
            if not key in work:
                work[key] = {}


metric.loadMetric(MetricSubstring)
