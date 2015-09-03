import json
import tangelo

tangelo.paths(".")
import elasticsearchutils


def run(host, database, graphA, guid, entityId, *args, **kwargs):
    # Create an empty response object.
    response = {}

    entities = elasticsearchutils.getEntitiesForGuid(graphA, guid)
    entity = None
    for testEntity in entities:
        if testEntity.get('id') == entityId:
            entity = testEntity
            break
    records = elasticsearchutils.getRankingsForGUID(
        guid, queries=entity.get('query'), filters=entity.get('filter'))
    # Massage the data to a simpler form, add a description, etc.
    for record in records:
        record['description'] = record.get('document', {}).get(
            'text', 'No description')
        record['id'] = record.get('doc_type', '') + ':' + record['doc_guid']
    response['result'] = records
    elasticsearchutils.lineupFromMetrics(
        response, records, ['id', 'doc_type', 'description'],
        ['derog'], True)

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
