


import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import random 
import itertools
import sys



# ----------- definition of routine to return the size of an n-hop network ---------

def extractKHopSocialNetworkSize(host, database, collection, center=None, degree=None):
    response = {}

     # Get a handle to the database collection.
    try:
        connection = pymongo.Connection(host)
        db = connection[database]
        c = db[collection]
    except pymongo.errors.AutoReconnect as e:
        response["error"] = "database error: %s" % (e.message)
        return response

    # Bail with error if any of the required arguments is missing.
    missing = map(lambda x: x[0], filter(lambda x: x[1] is None, zip([ "center", "degree"], [ center, degree])))
    if len(missing) > 0:
        response["error"] = "missing required arguments: %s" % (", ".join(missing))
        return response

    # Cast the arguments to the right types.
    #
    # The degree is the degree of separation between the center element and the
    # retrieved nodes - an integer.
    try:
        degree = int(degree)
    except ValueError:
        response["error"] = "argument 'degree' must be an integer"
        return response

    # Start a set of all interlocutors we're interested in - that includes the
    # center tweeter.
    talkers = set([center])

    # Also start a table of distances from the center.
    distance = {center: 0}

    current_talkers = list(talkers)
    all_results = []
    for i in range(degree):
        # Construct and send a query to retrieve all records involving the
        # current talkers, occurring within the time bounds specified, and
        # involving two known addresses.
        query = {"$and": [ {"source": {"$ne": ""} },
            {"target": {"$ne": ""} },
            {"$or": [
                {"source": {"$in": current_talkers} },
                {"target": {"$in": current_talkers} }
                ]
            }
            ]
        }
        results = c.find(query, fields=["target", "source"])
        results.rewind()

        # Collect the names.
        #current_talkers = list(set(map(lambda x: x["target"] if x["source"] == center else x["source"], results)))
        current_talkers = list(itertools.chain(*map(lambda x: [x["target"], x["source"]], results)))
        talkers = talkers.union(current_talkers)

        # Compute updates to everyone's distance from center.
        for t in current_talkers:
            if t not in distance:
                distance[t] = i+1

        # Rewind and save the cursor.
        results.rewind()
        all_results.append(results)

    # Construct a canonical graph structure from the set of talkers and the list
    # of tweets.
    #
    # Start with an index map of the talkers.
    talkers = list(talkers)
    talker_index = {name: index for (index, name) in enumerate(talkers)}

    # Create a chained iterable from all the rewound partial results.
    all_results = itertools.chain(*all_results)

    # Create a list of graph edges suitable for use by D3 - replace each record
    # in the data with one that carries an index into the tweeters list.
    edges = []
    for result in all_results:
        source = result["source"]
        target = result["target"]
        #ident = str(result["_id"])
        rec = { "source": talker_index[source],
                "target": talker_index[target]}
                #"id": ident }
        edges.append(rec)
        
    talkers = [{"tweet": n, "distance": distance[n]} for n in talkers]

    # Stuff the graph data into the response object, and return it.
    response["result"] = { "nodes": talkers,
                           "edges": edges }
    connection.close()
    # return the total size of the community, not the detail of the community
    return len(response['result']['nodes'])



connection2 = pymongo.Connection('localhost')
db = connection2['july']
edge_collection = db['twitter_mentions']
out_collection = db['twitter_mentions_hop_analysis']

# now loop through the vertices in this database 
records = edge_collection.find(timeout=False)
namelist = []
for record in records:
    namelist.append(record['source'])
    namelist.append(record['target'])
print 'namelist length = ',len(namelist)
# remove duplicates
cleanlist = set(namelist)
print 'uniquelist length = ',len(cleanlist)
sys.stdout.flush()
# now process the 1,2,3 hop information to characterize the dataset
for name in cleanlist:    
    Onehop = extractKHopSocialNetworkSize('localhost', 'july_test','twitter_mentions',name, 1)
    Twohop = extractKHopSocialNetworkSize('localhost', 'july_test','twitter_mentions',name, 2)
    #Threehop = extractKHopSocialNetworkSize('localhost', 'year3_ea_twitter','twitter_geosample_mentions_full',name, 3)
    outrecord = {'entity': name, '1hop': Onehop, '2hop' : Twohop}
    out_collection.insert(outrecord)
   