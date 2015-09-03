import json
import tangelo

tangelo.paths(".")
import elasticsearchutils


def run(host, database, graphA, guid, entityId, docId, *args, **kwargs):
    # Create an empty response object.
    response = {}

    entities = elasticsearchutils.getEntitiesForGuid(graphA, guid)
    entity = None
    for testEntity in entities:
        if testEntity.get('id') == entityId:
            entity = testEntity
            break
    doc = None
    docs = elasticsearchutils.getRankingsForGUID(
        guid, queries=entity.get('query'), filters=entity.get('filter'))
    for testDoc in docs:
        if testDoc.get('id') == docId:
            doc = testDoc
            break
    if doc:
        if 'query' in doc:
            response['result'] = elasticsearchutils.getDocument(
                queries=doc['query'])
        else:
            response['result'] = elasticsearchutils.getDocument(
                doc_guid=doc.get('doc_guid'))

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
