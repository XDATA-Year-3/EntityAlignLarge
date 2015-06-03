import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo


def run(host,database):
    # Create an empty response object.
    response = {}
    collectionNames = ['select a dataset']

   # look through the collections in the ivaan database and return the name of all collections
   # that match the naming profile for tables.  This is matching to see if the collection name
   # begins with "seeds_" or not, since this routine can return the matching graphs (that don't start
    # with 'seeds_') or the matching seeds.
    
    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    collection_list = db.collection_names(False)
    for coll in collection_list:
         # exclude the seeds collections
        if (coll[:6] != 'seeds_') and (coll[:4] != 'topk'):
            print "found graph:", coll
            collectionNames.append(coll)

    client.close()

    # Pack the results into the response object, and return it.
    response['result'] = collectionNames

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
