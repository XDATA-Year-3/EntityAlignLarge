#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metric


class Metric2hop(metric.Metric):
    name = '2hop'

    def __init__(self, **kwargs):
        super(Metric2hop, self).__init__(**kwargs)
        self.onLinksOnlyNew = False

    def calc(self, ga, entityColl, **kwargs):
        """
        Calculate the number of 2 hop neighbors.

        :param ga: the entity for which we are computing the metric.
        :param entityColl: the database collection used for querying neighbors.
        :returns: the number of 2-hop neighbors, both excluding 1-hop-only
                  neighbors and including 1-hop-only neighbors.  The central
                  node is never counted.
        """
        if not len(ga.get('neighbors', [])):
            return {'2hop': 0, 'lte2hop': 0}
        neighbors = set()
        for gb in entityColl.find({'_id': {'$in': list(neighbors)}},
                                  {'neighbors': True}, timeout=False):
            neighbors.update(gb.get('neighbors', []))
        neighbors.discard(ga['_id'])
        result = {'2hop': len(neighbors)}
        neighbors.update(ga['neighbors'])
        result['lte2hop'] = len(neighbors)
        return result


metric.loadMetric(Metric2hop)
