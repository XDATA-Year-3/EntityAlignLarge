import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string

database = 'july'
read_collection_name = 'topk_twitter_nodelink_instagram_nodelink'
read_coll_name2 = 'topk_instagram_nodelink_twitter_nodelink'
twitter_coll_name = 'topk_names_twitter_nodelink'
instagram_coll_name = 'topk_names_instagram_nodelink'

client = MongoClient('localhost', 27017)
db = client[database]
read_collection = db[read_collection_name]
read_collection2 = db[read_coll_name2]

twitter_collection = db[ twitter_coll_name]
instagram_collection = db[instagram_coll_name]

     
    # loop through the records in the topk and generate a 

nodes = read_collection.find({},{'_id':0})

ga_namelist = []
gb_namelist = []
print 'scanning through topk collection'
for x in nodes:
 	ga_namelist.append(x['ga'])

nodes = read_collection2.find({},{'_id':0})
print 'scanning through topk collection'
for x in nodes:
 	gb_namelist.append(x['ga'])

print 'ga count:',len(ga_namelist), ' gb count:',len(gb_namelist)
ga_uniqueset = set(ga_namelist)
gb_uniqueset = set(gb_namelist)
ga_uniquenames = list(ga_uniqueset)
gb_uniquenames = list(gb_uniqueset)
print 'ga unique:',len(ga_uniquenames), ' gb unique:',len(gb_uniquenames)

for name in ga_uniquenames:
	twitter_collection.insert({'name': name})
for name in gb_uniquenames:
	instagram_collection.insert({'name':name})