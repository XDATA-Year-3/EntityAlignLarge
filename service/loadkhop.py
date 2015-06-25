import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo
import itertools
import networkx as nx



def run(host,database,graphname,centername,degree=2):
    # Create an empty response object.
    response = {}
    collectionNames = []
    centerid = 0

    print 'looking for one-hop around:',centername, 'in graph',graphname
   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents the graph to the application.  It might be faster to adopt to using a standard 
   # networkX JSON description, but this is certainly simple and flexible for an initial prototype.

    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    c = db[graphname]

    # first find the node ID of the denter
    centerrecord = c.find_one({'data.name':centername},fields=['data.id'])
    center = centerrecord['data']['id']
    print 'found center id:',center

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
        query = {"$or": [
                    {"data.source": {"$in": current_talkers} },
                    {"data.target": {"$in": current_talkers} }
                    ]
        }
        #print "query:",query
        results = c.find(query, fields=["data.target", "data.source"])
        #print 'results:'
        #for r in results:
        #    print r
        results.rewind()
        #print 'end results'

        # Collect the names.
        #current_talkers = list(set(map(lambda x: x["target"] if x["source"] == center else x["source"], results)))
        current_talkers = list(itertools.chain(*map(lambda x: [x['data']["target"], x['data']["source"]], results)))
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
    #print 'talkers:',talkers
    #print 'talker_index:',talker_index

    # Create a chained iterable from all the rewound partial results.
    all_results = itertools.chain(*all_results)
    print 'all results:',all_results

    # Create a list of graph edges suitable for use by D3 - replace each record
    # in the data with one that carries an index into the tweeters list.
    edges = []
    for result in all_results:
        source = result['data']["source"]
        target = result['data']["target"]
        #ident = str(result["_id"])
        rec = { "source": source,
                "target": target}
                #"id": ident }
        edges.append(rec)
        
    talkers = [{"id": n, "distance": distance[n],'group':1} for n in talkers]

    #fixedNodes = []
    #for node in talkers:
    #    centerrecord = c.find_one({'data.id':node})        
    #    fixedNodes.append({'name' : centerrecord['data']['name'],  'id': node['id'],'data': centerrecord['data'], 'distance':node['distance']})

    print 'edges:',edges
    fixedEdges = []
    for edge in edges:
        fixedEdges.append({'source':int(edge['source']),'target': int(edge['target']),'weight':1})
    # Stuff the graph data into the response object, and return it.
    
    client.close()
    
    response =  dict()
    response["edges"] =  fixedEdges
    response["nodes"] = talkers

    print 'response returned:'
    print response

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
