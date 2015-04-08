import bson
import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import tangelo

import networkx as nx



def run(host,database,seedsname):
    # Create an empty response object.
    response = {}
    collectionNames = []

   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents the graph to the application.  It might be faster to adopt to using a standard 
   # networkX JSON description, but this is certainly simple and flexible for an initial prototype.

    connection = Connection(host, 27017)
    db = connection[database]
    # get a list of all collections (excluding system collections)
    collection = db[seedsname]
    
    # create an empty list to fill from the collection
    seeds = []

    # loop through the records in the network and take the appropriate action for each type
    for record in collection.find({},{'_id':0}):
        # processing for nodes.  Add node to graph, then add attributes
        if (record['type']=='seed'):
           seeds.append(record)

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['seeds'] = seeds
    connection.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
