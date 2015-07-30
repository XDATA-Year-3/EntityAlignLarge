from pymongo import MongoClient
import heapq
import sys
import json



#----------------------- initialization of mongo collection connections ------------


client = MongoClient("localhost")


challenge_db = client['july']

read_coll = challenge_db['topk_ground_truth2_instagram_nodelink']
write_coll = challenge_db['topk_twitter_nodelink_instagram_nodelink']

read_coll2 = challenge_db['topk_matches2_ground_truth2_twitter_nodelink']
write_coll2 = challenge_db['topk_instagram_nodelink_twitter_nodelink']


# -------------- main processing loop: 

count = 0

print 'collections set, starting traversal'
sys.stdout.flush()

'''
print 'adding ground truth to t2i top-k'
matches = read_coll.find({},timeout=False)
for m in matches:
    write_coll.insert(m)
    count += 1
    #if count > 2:
    #    break    
print 'finished! Processed ', count, 'record pairs'

'''

count = 0
print 'adding ground truth to i2t top-k'
matches = read_coll2.find({},timeout=False)
for m in matches:
    write_coll2.insert(m)
    count += 1
    #if count > 2:
    #    break    
print 'finished! Processed ', count, 'record pairs'

client.close()
