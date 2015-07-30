from pymongo import MongoClient
import heapq
import sys
import json



#----------------------- initialization of mongo collection connections ------------


client = MongoClient("localhost")


challenge_db = client['july']

gnd_truth_coll = challenge_db['ground_truth2']
t2i_coll = challenge_db['topk_twitter_nodelink_instagram_nodelink']
i2t_coll = challenge_db['topk_instagram_nodelink_twitter_nodelink']
write_coll = challenge_db['ground_truth_t2i_verified']
write_coll2 = challenge_db['ground_truth_i2t_verified']
# -------------- main processing loop: 

count = 0

print 'collections set, starting traversal'
sys.stdout.flush()

'''
missing = found = 0
print 'adding ground truth to t2i top-k'
truth = gnd_truth_coll.find({},timeout=False)
for t in truth:
    matches = t2i_coll.find({'ga':t['twitter_name'],'apriori':1})
    if matches.count()>0:
        write_coll.insert(t)
        found += 1
    else:
        print 'missing t2i:',t
        missing += 1
    count +=1

print 't2i: found',found,'missing',missing
print 'finished! Processed ', count, 'record pairs'
'''

missing = found = 0
print 'adding ground truth to i2t top-k'
truth = gnd_truth_coll.find({},timeout=False)
for t in truth:
    matches = i2t_coll.find({'ga':t['instagram_name'],'apriori':1})
    if matches.count()>0:
        write_coll2.insert(t)
        found += 1
    else:
        print 'missing i2t:',t
        missing += 1
    count +=1

print 'i2t: found',found,'missing',missing
print 'finished! Processed ', count, 'record pairs'


client.close()
