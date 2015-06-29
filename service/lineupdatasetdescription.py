import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string
import tangelo



def run(displaymode):
    # Create an empty response object.
    response = {}


    if (displaymode == 'left network only') or (displaymode == 'right network only'):
        print "displaying left or right"
        # return fixed result to compare two datasets
        response['primaryKey'] = 'entity'
        response['separator'] = '\t'
        response['url'] = 'service/lineupdataset'
        response['columns'] = [ {'column': 'entity', 'type': 'string'}, {'column': '1hop','type':'number', 'domain':[0,1]}, {'column': '2hop','type':'number', 'domain':[0,1]}]
        response['layout'] = {'primary': [   {'column': 'entity', 'width':130},  {'column': '1hop','width':100}, {'column': '2hop','width':100}, {"type": "stacked","label": "Combined", "children": [{'column': '1hop','width':75}, {'column': '2hop','width':75}]}]}
    else:
        # return fixed result to compare two datasets
        print 'displaying centered'
        response['primaryKey'] = 'entity'
        response['separator'] = '\t'
        response['url'] = 'service/lineupdataset'
        response['columns'] = [ {'column': 'entity', 'type': 'string'}, {'column': 'apriori','type':'number', 'domain':[0,1]}, {'column': 'LSGM','type':'number', 'domain':[0,1]},{'column': 'lev','type':'number', 'domain':[0,1]},{'column': 'substring','type':'number', 'domain':[0,1]}, {'column': '1hop','type':'number', 'domain':[0,1]}, {'column': '2hop','type':'number', 'domain':[0,1]}]
        response['layout'] = {'primary': [   {'column': 'entity', 'width':100},{'column': 'LSGM','width':75},{'column': 'lev','width':75}, {'column': 'substring','width':75},  {'column': '1hop','width':50}, {'column': '2hop','width':50}, {"type": "stacked","label": "Combined", "children": [{'column': 'apriori','width':100},{'column': 'lev','width':50}, {'column': 'substring','width':50}, {'column': '1hop','width':50}, {'column': '2hop','width':50}]}]}

    #tangelo.log(str(response))
    return json.dumps(response)
