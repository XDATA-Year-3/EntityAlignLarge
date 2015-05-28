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
    response['layout'] = {'primary': [   {'column': 'entity', 'width':100},{'column': 'lev','width':100}, {'column': 'substring','width':100},  {"type": "stacked","label": "Combined", "children": [{'column': 'lev','width':100}, {'column': 'substring','width':100}]}]}

    



    tangelo.log(str(response))
    return json.dumps(response)
