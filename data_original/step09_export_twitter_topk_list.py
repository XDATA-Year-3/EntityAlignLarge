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

# open the output file
outfile = open('resonant_Net_Align_twitter_handles.csv', 'w')
     
# loop through the records in the topk and generate a duplication collection with the ga and gb entries reversed, it is safer
# than changing the application logic

nodes = read_collection.find({},{'_id':0})

print 'scanning through topk collection'
print 'found ',nodes.count(), ' topk records'

nodelist = []
for x in nodes:
	nodelist.append(x['ga'])
# now make it a unique list
uniquenodes = set(nodelist)
uniquelist = list(uniquenodes)

count = 0
loopcount = 0
outstring = ''
for x in uniquelist:
	if loopcount == 0:
		outstring = x
	else:
 		outstring = outstring+', '+x
 	loopcount += 1
 	if loopcount>10:
 		#print outstring
 		outfile.write(outstring)
 		outfile.write("\n")
 		outstring = ''
 		loopcount = 0
 	count += 1
 	#if count > 100:
 		#break
print 'wrote ',count, ' records into ',write_collection_name
outfile.close()