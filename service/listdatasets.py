import json
import tangelo

tangelo.paths(".")
import utils


def run(host, database):
    # Create an empty response object.
    response = {}
    collectionNames = [{'name': 'Select a dataset', 'value': ''}]

    config = utils.getDefaultConfig()
    # Manually hard-code the entity dataset list.
    collectionNames.append({
        'name': 'Cases List',
        'value': config['entities']
    })

    # Pack the results into the response object, and return it.
    response['result'] = collectionNames

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
