#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This has the general classes and functions for metric computation

import collections
import importlib
import pprint
import unicodedata

LoadedMetrics = collections.OrderedDict()


class Metric(object):
    """
    Subclass this to compute a metric on an entity.
    """
    name = 'metric'

    def __init__(self, **kwargs):
        self.args = kwargs
        self.dependencies = []  # metrics that must run before this one
        # does this need to operate on all links to the entity?
        self.onLinks = False
        # If we have to visit links, only visit updated links if this is True,
        # otherwise visit all the links when recomputing the metric.
        # This also determines if a metric should be recomputed if any link
        # was updated, even if we aren't using the links.
        self.onLinksOnlyNew = True
        # does this need to operate on all other entities in combination with
        # this entity?
        self.onEntities = False
        # If we have to visit entities, only visit updated entities if this is
        # True, otherwise visit all the entities when recomputing the metric.
        # This also determines if a metric should be recomputed if any entity
        # was updated, even if we aren't using the entities.
        self.onEntitiesOnlyNew = True
        # If self.entityFields is specified, only those fields are retreived
        # when visiting entities.  This can be used to reduce data transfer
        # from the database.
        # self.entityFields = {'name': True}
        # If saveWork is True, the work record is saved along with the value of
        # the metric
        self.saveWork = False

    def calc(self, ga, work={}, **kwargs):
        """
        Calculate the metric based on the accumulated or stand-alone data.

        :param ga: the entity for which we are computing the metric.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        :returns: the value of the metric.
        """
        return

    def calcEntity(self, ga, gb, work={}, **kwargs):
        """
        Subclass this to handle partial calculations based on a second entity.

        :param ga: the entity for which we are computing the metric.
        :param gb: the secondary entity.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        return

    def calcEntityPrep(self, ga, work={}, **kwargs):
        """
        Subclass this to handle partial calculations based on a second entity.
        This is called before calcEntity is called on each second entity.

        :param ga: the entity for which we are computing the metric.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        return

    def calcLink(self, ga, gb, link, work={}, **kwargs):
        """
        Subclass this to handle partial calculations based on a link.

        :param ga: the entity for which we are computing the metric.
        :param gb: the secondary entity.
        :param link: the link between the two entities.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        return

    def calcLinkPrep(self, ga, work={}, **kwargs):
        """
        Subclass this to handle partial calculations based on a link.
        This is called before calcLink is called on each link.

        :param ga: the entity for which we are computing the metric.
        :param work: an object for working on the metric.  Results should be
                     stored here.
        """
        return


def loadMetric(metricClass, initVal=None):
    """
    Load a metric and its dependencies.  Keep the list of loaded metrics
    ordered so that if we walk the list, all dependencies will be met.

    :param metricClass: the class of the metric to load or a string with the
                        name of a metric we should attempt to located.
    :param initVal: a value to pass to the class when initializing it.
    :returns: True if success, None if failed to load dependencies.
    """
    if isinstance(metricClass, basestring):
        className = 'Metric' + metricClass.capitalize()
        if globals().get(className):
            metricClass = globals().get(className)
        else:
            moduleName = 'metric' + metricClass
            module = importlib.import_module(moduleName)
            # We expect metrics to register themselves, but if they
            # don't, we try the expected class name again.
            if metricClass not in LoadedMetrics:
                if getattr(module, className, None):
                    metricClass = getattr(module, className)
        if isinstance(metricClass, basestring):
            return None
    if metricClass.name not in LoadedMetrics:
        if initVal is None:
            initVal = {}
        elif not isinstance(initVal, dict):
            initVal = {'value': initVal}
        newMetric = metricClass(**initVal)
        for dependency in newMetric.dependencies:
            if dependency not in LoadedMetrics:
                loadMetric(dependency)
        LoadedMetrics[metricClass.name] = newMetric
        return True


def normalizeAndLower(text):
    """
    Convert some text so that it is normalized and lowercased unicode.

    :param text: the text to alter.
    :returns: the normalized and lower-cased text.
    """
    if isinstance(text, str):
        text = text.decode('utf8')
    text = unicodedata.normalize('NFC', text)
    return text.lower()


def normalizeNames(entity):
    """
    Normalize the name and fullname lists in an entity.

    :param entity: the entity to modify.
    """
    entity['normname'] = list({normalizeAndLower(name)
                               for name in entity['name']})
    entity['normfullname'] = list({normalizeAndLower(name)
                                   for name in entity['fullname']})


def topKCategories(entity):
    """
    Return a set of categories used for tracking topk.

    :param entity: the entity for which to extract categories.
    :returns: a set of categories.
    """
    cat = set()
    if entity.get('service'):
        cat.add(entity['service'])
    for msg in entity.get('msgs', []):
        cat.update([msg['service'] + '-' + subset for subset in msg['subset']])
    return cat


def topKSetsToLists(topkDict):
    """
    Convert the sets in the topk list to lists so we can store them.  This also
    removes the id dictionary, as it is not necessary.

    :param topkDict: the dictionary of topk results.  Modified.
    """
    if 'topk' not in topkDict:
        return
    topk = topkDict['topk']
    if len(topk) and isinstance(topk[0][-1], set):
        for pos in xrange(len(topk)):
            topk[pos] = (topk[pos][0], topk[pos][1], list(topk[pos][2]))
    if 'ids' in topkDict:
        del topkDict['ids']


def trackTopK(topkDict, value, id, cats, state):
    """
    Track the top-k values for various services and subsets.  Each service and
    subset will have at least k entries in the list.

    :param topkDict: a dictionary to store the top-k in.
    :param value: the value associated with an item.  Higher values are kept.
    :param id: the id of the item.  If the id is already present, it will be
               replaced.
    :param cats: a set of categories to track for this item.
    :param state: the state dictionary with the definition of k.
    :return: True is we added this item into the top-k.  False if it was too
             minor.
    """
    if 'topk' not in topkDict:
        topkDict['topk'] = []
        topkDict['cats'] = {}
        topkDict['ids'] = {}
        topkDict['processed'] = 0
        if (state and 'config' in state and 'topk' in state['config'] and
                state['config']['topk'].get('k')):
            topkDict['k'] = (state['config']['topk']['k'] +
                             state['config']['topk'].get('extra', 0))
        else:
            topkDict['k'] = 25
    topk = topkDict['topk']
    k = topkDict['k']
    topkDict['processed'] += 1
    # When we get our dictionary out of storage, it contains lists, not sets.
    # We want to operate on sets.  Also, recerate our ids dictionary.
    if len(topk) and isinstance(topk[0][-1], list):
        for pos in xrange(len(topk)):
            topk[pos] = (topk[pos][0], topk[pos][1], set(topk[pos][2]))
        topkDict['ids'] = dict.fromkeys([row[1] for row in topk])
    if not cats or not len(cats):
        cats = set('default')
    # If we already have this id, remove it
    if id in topkDict['ids']:
        for pos in xrange(len(topk)):
            rval, rid, rcats = topk[pos]
            if rid == id:
                if rid in topkDict['ids']:
                    del topkDict['ids'][rid]
                for cat in rcats:
                    topkDict['cats'][cat] -= 1
                topk[pos:pos+1] = []
                break
    # Skip this one if we can tell it shouldn't be added.
    if (len(topk) >= k and value < topk[-1][0] and
            not any(topkDict['cats'].get(cat, 0) < k for cat in cats)):
        return False
    # Add the entry to the list
    entry = (value, id, cats)
    topk.append(entry)
    topk.sort(reverse=True)
    topkDict['ids'][id] = True
    for cat in cats:
        topkDict['cats'][cat] = topkDict['cats'].get(cat, 0) + 1
    kept = trackTopKRemove(topkDict, entry)
    if kept and state['args']['verbose'] >= 3:
        pprint.pprint(topkDict)
    return kept


def trackTopKRemove(topkDict, entry):
    """
    Check if we need to remove any entries from the top-k list.  Because of
    keeping the top-k for multiple categories, one addition can result in
    removing multiple rows.

    :param topk: the list of topk entries.
    :param entry: a tuple of (value, id, cats) that was just added to the topk
                  list.
    :return: True is we kept the item that was added into the top-k.  False if
             it was removed.
    """
    k = topkDict['k']
    topk = topkDict['topk']
    kept = True
    cats = entry[2]
    if len(topk) > k:
        while True:
            counts = {cat: 0 for cat in cats}
            remove = False
            for pos in xrange(len(topk)):
                rval, rid, rcats = topk[pos]
                for cat in cats:
                    if cat in rcats:
                        counts[cat] += 1
                if (min(counts.values()) > k and rcats.issubset(cats)):
                    if topk[pos] == entry:
                        kept = False
                    if rid in topkDict['ids']:
                        del topkDict['ids'][rid]
                    for cat in rcats:
                        topkDict['cats'][cat] -= 1
                    topk[pos:pos+1] = []
                    remove = True
                    break
            if not remove:
                break
    return kept


def trackTopKWorst(topkDict, cats, low):
    """
    Determine the worst value that we need to care about for tracking the
    sepecified categories.

    :param topkDict: a dictionary with the top-k.
    :param cats: a set of categories for a potential item.
    :param low: a fall-back low value.
    :return: The worst value that could be added to the top-k for these
             categories.
    """
    if not cats or not len(cats) or 'topk' not in topkDict:
        return low
    topk = topkDict['topk']
    k = topkDict['k']
    if len(topk) < k or isinstance(topk[0][-1], list):
        return low
    if any(topkDict['cats'].get(cat, 0) < k for cat in cats):
        return low
    return topk[-1][0]
