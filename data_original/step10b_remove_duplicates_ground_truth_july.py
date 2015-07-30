from pymongo import MongoClient
import heapq
import sys
import json



#----------------------- initialization of mongo collection connections ------------

ga_dataset_name = 'ground_truth2'

gb_dataset_name = 'instagram_nodelink'

client = MongoClient("localhost")

# set up the databases
dba = client['july']
dbb = client['july']
challenge_db = client['july']

ga_coll = dba[ga_dataset_name]
gb_coll = dbb[gb_dataset_name]

#write_coll = challenge_db['topk_matches_'+ga_dataset_name+'_'+gb_dataset_name]
write_coll = challenge_db['topk_ground_truth2_instagram_nodelink']


# -------------- main processing loop: calculate separate quantities and write out for each pair
# -------------- of entities in the graphA and graphB collection that have proper names assigned

# how many candidate options do we want to be able to display as the 'top k' candidates?

k_value = 15

# this is a routine to find top-k matches for two string-based algorithms for each node in a graph. 
count = 0
dupcount = 0

print 'collections set, starting traversal'
sys.stdout.flush()

# -- graphA node list: composed of instagram collection returns plus ground truth added in

historyDictionary = {}

matches = write_coll.find({},timeout=False)
for m in matches:
    #print m
    sys.stdout.flush()
    if (m['ga'] in historyDictionary):
        if (m['entity'] in historyDictionary[m['ga']]):
            write_coll.remove(m)
            dupcount += 1
    else:
        if m['ga'] in historyDictionary:
            historyDictionary[m['ga']].append(m['entity'])
        else:
            historyDictionary[m['ga']] = [m['entity']]
    
    if (count % 1000) == 0:
        print count

    count += 1
    #if count > 2:
    #    break
    
print 'finished! Processed ', count, 'record pairs'
print 'found ',dupcount,' duplicates'
client.close()
