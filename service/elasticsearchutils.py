import copy
import elasticsearch
import json
import tangelo
import urllib
import urllib3

tangelo.paths(".")
import utils

urllib3.disable_warnings()


ColumnLabels = {
    'doc_type': 'Document Type',
    'doc_id': 'Document ID',
    'document': 'Document',
    'desc': 'Description',

    'type': 'Type',
    'description': 'Description',
    'enabled': 'Possible',
    'confidence': 'Confidence',
    'derog': 'Derogatory'
}
ColumnDomains = {
    'confidence': [0, 100],
}
ColumnTypes = {
    'confidence': 'number',
}
ColumnWidths = {
    'description': 140,
}
MetricLabels = {
    'name-substring': 'User or email name substring match',
    'fullname-substring': 'Full name substring match',
    'allname-substring': 'Best substring match between all user names and '
                         'full names',
}

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


def getEntitiesForGuid(dbname, guid):
    """
    Get a list of entities that might be the same as the specified guid.  Each
    entity has some standardized information, as well as metrics for how well
    they match the guid.

    :param dbname: name of the database.  This is URI encoded and contains an
                   appropriate document type.
    :param guid: the PersonGuid to match.
    :returns: a list of entities.
    """
    entities = {}
    # currently, we aren't getting information from this database
    dbname = urllib.unquote(dbname).replace('!', '/')
    # We are using this one
    dbkey = 'istRankings'
    es = elasticsearch.Elasticsearch(utils.getDefaultConfig()[dbkey],
                                     timeout=300)
    # We get all relevant documents, and extract unique users from that.
    query = {
        '_source': {'include': [
            'doc_type', 'document.user', 'document._source.actor',
            'document.username',
        ]},
        'size': 25000,
        'query': {'function_score': {
            'filter': {'bool': {'must': [
                {'exists': {'field': 'metrics'}}
            ]}},
            'query': {'bool': {'must': [
                {'match': {'visa_guid': guid}},
            ]}},
        }},
    }
    res = es.search(body=json.dumps(query))
    tweetTypes = ('tweet', 'Tweet', 'QCR_holdings', 'QCR_Holding')
    for hit in res['hits']['hits']:
        record = hit['_source']
        entity = {}
        docType = record.get('doc_type', hit.get('_type'))
        if docType in tweetTypes:
            entity['type'] = 'twitter_user'
            user = record['document']['user']
            entity['user_id'] = user['screen_name']
            entity['id'] = entity['type'] + ':' + entity['user_id']
            entity['query'] = [
                {'bool': {'should': [
                    {'match': {'doc_type': tweetType}}
                    for tweetType in tweetTypes
                ]}},
                {'match': {'document.user.screen_name': user['screen_name']}},
            ]
            entity['description'] = '@' + user['screen_name']
            entity['name'] = user['screen_name']
            fullname = user.get('name')
            if not fullname and 'actor' in record['document'].get(
                    '_source', {}):
                fullname = record['document']['_source']['actor'].get(
                    'displayName')
            if fullname:
                entity['description'] += ' (%s)' % fullname
                entity['fullname'] = fullname
        elif docType == 'Child_Exploitation':
            entity['type'] = 'web_user'
            entity['user_id'] = record['document']['username']
            entity['id'] = entity['type'] + ':' + entity['user_id']
            entity['query'] = [
                {'match': {'doc_type': record.get('doc_type')}},
                {'match': {'document.username': entity['user_id']}},
            ]
            entity['description'] = record['document']['username']
            entity['name'] = record['document']['username']
        elif docType == 'HG_Profiler':
            pass
        # Copy user metrics here, plus any other data we want to show
        if not entity.get('id'):
            continue
        entities[entity['id']] = entity
    return entities.values()


def getMetricDomains(docs):
    """
    Based on a set of documents that contain a metrics key, determine the
    domain of unique metrics.

    :param docs: a list of document objects.
    :returns: a dictionary of metric domains.
    """
    metrics = {}
    for doc in docs:
        for metric in doc['metrics'].keys():
            if not isinstance(doc['metrics'][metric], (int, float)):
                try:
                    doc['metrics'][metric] = float(
                        doc['metrics'][metric])
                except ValueError:
                    del doc['metrics'][metric]
                    continue
            if metric not in metrics:
                metrics[metric] = [
                    doc['metrics'][metric], doc['metrics'][metric]]
            metrics[metric][0] = min(metrics[metric][0],
                                     doc['metrics'][metric])
            metrics[metric][1] = max(metrics[metric][1],
                                     doc['metrics'][metric])
            # Flatten key structure
            doc[metric] = doc['metrics'][metric]
    return metrics


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
        for metric in record['metrics'].keys():
            if not isinstance(record['metrics'][metric], (int, float)):
                try:
                    record['metrics'][metric] = float(
                        record['metrics'][metric])
                except ValueError:
                    del record['metrics'][metric]
            metDict = metric.get(metric, {'domain': [0, 1]})
            if record.get('db_key') in config:
                dbkey = record['db_key']
                if dbkey != lastdbkey:
                    es = elasticsearch.Elasticsearch(config[dbkey],
                                                     timeout=300)
                    lastdbkey = dbkey
                if dbkey == 'istRankings':
                    query = copy.deepcopy(queryinfo[dbkey])
                    if '_source' in query:
                        del query['_source']
                    query.update({'size': 0, 'aggs': {
                        'maxmetric': {'max': {'field': metric}},
                        'minmetric': {'min': {'field': metric}}
                    }})
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


def getRankingsForGUID(handle, limited=False, queryinfo={}, queries=None,
                       filters=None):
    """
    Get all rankings associated with a specific handle, or one of each ranking
    type.

    :param handle: the userID for the rankings.
    :param limited: if True, get one of each distinct ranking type.
    :param queryinfo: a dictionary to store query information for different
                      data sources.
    :param queries: a list of additional query specifications to add to the
                    elasticseach query.
    :param filters: a list of additional filter specifications to add to the
                    elasticseach query.
    :returns: records found.
    """
    results = []
    found = {}
    # Only user IST data
    dbkey = 'istRankings'
    es = elasticsearch.Elasticsearch(utils.getDefaultConfig()[dbkey],
                                     timeout=300)
    queryList = [{'match': {'visa_guid': handle}}]
    filterList = [{'exists': {'field': 'metrics'}}]
    if queries is not None and len(queries):
        queryList.append(queries)
    if filters is not None and len(filters):
        filterList.append(filters)
    query = {
        '_source': {'include': [
            'doc_type', 'doc_guid', 'document.user', 'document.id',
            'document.text', 'metrics',
            # I probably need to tweek this for the non-tweet data
        ]},
        'size': 25000,
        'query': {'function_score': {
            'filter': {'bool': {'must': filterList}},
            'query': {'bool': {'must': queryList}},
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
    queryList = [{'match': {'entityId': handle}}]
    query = {
        '_source': {'include': [
            'documentId', 'documentSource', 'documentLink', 'name', 'info',
            'score'
        ]},
        'size': 25000,
        'query': {'function_score': {
            'query': {'bool': {'must': queryList}},
        }},
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
    queryList = [{'match': {'visa_guid': handle}}]
    filterList = [{'exists': {'field': 'metrics'}}]
    query = {
        'size': 25000,
        'query': {'function_score': {
            'filter': {'bool': {'must': filterList}},
            'query': {'bool': {'must': queryList}},
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


def lineupFromMetrics(response, docs, firstColumns, lastColumns=[],
                      includeZeroMetrics=False):
    """
    Add information for lineup into a response document.

    :param response: the dictionary to add lineup data into.  Modified.
    :param docs: a list of documents that contain metrics.
    :param firstColumns: a list of column ids to include at the beginning of
                         the line up.  The first value is used as the unique
                         row id, not as a column.  Required.
    :param lastColumns: a list of column ids to include at the end of the line
                        up.  Optional.
    :param includeZeroMetrics: if True, include metrics for which all values
                               are exactly zero.
    """
    response['primaryKey'] = firstColumns[0]
    response['columns'] = col = []
    laycol = []
    primecol = []
    response['layout'] = {'primary': primecol}
    for key in firstColumns + lastColumns:
        colData = {
            'column': key,
            'type': ColumnTypes.get(key, 'string'),
        }
        colData['label'] = ColumnLabels.get(key)
        colData['domain'] = ColumnDomains.get(key)
        col.append(colData)
        if len(col) > 1:
            primecol.append({
                'column': key,
                'width': ColumnWidths.get(key, 60)
            })
        if len(col) == len(firstColumns):
            primecol.append(
                {"type": "stacked", "label": "Combined", "children": laycol})
    metrics = getMetricDomains(docs)
    import pprint
    pprint.pprint(metrics)  # ##DWM::
    for metric in metrics.keys():
        domain = metrics[metric]
        if domain[0] >= 0 and domain[1] >= 0:
            domain[0] = 0
            if domain[1] < 1:
                domain[1] = 1
        elif domain[0] < 0 and domain[1] < 0:
            domain[1] = 0
        if (domain[0] == domain[1] and (
                domain[0] != 0 or not includeZeroMetrics)):
            del metrics[metric]
    pprint.pprint(metrics)  # ##DWM::
    for metric in sorted(metrics.keys()):
        col.append({
            'column': metric,
            'type': 'number',
            'domain': metrics[metric],
        })
        if MetricLabels.get(metric):
            col[-1]['label'] = MetricLabels[metric]
        laycol.append({'column': metric, 'width': 350./len(metrics)})
