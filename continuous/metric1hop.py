#!/usr/bin/env python
# -*- coding: utf-8 -*-

import metric


class Metric1hop(metric.Metric):
    name = '1hop'

    def __init__(self, **kwargs):
        super(Metric1hop, self).__init__(**kwargs)

    def calc(self, ga, **kwargs):
        """
        Calculate the number of 1 hop neighbors.  Since we already have the
        neighbors in the entity record, this is just that length.

        :param ga: the entity for which we are computing the metric.
        :returns: the number of 1-hop neighbors.
        """
        # This does not include the node itself
        return len(ga.get('neighbors', []))


metric.loadMetric(Metric1hop)
