import json
import tangelo

tangelo.paths(".")
import elasticsearchutils


def run(host, database, graphA, handle, displaymode):
    # Create an empty response object.
    response = {}

    records = elasticsearchutils.getRankingsForHandle(graphA, handle)
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
