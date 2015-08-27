import elasticsearch
import json
import urllib


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
    collection = urllib.unquote(dbname).rsplit('/', 1)[0] + '/ranking'
    es = elasticsearch.Elasticsearch(collection, timeout=300)
    query = {
        '_source': {'include': [
            'documentId', 'documentSource', 'documentLink', 'name', 'info',
            'score'
        ]},
        'size': 25000,  # use a number for debug
        'query': {'function_score': {'filter': {'bool': {'must': [
            {'term': {'entityId': handle}},
            # {'exists': {'field': 'entityId'}}
        ]}}}},
    }
    res = es.search(body=json.dumps(query))
    results = []
    found = {}
    for hit in res['hits']['hits']:
        record = hit['_source']
        if not record.get('name') or record.get('score') is None:
            continue
        if not limited or record['name'] not in found:
            results.append(record)
            found[record['name']] = True
    return results


def run(host, database, graphA, handle, displaymode):
    # Create an empty response object.
    response = {}

    records = getRankingsForHandle(graphA, handle)
    docids = {}
    for record in records:
        metric = record['name']
        score = record['score']
        docid = (record.get('documentSource') + ':' +
                 record.get('documentId', ''))
        if docid not in docids:
            docids[docid] = doc = {
                'info': record.get('info'),
                'document': docid,
                'doc_type': record.get('documentSource', ''),
                'doc_id': record.get('documentId', ''),
                'desc': docid,
            }
            if record.get('info') and record.get('documentSource') == 'twitter':
                doc['desc'] = record['info'].get('name', [])[0]
                if len(record['info'].get('fullname', [])):
                    doc['desc'] += ' - ' + record['info']['fullname'][0]
        docids[docid][metric] = score
    response['result'] = docids.values()

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
