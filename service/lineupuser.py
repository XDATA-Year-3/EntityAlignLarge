import elasticsearch
import json
import tangelo
import urllib

tangelo.paths(".")
import elasticsearchutils

try:
    import Levenshtein
except Exception:
    Levenshtein = None


def calculateMetrics(graphA, guid, entities, knownMetrics={}):
    """
    Get the main entity and calculate some simple metrics.  This should be
    replaced by pre-computed data.

    :param graphA: name of our main entity database, escaped.
    :param guid: PersonGuid of the main entity.
    :param entities: matching entities from the document database.
    """
    collection = urllib.unquote(graphA).replace('!', '/')
    es = elasticsearch.Elasticsearch(collection, timeout=300)
    query = {
        'query': {'function_score': {'query': {'bool': {'must': [
            {'match': {'PersonGUID': guid}},
        ]}}}},
    }
    res = es.search(body=json.dumps(query))
    doc = res['hits']['hits'][0]['_source']
    names = []
    fullnames = []
    for identIter in xrange(len(doc['Identity'])):
        ident = doc['Identity'][identIter]
        fullnames.extend([fullname.get('FullName')
                          for fullname in ident['Name']])
        if 'Email' in ident:
            names.extend([email['Username'].lower() for email in ident['Email']
                          if email.get('Username')])
    allnames = names + fullnames
    for entity in entities:
        if entity['id'].lower() in knownMetrics:
            entity['metrics'] = knownMetrics[entity['id'].lower()]
            continue
        entity['metrics'] = {}
        if entity.get('name') and len(names):
            entity['metrics']['name-substring'] = max([
                substringSimilarity(entity['name'].lower(), name.lower())
                for name in names])
            entity['metrics']['name-levenshtein'] = max([
                levenshteinSimilarity(entity['name'].lower(), name.lower())
                for name in names])
        if entity.get('fullname') and len(fullnames):
            entity['metrics']['fullname-substring'] = max([
                substringSimilarity(entity['fullname'].lower(), name.lower())
                for name in fullnames])
            entity['metrics']['fullname-levenshtein'] = max([
                levenshteinSimilarity(entity['fullname'].lower(), name.lower())
                for name in fullnames])
        enames = []
        if entity.get('name'):
            enames.append(entity['name'])
        if entity.get('fullname'):
            enames.append(entity['fullname'])
        if len(enames) and len(allnames):
            entity['metrics']['allname-substring'] = 0
            entity['metrics']['allname-levenshtein'] = 0
            entity['metrics']['jaro-winkler'] = 0
            for ename in enames:
                entity['metrics']['allname-substring'] = max(
                    entity['metrics']['allname-substring'], max([
                        substringSimilarity(ename.lower(), name.lower())
                        for name in allnames]))
                entity['metrics']['allname-levenshtein'] = max(
                    entity['metrics']['allname-levenshtein'], max([
                        levenshteinSimilarity(ename.lower(), name.lower())
                        for name in allnames]))
                if Levenshtein:
                    entity['metrics']['jaro-winkler'] = max(
                        entity['metrics']['jaro-winkler'], max([
                            Levenshtein.jaro_winkler(
                                ename.lower(), name.lower())
                            for name in allnames]))


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


def levenshteinSimilarity(s1, s2):
    """
    Calculate and normalize the Levenshtein metric to a result of 0 (poor) to 1
    (perfect).

    :param s1: the first string
    :param s2: the second string
    :return: the normalized result.  1 is a perfect match.
    """
    totalLen = float(len(s1) + len(s2))
    # The C-module version of Levenshtein is vastly faster
    if Levenshtein is None:
        return (totalLen - levenshtein(s1, s2)) / totalLen
    if isinstance(s1, str):
        s1 = s1.decode('utf8')
    if isinstance(s2, str):
        s2 = s2.decode('utf8')
    return (totalLen - Levenshtein.distance(s1, s2)) / totalLen


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


def run(host, database, graphA, guid, *args, **kwargs):
    # Create an empty response object.
    response = {}

    entities = elasticsearchutils.getEntitiesForGuid(graphA, guid)
    entityMetrics = elasticsearchutils.getEntityMetricsForGuid(guid)

    # We have to compute metrics ourselves until we get better data
    calculateMetrics(graphA, guid, entities, entityMetrics)

    response['result'] = entities
    # For our results, generate the lineup columns
    elasticsearchutils.lineupFromMetrics(
        response, entities, ['id', 'type', 'description'],
        ['enabled', 'confidence'])

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
