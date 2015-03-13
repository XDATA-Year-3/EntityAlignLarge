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

   # look through the collections in the ivaan database and return the name of all collections
   # that match the naming profile for tables.  This is matching to see if the collection name
   # begins with "table_"

    connection = Connection(host, 27017)
    db = connection[database]
    # get a list of all collections (excluding system collections)
    collection = db[graphname]
    

    # read ugly, hacked adjacency list format and convert back to networkX object
    result_json = collection.find({},{'_id':0})[0]
    graph = nx.convert.from_dict_of_dicts(result_json)
    #print graph.adj

    fixedNodes = []
    for node in graph.nodes():
        fixedNodes.append({'name':node,'group':1})

    fixedEdges = []
    for edge in graph.edges():
        fixedEdges.append({'source':int(edge[0]),'target': int(edge[1]),'weight':1})


    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = fixedNodes
    response['result']['links'] = fixedEdges
    connection.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
