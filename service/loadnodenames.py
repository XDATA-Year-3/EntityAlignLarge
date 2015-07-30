import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string


def run(host,database,graphname):
    # Create an empty response object.
    response = {}

   # this method traverses the documents in the selected graph collection and builds a JSON object
   # that represents a list of all nodes in the graph

    client = MongoClient(host, 27017)
    db = client[database]
    # get a list of all collections (excluding system collections)
    namehint_coll_name = 'topk_'+graphname+("_instagram" if graphname == "twitter" else "_twitter")
    print 'looking in collection',namehint_coll_name
    collection = db[namehint_coll_name]

    namelist = [x["ga"] for x in collection.find({"selfreport": 1})]
     
    # loop through the records in the network and take the appropriate action for each type. Suppress
    # the ID field because it doesn't serialize in JSON.  If the node is named, return the name,  else return
    # ID if there is an ID only

#    nodes = collection.find({},{'_id':0}).limit(99999)
    #namelist = []
    #for x in nodes:
        #if 'name' in x:
            #namelist.append(x['name'])
        #elif 'name' in x['data']:
            #namelist.append(x['data']['name'])
        #elif 'username' in x['data']:
            #namelist.append(x['data']['username'])
       

    # Pack the results into the response object, and return it.
    response['result'] = {}
    response['result']['nodes'] = namelist
    client.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
