import json


def run(host, database):
    # Create an empty response object.
    response = {}
    collectionNames = [{'name': 'Select a dataset', 'value': ''}]

    # Manually hard-code the entity dataset list.
    collectionNames.append({
        'name': 'People List',
        'value': '10.0.2.2:9200/test1/entity'
    })

    # Pack the results into the response object, and return it.
    response['result'] = collectionNames

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
