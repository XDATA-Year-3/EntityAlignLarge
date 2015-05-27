import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo



def run():
    # Create an empty response object.
    response = {}

    # return a fixed result for now
    response['primaryKey'] = 'entity'
    response['separator'] = '\t'
    response['url'] = 'service/lineupdataset'
    response['columns'] = [ {'column': 'entity', 'type': 'string'},{'column': 'lev','type':'number', 'domain':[0,1]},{'column': 'substring','type':'number', 'domain':[0,1]}]
    response['layout'] = {'primary': [   {'column': 'entity', 'type': 'string'},{'column': 'lev','type':'number', 'domain':[0,1]}, {'column': 'substring','type':'number', 'domain':[0,1]}]}

    
    #client = MongoClient(host, 27017)
    #db = client[database]
    # get a list of all collections (excluding system collections)
    #collection_list = db.collection_names(False)
    #for coll in collection_list:
         # exclude the seeds collections
    #    if coll[:6] != 'seeds_':
    #        print "found graph:", coll
    #        collectionNames.append(coll)
    #client.close()

    # Return the response object.
    tangelo.log(str(response))
    return json.dumps(response)
