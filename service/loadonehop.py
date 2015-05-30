import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo

import networkx as nx





def run(host,database,graphname,centername):
    # Create an empty response object.
    response = {}
    collectionNames = []
    centerid = 0

    print 'looking for one-hop around:',centername
   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents the graph to the application.  It might be faster to adopt to using a standard 
   # networkX JSON description, but this is certainly simple and flexible for an initial prototype.

    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    collection = db[graphname]
    
    # create an empty graph to fill from the collection
    graph = nx.Graph()

    # loop through the records in the network and take the appropriate action for each type
    for record in collection.find({'type':'node'},{'_id':0}):
        # processing for nodes.  Add node to graph, then add attributes
            #print 'node:',record
        if 'name' in record['data']:
            if record['data']['name'] == centername:
                centerid = record['data']['id']
                centername = record['data']['name']
                graph.add_node(centerid)
                #print 'one hop: found node id:',centerid, 'node record:',record
                for attrib in record['data']:
                    # don't need the test here because of _id suppression at the query above
                    #if (attrib != '_id'):
                    graph.node[centerid][attrib] = record['data'][attrib]
                    #print 'added',attrib,'to ',centerid,' record now:',graph.node[centerid]
    #print nx.info(graph,n=centerid)

    # go through the links in the network and output any which are connected to te central node. Also output
    # the other node involved so a complete one-hop graph is generated

    query = {'$and': [{'type':'link'},{'$or': [{'data.source':centerid},{'data.target':centerid}]}]}
    #for record in collection.find({'type':'link'},{'_id':0}): 
    for record in collection.find(query,{'_id':0}):                   
        source = record['data']['source']
        target = record['data']['target']
        print 'source,target, centerid:',source,target,centerid
        edgeToAdd = False
        # examine this edge to see if it connects to the center node, if so, add it to the output graph
        if (source == centerid):
            graph.add_edge(source,target)
            nodetoadd = target
            edgeToAdd = True
        if  (target == centerid):
            graph.add_edge(source,target)            
            nodetoadd = source
            edgeToAdd = True

        # this is called when a node is entererd into the one-hop graph by edge reference. We need
        # to do a mongo query to get the full attribute information for the node.  There will only be 
        # one node record, so we can index to [0] in the mongo cursor instance to pull out the record.

        if edgeToAdd == True:
            graph.add_node(nodetoadd)
            noderecord = collection.find({'type':'node','data.id':nodetoadd},{'_id':0})
            for attrib in noderecord[0]['data']:
                #print 'adding', attrib, ' to node',nodetoadd
                graph.node[nodetoadd][attrib] = noderecord[0]['data'][attrib]

        # now add any attributes that were on the edge
        for attrib in record['data']:
            if (attrib not in ['source','target']):
                graph.edge[source][target][attrib] = record['data'][attrib]

    # prepare the records to return to the calling program.  We build a list of nodes
    # and a list of edges here.  All the original node data for each node is added as 
    # a 'data' field to preserve all attributes.  We might decide on a better way later or
    # decide to just return the JSON version of the graph directly instead of building edge and 
    # node lists.

    print 'one-hop graph finished'
    print nx.info(graph)

    fixedNodes = []
    for node in graph.nodes(data=True):
        #print 'one-hop node:',node
        if 'name' in node[1]:
            fixedNodes.append({'name' : node[1]['name'], 'id': node[1]['id'],'data': node, 'group':1})
        else:
            fixedNodes.append({'name' : node[1]['id'],  'id': node[1]['id'],'data': node, 'group':2})

    fixedEdges = []
    for edge in graph.edges():
        print "found edge: ",edge
        fixedEdges.append({'source':int(edge[0]),'target': int(edge[1]),'weight':1})
    #print fixedEdges
    #print fixedNodes

    # add a "matched" node to test rendering colors artificially
    #fixedNodes[24]['matched'] = 12

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['links'] = fixedEdges
    response['result']['nodes'] = fixedNodes

    client.close()

    print 'response returned:'
    print response

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
