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
    response['result'] = entity

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
