import json
import os


def getDefaultConfig():
    """
    Fetch the defaults.json file.

    :returns: the parsed file.
    """
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    config = json.loads(open(os.path.join(
        scriptPath, '..', 'defaults.json')).read())
    return config


def run(host, database):
    # Create an empty response object.
    response = {}
    collectionNames = [{'name': 'Select a dataset', 'value': ''}]

    config = getDefaultConfig()
    # Manually hard-code the entity dataset list.
    collectionNames.append({
        'name': 'People List',
        'value': config['entities']
    })

    # Pack the results into the response object, and return it.
    response['result'] = collectionNames

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
