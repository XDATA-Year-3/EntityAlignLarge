from pymongo import MongoClient
import heapq
import sys


#----------------------- initialization of mongo collection connections ------------

topk_name = 'topk_twitter_nodelink_instagram_nodelink'
ga_hop_collection_name = 'twitter_mentions_hop_analysis'
gb_hop_collection_name = 'instagram_mentions_hop_analysis'

ground_truth_collection_name = 'ground_truth'

client = MongoClient("localhost")

# set up the databases
dba = client['july']
dbb = client['july']
challenge_db = client['july']

topk_coll = dba[topk_name]
ga_hop_collection = dba[ga_hop_collection_name]
gb_hop_collection = dbb[gb_hop_collection_name]
ground_truth_collection = dbb[ground_truth_collection_name]


# define a lookup in the ground truth collection that returns 1 if this pair is in the ground truth matches
def ground_truth_similarity(s1, s2):
    gt_match = ground_truth_collection.find({'$and':[{'twitter_name':s1},{'instagram_name':s2}]})
    return gt_match.count()


#----------------------- suppress false hop count matches ------------
# If the 1 hop count is 1, then it often means we don't have any other
# information about this entity. (e.g. they were a target of a message).  Therefore, detect the
# case where one or the other is all ones in order to handle these cases specially.  Two isolated nodes
# should match each other perfectly.  

def hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
    a_is_not_alone = ga_hopcount[0]['1hop'] != 1 
    b_is_not_alone = gb_hopcount[0]['1hop'] != 1
    return a_is_not_alone or b_is_not_alone


# -------------- main processing loop: calculate separate quantities and write out for each pair
# -------------- of entities in the graphA and graphB collection that have proper names assigned


# this is a routine to find top-k matches for two string-based algorithms for each node in a graph. 
count = 0
writecount = 0
goodcount = 0
clearcount = 0


print 'collections set, starting traversal'
sys.stdout.flush()

topk_cursor = topk_coll.find({},timeout=False)
print 'found', topk_cursor.count(), 'records'
outrecord = {}
for record in topk_cursor:

    # make an output record, then overwright some values
    for field in record:
        outrecord[field] = record[field]

    outrecord['apriori'] = ground_truth_similarity( record['ga'], record['entity'] )

    ga_hopcount = ga_hop_collection.find({'entity':record['ga']})
    gb_hopcount = gb_hop_collection.find({'entity':record['entity']})
    #print 'hop b:',entry,gb_hopcount[0]
    if (ga_hopcount.count()>0) and (gb_hopcount.count()>0) and hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
        outrecord['1hop'] = 1.0/(1.0+abs(ga_hopcount[0]['1hop']-float(gb_hopcount[0]['1hop'])))
        outrecord['2hop'] = 1.0/(1.0+abs(ga_hopcount[0]['2hop']-float(gb_hopcount[0]['2hop'])))
        goodcount += 1
    else:
        clearcount +=1
        outrecord['1hop'] = record['2hop']  = 0.0
    #print record
    topk_coll.update(record,outrecord)
    writecount +=1
    if (writecount % 500) == 0:
        print writecount,'ga=',record['ga'],'gb=',record['entity'] 
        
    #print record
    count += 1
    #if count > 35:
    #    break
    
print 'finished! Processed ', count, 'record pairs ' 
print 'changed', goodcount , 'clear:', clearcount
client.close()
