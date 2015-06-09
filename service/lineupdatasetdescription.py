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
    response['columns'] = [ {'column': 'entity', 'type': 'string'}, {'column': 'apriori','type':'number', 'domain':[0,1]}, {'column': 'lev','type':'number', 'domain':[0,1]},{'column': 'substring','type':'number', 'domain':[0,1]}, {'column': '1hop','type':'number', 'domain':[0,100]}, {'column': '2hop','type':'number', 'domain':[0,1000]}, {'column': '3hop','type':'number', 'domain':[0,5000]}]
    response['layout'] = {'primary': [   {'column': 'entity', 'width':100}, {'column': 'apriori', 'width':100},{'column': 'lev','width':75}, {'column': 'substring','width':75},  {'column': '1hop','width':50}, {'column': '2hop','width':50}, {'column': '3hop','width':50}, {"type": "stacked","label": "Combined", "children": [{'column': 'lev','width':50}, {'column': 'substring','width':50}, {'column': '1hop','width':50}, {'column': 'apriori','type':'number', 'domain':[0,1]}, {'column': '2hop','width':50}, {'column': '3hop','width':50}]}]}


    #tangelo.log(str(response))
    return json.dumps(response)
