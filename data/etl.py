import bson.json_util
import datetime
import heapq
import json
from pymongo import MongoClient
import sys
import time


def display_time(s):
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    return "%02d:%02d:%02d" % (h, m, s)


def ingest_matches(f):
    def slim(r):
        rr = json.loads(r)
        return (rr["twitter_name"], rr["instagram_name"])

    return [slim(r) for r in f]


def minmax(vals):
    mx = float("-inf")
    mn = float("inf")

    for v in map(float, vals):
        if v < mn:
            mn = v
        if v > mx:
            mx = v

    return (mn, mx)


def main():
    matchfile = sys.argv[1]
    host = "localhost"
    db = "year3_challenge2_v6"
    tcoll = "twitter_msg"
    icoll = "instagram_msg"

    matches = ingest_matches(open(matchfile))

    print >>sys.stderr, "%d matches" % (len(matches))

    # Collect twitter and instagram names.
    twitter_names = set()
    instagram_names = set()
    for (twitter, instagram) in matches:
        twitter_names.add(twitter)
        instagram_names.add(instagram)

    mongo = MongoClient(host)[db]

    # Get the listed twitter users' data.
    try:
        with open("twitter.etl.json") as f:
            print >>sys.stderr, "Reading twitter data from disk..."
            twitter = bson.json_util.loads(f.read())
    except IOError:
        tmongo = mongo[tcoll]
        twitter = {}
        for i, t in enumerate(twitter_names):
            cursor = tmongo.find({"user_name": t})
            twitter[t] = list(cursor)

            if i % 100 == 0:
                print >>sys.stderr, "\rTwitter users: %d/%d (%.1f%%)" % (i, len(twitter_names), 100.*i/len(twitter_names)),
                sys.stderr.flush()
        print >>sys.stderr, ""

        print >>sys.stderr, "Writing to disk..."
        sys.stderr.flush()

        with open("twitter.etl.json", "w") as f:
            f.write(bson.json_util.dumps(twitter, indent=4, separators=(",", ": ")))

    # Get the listed twitter users' data.
    try:
        print >>sys.stderr, "Reading instagram data from disk..."
        with open("instagram.etl.json") as f:
            instagram = bson.json_util.loads(f.read())
    except IOError:
        imongo = mongo[icoll]
        instagram = {}
        for i, t in enumerate(instagram_names):
            cursor = imongo.find({"user_name": t})
            instagram[t] = list(cursor)

            if i % 100 == 0:
                print >>sys.stderr, "\rInstagram users: %d/%d (%.1f%%)" % (i, len(instagram_names), 100.*i/len(instagram_names)),
                sys.stderr.flush()
        print >>sys.stderr, ""

        print >>sys.stderr, "Writing to disk..."
        sys.stderr.flush()

        with open("instagram.etl.json", "w") as f:
            f.write(bson.json_util.dumps(instagram, indent=4, separators=(",", ": ")))

    # Geographical bounding box.
    def geobb(msgs):
        lats = minmax(x["latitude"] for x in msgs)
        lons = minmax(x["longitude"] for x in msgs)

        return (lats, lons)

    def message_histogram(msgs):
        data = {}

        for m in msgs:
            date = datetime.datetime.fromtimestamp(m["msg_date"])
            date = "%d-%d-%d" % (date.year, date.month, date.day)

            data[date] = data.get(date, 0) + 1

        for date in data:
            data[date] /= float(len(msgs))

        return data

    def longest_common_substring(s1, s2):
        m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
        longest, x_longest = 0, 0 
        for x in xrange(1, 1 + len(s1)): 
            for y in xrange(1, 1 + len(s2)):
                if s1[x - 1] == s2[y - 1]: 
                    m[x][y] = m[x - 1][y - 1] + 1 
                    if m[x][y] > longest: 
                        longest = m[x][y]
                        x_longest = x 
                else: 
                    m[x][y] = 0 
        return s1[x_longest - longest: x_longest]


    def levenshtein(a,b):
        "Calculates the Levenshtein distance between a and b."
        n, m = len(a), len(b)
        if n > m:
            # Make sure n <= m, to use O(min(n,m)) space
            a,b = b,a
            n,m = m,n
            
        current = range(n+1)
        for i in range(1,m+1):
            previous, current = current, [i]+[0]*n
            for j in range(1,n+1):
                add, delete = previous[j]+1, current[j-1]+1
                change = previous[j-1]
                if a[j-1] != b[i-1]:
                    change = change + 1
                current[j] = min(add, delete, change)
                
        return current[n]


    # Compute the data needed for the metrics.
    #
    # Twitter...
    twitter_data = {}
    for i, t in enumerate(twitter):
        rec = twitter[t]

        twitter_data[t] = {}
        twitter_data[t]["geobb"] = geobb(rec)
        twitter_data[t]["msghist"] = message_histogram(rec)

        if i % 100 == 0:
            print >>sys.stderr, "\rTwitter metadata: %d/%d (%.1f%%)" % (i, len(twitter), 100.*i/len(twitter)),
            sys.stderr.flush()
    print >>sys.stderr, ""

    # ...and instagram.
    instagram_data = {}
    for i, t in enumerate(instagram):
        rec = instagram[t]

        instagram_data[t] = {}
        instagram_data[t]["geobb"] = geobb(rec)
        instagram_data[t]["msghist"] = message_histogram(rec)

        if i % 100 == 0:
            print >>sys.stderr, "\rInstagram metadata: %d/%d (%.1f%%)" % (i, len(instagram), 100.*i/len(instagram)),
            sys.stderr.flush()
    print >>sys.stderr, ""

    # Compute cross-data metrics, and maintain heaps of their values.
    metrics = {}
    topk_ti = {}
    start = time.time()
    for i, twit in enumerate(twitter_names):
        area_heap = []
        freq_heap = []
        lev_heap = []
        substring_heap = []

        for j, inst in enumerate(instagram_names):
            metric = metrics[json.dumps([twit, inst])] = {"id": json.dumps([twit, inst])}

            tdata = twitter_data[twit]
            idata = instagram_data[inst]

            # Geographical overlap.
            tlats, tlons = tdata["geobb"]
            ilats, ilons = idata["geobb"]

            first, second = (tlats, ilats) if tlats[0] < ilats[0] else (ilats, tlats)

            if first[1] < second[0]:
                height = 0.0
            else:
                height = min(first[1], second[1]) - second[0]

            first, second = (tlons, ilons) if tlons[0] < ilons[0] else (ilons, tlons)

            if first[1] < second[0]:
                width = 0.0
            else:
                width = min(first[1], second[1]) - second[0]

            try:
                metric["area"] = 2.0 * (width * height) / ((tlons[1] - tlons[0]) * (tlats[1] - tlats[0]) + (ilons[1] - ilons[0]) * (ilats[1] - ilats[0]))
            except ZeroDivisionError:
                metric["area"] = 0.0

            # Posting frequency overlap.
            thist = tdata["msghist"]
            ihist = idata["msghist"]

            a, b = (thist, ihist) if len(thist.keys()) < len(ihist.keys()) else (ihist, thist)

            score = 0.0
            for date in a:
                if date in b:
                    score += a[date]*b[date]

            metric["freq"] = score

            # Levenshtein distance between usernames.
            metric["lev"] = (len(twit) + len(inst) - levenshtein(twit, inst)) / float(len(twit) + len(inst))

            # Substring match between usernames.
            metric["substring"] = 2.0 * len(longest_common_substring(twit, inst)) / (len(twit) + len(inst))

            # Add values to the heaps.
            heapq.heappush(area_heap, (metric["area"], metric))
            heapq.heappush(freq_heap, (metric["freq"], metric))
            heapq.heappush(lev_heap, (metric["lev"], metric))
            heapq.heappush(substring_heap, (metric["substring"], metric))

            if j % 500 == 0:
                now = time.time()
                n_t = len(twitter_names)
                n_i = len(instagram_names)
                cur = i*n_i + j
                total = n_t*n_i
                print >>sys.stderr, "\rCross-data metrics (elapsed - %s, remaining - %s): %d/%d (twitter) %d/%d (instagram) (%.2f%%)" % (display_time(now - start), display_time((now - start) / max(cur,1) * total - (now - start)), i, n_t, j, n_i, 100.*cur/total),
                sys.stderr.flush()

        # Collect the top-k from each heap into a single list.
        for heap in [area_heap, freq_heap, lev_heap, substring_heap]:
            for entry in heapq.nlargest(20, heap):
                topk_ti[entry[1]["id"]] = entry[1]
    print >>sys.stderr, ""

    # Run the instagram-twitter metric top-k.
    #
    # This should go much faster because we cached all the (symmetric) metrics
    # already.
    topk_it = {}
    for i, inst in enumerate(instagram_names):
        area_heap = []
        freq_heap = []
        lev_heap = []
        substring_heap = []

        for j, twit in enumerate(twitter_names):
            metric = metrics[json.dumps([twit, inst])]

            # Add values to the heaps.
            heapq.heappush(area_heap, (metric["area"], metric))
            heapq.heappush(freq_heap, (metric["freq"], metric))
            heapq.heappush(lev_heap, (metric["lev"], metric))
            heapq.heappush(substring_heap, (metric["substring"], metric))

            if j % 500 == 0:
                now = time.time()
                n_t = len(twitter_names)
                n_i = len(instagram_names)
                cur = i*n_t + j
                total = n_t*n_i
                print >>sys.stderr, "\rCross-data metrics (elapsed - %s, remaining - %s): %d/%d (instagram) %d/%d (twitter) (%.2f%%)" % (display_time(now - start), display_time((now - start) / max(cur,1) * total - (now - start)), i, n_i, j, n_t, 100.*cur/total),
                print >>sys.stderr, "\rCross-data metrics: %d/%d (instagram) %d/%d (twitter) (%.2f%%)" % (i, len(twitter_names), j, len(instagram_names), 100.*(i*len(instagram_names) + j)/(len(twitter_names)*len(instagram_names))),
                sys.stderr.flush()

        # Collect the top-k from each heap into a single list.
        for heap in [area_heap, freq_heap, lev_heap, substring_heap]:
            for entry in heapq.nlargest(20, heap):
                topk_it[entry[1]["id"]] = entry[1]
    print >>sys.stderr, ""

    # Dump out a json record of these entries.
    with open("topk_twitter_instagram.etl.json", "w") as f:
        print >>f, "["
        for i, v in enumerate(topk_ti.values()):
            names = json.loads(v["id"])
            v["twitter"] = names[0]
            v["instagram"] = names[1]
            del v["id"]

            print >>f, "%s%s" % ("," if i > 0 else "", json.dumps(v, separators=(",",":")))
        print >>f, "]"

    with open("topk_instagram_twitter.etl.json", "w") as f:
        print >>f, "["
        for i, (k, v) in enumerate(topk_it.iteritems()):
            names = json.loads(k)
            v["twitter"] = names[0]
            v["instagram"] = names[1]

            print >>f, "%s%s" % ("," if i > 0 else "", json.dumps(v, separators=(",",":")))
        print >>f, "]"


if __name__ == "__main__":
    sys.exit(main())
