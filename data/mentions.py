import json
from pymongo import MongoClient
import sys


class Tag:
    def __init__(self):
        self.count = -1

    def next(self):
        self.count += 1
        return str(self.count)


def main():
    print >>sys.stderr, "reading mentions...",
    sys.stderr.flush()
    with open(sys.argv[1]) as f:
        mentions = json.loads(f.read())
    print >>sys.stderr, "%d users" % (len(mentions))

    names = mentions.keys()
    nametable = {}
    tag = Tag()

    print >>sys.stderr, "adding names..."
    for i, n in enumerate(names):
        id = tag.next()
        sys.stdout.write("," if i > 0 else "[")
        print json.dumps({"_id": {"$oid": id},
                          "type": "node",
                          "data": {"username": n}})
        nametable[n] = id

        if i % 500 == 0:
            print >>sys.stderr, "\r%d/%d (%.1f%%)" % (i, len(names), 100.*i/len(names)),
    print >>sys.stderr

    print >>sys.stderr, "adding mention links..."
    for i, n in enumerate(names):
        n_id = nametable[n]

        onehop = mentions.get(n, {}).keys()
        twohop = [mentions.get(x, {}).keys() for x in onehop]

        nbrs = set(onehop + sum(twohop, []))
        for nbr in nbrs:
            if nbr not in nametable:
                id = tag.next()
                print json.dumps({"_id": {"$oid": id},
                                  "type": "node",
                                  "data": {"username": nbr}})
                nametable[nbr] = id

            print json.dumps({"_id": {"$oid": tag.next()},
                              "type": "link",
                              "source": n_id,
                              "target": nametable[nbr]})

        if i % 500 == 0:
            print >>sys.stderr, "\r%d/%d (%.1f%%)" % (i, len(names), 100.*i/len(names)),
    print >>sys.stderr

    print "]"


if __name__ == "__main__":
    sys.exit(main())
