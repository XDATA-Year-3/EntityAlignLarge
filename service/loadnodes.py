import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string


import networkx as nx



def run(host,database,graphname):
    # Create an empty response object.
    response = {}

   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents a list of all nodes in the graph

    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    namehint_coll_name = 'topk_names_'+graphname 
    collection = db[namehint_coll_name]
     
    # loop through the records in the network and take the appropriate action for each type. Suppress
    # the ID field because it doesn't serialize in JSON
    
    nodes = collection.find({},{'_id':0})
    namelist = []
    for x in nodes:
        if x['name'][:3] != 'id_':
            namelist.append(x['name'])

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = namelist
    client.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
