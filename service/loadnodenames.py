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
    collection = db[graphname]
     
    # loop through the records in the network and take the appropriate action for each type. Suppress
    # the ID field because it doesn't serialize in JSON

    nodes = collection.find({'type':'node'},{'_id':0})
    namelist = []
    for x in nodes:
        namelist.append(x['data']['name'])

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = namelist
    client.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
