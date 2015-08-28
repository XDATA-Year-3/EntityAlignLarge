import elasticsearch
import json
import tangelo
import urllib
import urllib3

tangelo.paths(".")
from listdatasets import getDefaultConfig

urllib3.disable_warnings()


translate = {'doc_type': 'Document Type', 'doc_id': 'Document ID',
             'document': 'Document', 'desc': 'Description'}


def getRankingsForHandle(dbname, handle, limited=False):
    """
    Get all rankings associated with a specific handle, or one of each ranking
    type.

    :param dbname: name of the database.  This is URI encoded and contains an
                   inappropriate document type.
    :param handle: the userID for the rankings.
    :param limited: if True, get one of each distinct ranking type.
    :returns: records found.
    """
    results = []
    collection = urllib.unquote(dbname).replace('!', '/').rsplit(
        '/', 1)[0] + '/ranking'
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
            results.append(record)
            found[record['name']] = True

    # Combine with IST data
    es = elasticsearch.Elasticsearch(getDefaultConfig()['istRankings'],
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
    res = es.search(body=json.dumps(query))
    for hit in res['hits']['hits']:
        record = hit['_source']
        # import pprint
        # pprint.pprint(record)
        newVal = used = False
        for metric in record.get('metrics', {}):
            if metric not in found:
                newVal = True
                found[metric] = True
            used = True
        if used and (not limited or newVal):
            results.append(record)
    return results


def run(host, database, graphA, handle, displaymode):
    # Create an empty response object.
    response = {}

    records = getRankingsForHandle(graphA, handle)
    docids = {}
    for record in records:
        docid = (record.get('doc_type') + ':' +
                 record.get('doc_guid', ''))
        if docid not in docids:
            docids[docid] = doc = {
                'dochash': docid,
                # 'document': record.get('document'),
                'doc_type': record.get('doc_type', ''),
                'doc_id': record.get('doc_guid', ''),
                'desc': docid,
            }
            if record.get('info') and record.get('doc_type') == 'twitter_user':
                doc['desc'] = record['document'].get('name', [])[0]
                if len(record['document'].get('fullname', [])):
                    doc['desc'] += ' - ' + record['info']['fullname'][0]
        for metric in record['metrics']:
            docids[docid][metric] = record['metrics'][metric]
    response['result'] = docids.values()

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
