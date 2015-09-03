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
    records = elasticsearchutils.getUserRankingsForGUID(guid)
    metrics = {}
    for record in records:
        id = 'twitter_user:' + record.get('screenname', '')
        id = id.lower()
        if id == entity['id'].lower():
            metrics.update(record['metrics'])
    response['result'] = [{'id': entity['id'], 'metrics': metrics}]
    elasticsearchutils.lineupFromMetrics(
        response, response['result'], ['id'], includeZeroMetrics=True)

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
