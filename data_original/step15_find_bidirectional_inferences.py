from pymongo import MongoClient
import heapq
import sys
import json



#----------------------- initialization of mongo collection connections ------------


client = MongoClient("localhost")


challenge_db = client['july']

gnd_truth_coll = challenge_db['ground_truth2']
t2i_verified_coll = challenge_db['ground_truth_t2i_verified']
i2t_verified_coll = challenge_db['ground_truth_i2t_verified']
write_coll = challenge_db['ground_thruth_bidirectional']
# -------------- main processing loop: 

count = 0

print 'collections set, starting traversal'
sys.stdout.flush()


missing = found = 0
print 'adding ground truth to t2i top-k'
truth = t2i_verified_coll.find({},timeout=False)
for t in truth:
    matches = i2t_verified_coll.find({'twitter_name':t['twitter_name'],'instagram_name':t['instagram_name']})
    if matches.count()>0:
        write_coll.insert(t)
        found += 1
    else:
        print 'missing t2i:',t
        missing += 1
    count +=1

print 'bidirectional: found',found,'missing',missing
print 'finished! Processed ', count, 'record pairs'

