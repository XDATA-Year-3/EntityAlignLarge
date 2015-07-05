import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo


def run(host,database,graphname):
    # Create an empty response object.
    response = {}
    collectionNames = []

   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents the graph to the application.  It might be faster to adopt to using a standard 
   # networkX JSON description, but this is certainly simple and flexible for an initial prototype.

    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    collection = db[graphname]
    
   
    # loop through the records in the network and take the appropriate action for each type
    nodecount = collection.find({'type':'node'}).count()
    edgecount = collection.find({'type':'link'}).count()


    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = nodecount
    response['result']['links'] = edgecount
    client.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
