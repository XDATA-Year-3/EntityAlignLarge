import json
import re
from pymongo import MongoClient


def run(host, db, coll, **kwargs):
    # Connect to the mongo collection.
    client = MongoClient(host)
    db = client[db]
    graph = db[coll]
    spec = {'type': 'node'}
    term = kwargs.get('term')
    if term:
        rterm = re.compile(re.escape(term), re.IGNORECASE)
        spec['data.name'] = rterm

    nodes = graph.find(spec, {'data.name': True, '_id': False},
                       limit=int(kwargs.get('limit', 0)),
                       skip=int(kwargs.get('offset', 0)))
    names = [node['data']['name'] for node in nodes]
    if term:
        sortorder = [(
            rterm.search(name).start() if rterm.search(name) else len(name),
            len(name), name.lower(), name) for name in names]
    else:
        sortorder = [(
            len(name), name.lower(), name) for name in names]
    names = [entry[-1] for entry in sorted(sortorder)]
    maxlist = int(kwargs.get('list', 30))
    if maxlist:
        names = names[:maxlist]
    response = {'names': names}
    return json.dumps(response)
