import bson.json_util
import json
import math
import numpy
import pymongo
import scipy.linalg
import sys
import time

from findNodes import run as find_nodes
from neighborhood import run as get_neighborhood


class Cache:
    def __init__(self, radius, namefield, host, db, coll):
        self.radius = radius
        self.namefield = namefield
        self.host = host
        self.db = db
        self.coll = coll
        self.cache = {}

    def get(self, handle):
        if handle not in self.cache:
            node = bson.json_util.loads(find_nodes(host=self.host, db=self.db, coll=self.coll, spec=json.dumps({self.namefield: handle}), singleton=json.dumps(True)))
            self.cache[handle] = signature(get_neighborhood(host=self.host, db=self.db, coll=self.coll, center=node["_id"], radius=self.radius))

        return self.cache[handle]


def adjacency_matrix(g):
    index_map = {h: i for i, h in enumerate([x["_id"]["$oid"] for x in g["nodes"]])}
    links = ({"source": index_map[x["source"]], "target": index_map[x["target"]]} for x in g["links"])

    m = numpy.eye(len(g["nodes"]))

    for link in links:
        s = link["source"]
        t = link["target"]

        m[s][t] = m[t][s] = 1.0

    return m


def signature(g):
    m = adjacency_matrix(g)
    return {"det": scipy.linalg.det(m),
            "trace": numpy.trace(m)}


def norm2(v):
    def sq(x):
        return x*x

    return math.sqrt(sq(v[0]) + sq(v[1]))


def similarity(s1, s2):
    return math.pow(1.01, -norm2([s1["det"] - s2["det"], s1["trace"] - s2["trace"]]))


def process(db, source, source_namefield, target, target_namefield):
    source_cache = Cache(2, source_namefield, "localhost", db, source)
    target_cache = Cache(2, target_namefield, "localhost", db, target)

    print "Computing %s -> %s" % (source, target)

    topk = pymongo.MongoClient("localhost")[db]["topk_%s_%s" % (source, target)]
    records = topk.find(timeout=False)
    count = records.count()

    print "%d records" % (count)

    start = time.time()

    for i, rec in enumerate(records):
        if "2spectral" not in rec:
            rec["2spectral"] = similarity(source_cache.get(rec["ga"]), target_cache.get(rec["entity"]))
            topk.save(rec)

        if i % 10 == 0 and i > 0:
            elapsed = time.time() - start
            estimated = (elapsed / i) * count - elapsed
            m, s = divmod(estimated, 60)
            h, m = divmod(m, 60)

            print "%d of %d records complete (time remaining: %02d:%02d:%02d)" % (i, count, h, m, s)


def main():
    db = "july"

    twitter = "twitter_nodelink"
    twitter_namefield = "user_name"

    instagram = "instagram_nodelink"
    instagram_namefield = "user_name"

    #process(db, twitter, twitter_namefield, instagram, instagram_namefield)
    process(db, instagram, instagram_namefield, twitter, twitter_namefield)


if __name__ == "__main__":
    sys.exit(main())
