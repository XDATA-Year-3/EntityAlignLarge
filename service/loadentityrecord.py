import elasticsearch
import json
import urllib


def run(host, database, graphA, handle):

    collection = urllib.unquote(graphA)
    es = elasticsearch.Elasticsearch(collection, timeout=300)
    query = {
        'query': {'function_score': {'query': {'bool': {'must': [
            {'match': {'PersonGUID': handle}},
        ]}}}},
    }
    res = es.search(body=json.dumps(query))
    doc = res['hits']['hits'][0]['_source']
    response = {'result': doc}

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
