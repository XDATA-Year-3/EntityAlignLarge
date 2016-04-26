import bson.json_util
import json
import os
import re
import unicodedata
import urllib
from bson.objectid import ObjectId
from pymongo import MongoClient


def safe_path(value, noperiods=False):
    """
    Make sure a string is a safe file path.

    :param value: the string to escape.
    :param noperids: if true, escape periods, too.
    :returns: the escaped string
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = re.sub('[-\s]+', '-', value)
    if noperiods:
        value = value.replace('.', '-')
    return value


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
            username = node['data']['name']
            url = 'https://twitter.com/%s/profile_image?size=original' % (
                urllib.quote(username), )
            safe_name = safe_path(username, True)
            path = os.path.join('profileimages', 'twitter', safe_name[:2])
            relpath = os.path.join('..', path)
            if os.path.exists(relpath):
                files = [file for file in os.listdir(relpath)
                         if file.split('.')[0] == safe_name]
                if len(files) and os.path.exists(
                        os.path.join(relpath, files[0])):
                    if os.path.getsize(os.path.join(relpath, files[0])):
                        url = os.path.join(path, files[0])
                    else:  # We know we don't have a valid image
                        continue
            node['data']['profile_image'] = url
    if singleton:
        result = nodes[0] if len(nodes) else None
    else:
        result = nodes
    return bson.json_util.dumps(result)
