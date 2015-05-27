import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo



def run(handle):
    # Create an empty response object.
    response = {}

   # look through the collections in the ivaan database and return the name of all collections
   # that match the naming profile for tables.  This is matching to see if the collection name
   # begins with "seeds_" or not, since this routine can return the matching graphs (that don't start
    # with 'seeds_') or the matching seeds.

    host = 'localhost'
    database = 'year3_graphs'
    
    client = MongoClient(host, 27017)
    db = client[database]
    topk_collection = db['topk']

    # get a list of all collections (excluding system collections)
    query = {'ga':handle}
    tablerows = []
    # return only the columns to potentially display in LineUp.  We don't want to return the gA entity we used to search by
    topk = topk_collection.find(query,{'_id':0,'ga':0})
    for row in topk:
        tablerows.append(row)

    client.close()

    # Pack the results into the response object, and return it.
    response['result'] = tablerows

    # Return the response object.
    tangelo.log(str(response))
    return json.dumps(response)
