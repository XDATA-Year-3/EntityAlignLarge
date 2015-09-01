import copy
import elasticsearch
import json
import tangelo
import urllib
import urllib3

tangelo.paths(".")
import utils

urllib3.disable_warnings()


ColumnLabels = {'doc_type': 'Document Type', 'doc_id': 'Document ID',
                'document': 'Document', 'desc': 'Description'}

CachedResults = {}


def cacheResults(dbname, key, value=None):
    """
    Store results in our result cache.

    :param dbname: database access key.
    :param key: data query key.
    :param value: value to store.  If None, retreive if available.
    :return: the cached value or None.
    """
    if dbname not in CachedResults:
        CachedResults[dbname] = {}
    if value is not None:
        CachedResults[dbname][key] = value
    return CachedResults[dbname].get(key)


def getCases(dbname, allowBuffered=True):
    """
    Get a list of cases that have some document-related data.  For each case,
    get a list of known PersonGUIDs and indicated if these are PA and/or used
    (have document data).

    :param dbname: name of the database.  This is URI encoded and contains an
                   appropriate document type.
    :param allowBuffered: if True, allow cached results to be used.
    :returns cases: a dictionary.  Each key is a case label.  Each value is a
                    a dict of 'guids', 'used', and 'pa', each of which have
                    keys indicated PersonGUIDs in that category.  The guids
                    also has a string of the form guid - name ... - email ...
                    that can be shown to the user.
    """
    dbname = urllib.unquote(dbname).replace('!', '/')
    if allowBuffered and cacheResults(dbname, 'cases'):
        return cacheResults(dbname, 'cases')
    usedGuids = getUsedPersonGuids()
    es = elasticsearch.Elasticsearch(dbname, timeout=300)
    query = {
        "_source": {"include": [
            "PersonGUID", "Identity.Name.FullName",
            "Identity.Email.OriginalEmail", "Identity.Payload",
        ]},
        "size": 25000,
        "query": {"function_score": {"filter": {"bool": {"must": [
            {"exists": {"field": "PersonGUID"}}
        ]}}}},
        "sort": {"PersonGUID": "asc"},
    }
    res = es.search(body=json.dumps(query))
    cases = {}
    for record in res['hits']['hits']:
        doc = record['_source']
        guid = doc['PersonGUID']
        # if usedGuids and guid not in usedGuids:
        #     continue
        pa = False
        case = None
        name = [guid]
        for identIter in xrange(len(doc['Identity'])):
            ident = doc['Identity'][identIter]
            for payIter in xrange(len(ident.get('Payload', []))):
                payload = ident['Payload'][payIter]
                key = payload.get('PayloadName', '').upper()
                value = payload.get('PayloadValue')
                if key in ('CASE NUMBER', 'CASE_NUMBER'):
                    case = value
                elif key == 'RELATIONSHIP' and value == 'PA':
                    pa = True
            name.extend([fullname.get('FullName')
                         for fullname in ident['Name']])
            if 'Email' in ident:
                name.extend([email.get('OriginalEmail')
                             for email in ident['Email']])
        namestr = ' - '.join([subname for subname in name if subname])
        doc['namestr'] = namestr
        if not case:
            continue
        if case not in cases:
            cases[case] = {'pa': {}, 'used': {}, 'guids': {}}
        if usedGuids and guid in usedGuids:
            cases[case]['used'][guid] = True
        cases[case]['guids'][guid] = doc['namestr']
        if pa:
            cases[case]['pa'][guid] = True
    for case in cases.keys():
        if not len(cases[case]['used']):
            del cases[case]
    cacheResults(dbname, 'cases', cases)
    return cases


def getMetricList(dbname, handle):
    """
    Get a list of used metrics based on a database and handle.

    :param dbname: name of the database.  This is URI encoded and contains an
                   appropriate document type.
    :param handle: the userID for the metrics.
    :returns: a dictionary of metrics.  Each value is a dictionary which can
              contain a domain and label.
    """
    config = utils.getDefaultConfig()
    es = None
    lastdbkey = None
    queryinfo = {}
    records = getRankingsForHandle(dbname, handle, True, queryinfo)
    metrics = {}
    for record in records:
        for metric in record['metrics']:
            metDict = {'domain': [0, 1]}
            if record.get('db_key') in config:
                dbkey = record['db_key']
                if dbkey != lastdbkey:
                    es = elasticsearch.Elasticsearch(config[dbkey],
                                                     timeout=300)
                    lastdbkey = dbkey
                if dbkey == 'istRankings':
                    import pprint
                    query = copy.deepcopy(queryinfo[dbkey])
                    if '_source' in query:
                        del query['_source']
                    query.update({'size': 0, 'aggs': {
                        'maxmetric': {'max': {'field': metric}},
                        'minmetric': {'min': {'field': metric}}
                    }})
                    pprint.pprint(query)
                    res = es.search(body=json.dumps(query))
                    if res['aggregations']['minmetric']['value'] is not None:
                        metDict['domain'] = [
                            res['aggregations']['minmetric']['value'],
                            res['aggregations']['maxmetric']['value'],
                        ]
            print metric, metDict
            if metDict['domain'][0] == metDict['domain'][1]:
                continue
            metrics[metric] = metDict
    return metrics


def getRankingsForHandle(dbname, handle, limited=False, queryinfo={}):
    """
    Get all rankings associated with a specific handle, or one of each ranking
    type.

    :param dbname: name of the database.  This is URI encoded and contains an
                   appropriate document type.
    :param handle: the userID for the rankings.
    :param limited: if True, get one of each distinct ranking type.
    :param queryinfo: a dictionary to store query information for different
                      data sources.
    :returns: records found.
    """
    results = []
    collection = urllib.unquote(dbname).replace('!', '/').rsplit(
        '/', 1)[0] + '/ranking'
    dbkey = collection
    es = elasticsearch.Elasticsearch(collection, timeout=300)
    query = {
        '_source': {'include': [
            'documentId', 'documentSource', 'documentLink', 'name', 'info',
            'score'
        ]},
        'size': 25000,  # use a number for debug
        'query': {'function_score': {'query': {'bool': {'must': [
            {'match': {'entityId': handle}},
        ]}}}},
    }
    queryinfo[dbkey] = query
    res = es.search(body=json.dumps(query))
    found = {}
    for hit in res['hits']['hits']:
        record = hit['_source']
        if not record.get('name') or record.get('score') is None:
            continue
        if not limited or record['name'] not in found:
            record['metrics'] = {
                record['name']: record['score']
            }
            record['document'] = record['info']
            record['doc_type'] = 'twitter_user'
            record['doc_guid'] = record['documentId']
            record['doc_link'] = record['documentLink']
            record['db_key'] = dbkey
            results.append(record)
            found[record['name']] = True

    # Combine with IST data
    dbkey = 'istRankings'
    es = elasticsearch.Elasticsearch(utils.getDefaultConfig()[dbkey],
                                     timeout=300)
    query = {
        'size': 25000,  # use a number for debug
        'query': {'function_score': {
            'filter': {'bool': {'must': [
                {'exists': {'field': 'metrics'}}
            ]}},
            'query': {'bool': {'must': [
                {'match': {'visa_guid': handle}},
            ]}},
        }},
    }
    queryinfo[dbkey] = query
    res = es.search(body=json.dumps(query))
    for hit in res['hits']['hits']:
        record = hit['_source']
        newVal = used = False
        for metric in record.get('metrics', {}):
            if metric not in found:
                newVal = True
                found[metric] = True
            used = True
        if used and (not limited or newVal):
            record['db_key'] = dbkey
            results.append(record)
    return results


def getUsedPersonGuids(allowBuffered=True):
    """
    Get a dictionary whose keys are the PersonGUIDs for which we have any
    document ranks.

    :param allowBuffered: if True, allow cached results to be used.
    :returns: a dictionary where any key is a PersonGUID for which at least
              one document exists that we have data for.
    """
    dbkey = 'istRankings'
    if allowBuffered and cacheResults(dbkey, 'usedGuids'):
        return cacheResults(dbkey, 'usedGuids')
    es = elasticsearch.Elasticsearch(utils.getDefaultConfig()[dbkey],
                                     timeout=300)
    query = {
        'size': 0,
        'query': {'function_score': {
            'filter': {'bool': {'must': [
                {'exists': {'field': 'metrics'}}
            ]}},
        }},
        'aggs': {'guids': {
            'terms': {'field': 'visa_guid', 'size': 25000},
        }},
    }
    res = es.search(body=json.dumps(query))
    guids = {}
    for bucket in res['aggregations']['guids']['buckets']:
        guids[bucket['key']] = True
    cacheResults(dbkey, 'usedGuids', guids)
    return guids
