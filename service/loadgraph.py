import bson
import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import tangelo

import networkx as nx



def run(host,database,graphname):
    # Create an empty response object.
    response = {}
    collectionNames = []

   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents the graph to the application.  It might be faster to adopt to using a standard 
   # networkX JSON description, but this is certainly simple and flexible for an initial prototype.

    connection = Connection(host, 27017)
    db = connection[database]
    # get a list of all collections (excluding system collections)
    collection = db[graphname]
    
    # create an empty graph to fill from the collection
    graph = nx.Graph()

    # loop through the records in the network and take the appropriate action for each type
    for record in collection.find({},{'_id':0}):
        # processing for nodes.  Add node to graph, then add attributes
        if (record['type']=='node'):
            #print 'node:',record
            thisid = record['data']['id']
            graph.add_node(thisid)
            for attrib in record['data']:
                if (attrib != '_id'):
                    #print 'adding attrib to node:',attrib
                    #thisid = record['data']['id']
                    #graph.add_node(thisid)
                    graph.node[thisid][attrib] = record['data'][attrib]
        elif (record['type'] == 'link'):
            #print 'link:',record
            source = record['data']['source']
            target = record['data']['target']
            graph.add_edge(source,target)
            for attrib in record['data']:
                if (attrib not in ['source','target']):
                    #print 'adding attrib to link:',attrib
                    graph.edge[source][target][attrib] = record['data'][attrib]

    # prepare the records to return to the calling program.  We build a list of nodes
    # and a list of edges here.  All the original node data for each node is added as 
    # a 'data' field to preserve all attributes.  We might decide on a better way later or
    # decide to just return the JSON version of the graph directly instead of building edge and 
    # node lists.

    fixedNodes = []
    for node in graph.nodes(data=True):
        if node[1]['name']:
        #if False:
            fixedNodes.append({'name' : node[1]['name'], 'id': node[1]['id'],'data': node, 'group':1})
        else:
            fixedNodes.append({'name' : node,  'id': node[1]['id'],'data': node, 'group':1})

    fixedEdges = []
    for edge in graph.edges():
        #print "found edge: [0] is:",edge[0]
        fixedEdges.append({'source':int(edge[0]),'target': int(edge[1]),'weight':1})

    # add a "matched" node to test rendering colors artificially
    #fixedNodes[24]['matched'] = 12

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = fixedNodes
    response['result']['links'] = fixedEdges
    connection.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
