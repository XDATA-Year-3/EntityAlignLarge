import bson
import pymongo
import json
from bson import ObjectId
from pymongo import MongoClient
import string

database = 'july'
read_collection_name = 'topk_twitter_nodelink_instagram_nodelink'
write_collection_name = 'topk_instagram_nodelink_twitter_nodelink'

client = MongoClient('localhost', 27017)
db = client[database]
read_collection = db[read_collection_name]
write_collection = db[ write_collection_name]
     
# loop through the records in the topk and generate a duplication collection with the ga and gb entries reversed, it is safer
# than changing the application logic

nodes = read_collection.find({},{'_id':0})

print 'scanning through topk collection'
print 'found ',nodes.count(), ' topk records'
count = 0
for x in nodes:
 	outrecord = {}
 	# first copy all the content
 	for attrib in x.keys():
 		outrecord[attrib] = x[attrib]
 	# then reverse the index keys
 	outrecord['entity'] = x['ga']
 	outrecord['ga'] = x['entity']
 	#print outrecord
	write_collection.insert(outrecord)
	count += 1
print 'wrote ',count, ' records into ',write_collection_name
