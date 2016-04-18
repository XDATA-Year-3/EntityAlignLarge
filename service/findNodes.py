import bson.json_util
from bson.objectid import ObjectId
import json
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

    matcher = {"type": "node"}
    for field, value in spec.iteritems():
        if field == "key":
            matcher["_id"] = ObjectId(value)
        else:
            matcher["data.%s" % (field)] = value

    it = graph.find(matcher, skip=offset, limit=limit)
    try:
        result = it.next() if singleton else list(it)
    except StopIteration:
        result = None

    return bson.json_util.dumps(result)
