import urllib
import bson.json_util
import json
from bson.objectid import ObjectId
from pymongo import MongoClient


def run(host=None, db=None, coll=None, spec=None, singleton=json.dumps(False),
        offset=None, limit=None, *args, **kwargs):
    # Connect to the mongo collection.
    client = MongoClient(host)
    db = client[db]
    graph = db[coll]

    spec = json.loads(spec)
    singleton = json.loads(singleton)
    offset = 0 if offset is None else int(offset)
    limit = 0 if limit is None else int(limit)
    if singleton:
        limit = 1

    matcher = {"type": "node"}
    for field, value in spec.iteritems():
        if field == "key":
            matcher["_id"] = ObjectId(value)
        else:
            matcher["data.%s" % (field)] = value

    nodes = list(graph.find(matcher, skip=offset, limit=limit))
    for node in nodes:
        if (coll.lower().startswith('twitter') and 'data' in node and
                'name' in node['data']):
            node['data']['profile_image'] = (
                'https://twitter.com/%s/profile_image?size=original' % (
                    urllib.quote(node['data']['name']), ))
    if singleton:
        result = nodes[0] if len(nodes) else None
    else:
        result = nodes
    return bson.json_util.dumps(result)
