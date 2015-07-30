from pymongo import MongoClient
import heapq
import sys

#--------------- common substring comparison ------------

def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0 
    for x in xrange(1, 1 + len(s1)): 
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]: 
                m[x][y] = m[x - 1][y - 1] + 1 
                if m[x][y] > longest: 
                    longest = m[x][y]
                    x_longest = x 
            else: 
                m[x][y] = 0 
    return s1[x_longest - longest: x_longest]

# normalize result to be between 0 and 1
def substring_similarity(s1, s2):
    return 2.0 * len(longest_common_substring(s1, s2)) / (len(s1) + len(s2))

#------------ levenshtein -----------------

# This is a straightforward implementation of a well-known algorithm, and thus
# probably shouldn't be covered by copyright to begin with. But in case it is,
# the author (Magnus Lie Hetland) has, to the extent possible under law,
# dedicated all copyright and related and neighboring rights to this software
# to the public domain worldwide, by distributing it under the CC0 license,
# version 1.0. This software is distributed without any warranty. For more
# information, see <http://creativecommons.org/publicdomain/zero/1.0>


def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]


def lev_similarity(s1, s2):
    combined_length = len(s1) + len(s2)
    return (float(combined_length) - float(levenshtein(s1, s2)))/combined_length 

#--------------- ground truth comparison ---------------------------


# define a lookup in the ground truth collection that returns 1 if this pair is in the ground truth matches
def ground_truth_similarity(s1, s2):
    gt_match = ground_truth_collection.find({'$and':[{'twitter_name':s1},{'instagram_name':s2}]})
    return gt_match.count()


#--------------- neighborhood calculation---------------------------


import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import random 
import itertools

def extractKHopSocialNetworkSize(host, database, collection, center=None, degree=None):
    response = {}

     # Get a handle to the database collection.
    try:
        connection = pymongo.Connection(host)
        db = connection[database]
        c = db[collection]
    except pymongo.errors.AutoReconnect as e:
        response["error"] = "database error: %s" % (e.message)
        return response

    # Bail with error if any of the required arguments is missing.
    missing = map(lambda x: x[0], filter(lambda x: x[1] is None, zip([ "center", "degree"], [ center, degree])))
    if len(missing) > 0:
        response["error"] = "missing required arguments: %s" % (", ".join(missing))
        return response

    # Cast the arguments to the right types.
    #
    # The degree is the degree of separation between the center element and the
    # retrieved nodes - an integer.
    try:
        degree = int(degree)
    except ValueError:
        response["error"] = "argument 'degree' must be an integer"
        return response

    # Start a set of all interlocutors we're interested in - that includes the
    # center tweeter.
    talkers = set([center])

    # Also start a table of distances from the center.
    distance = {center: 0}

    current_talkers = list(talkers)
    all_results = []
    for i in range(degree):
        # Construct and send a query to retrieve all records involving the
        # current talkers, occurring within the time bounds specified, and
        # involving two known addresses.
        query = {"$and": [ {"source": {"$ne": ""} },
            {"target": {"$ne": ""} },
            {"$or": [
                {"source": {"$in": current_talkers} },
                {"target": {"$in": current_talkers} }
                ]
            }
            ]
        }
        results = c.find(query, fields=["target", "source"])
        results.rewind()

        # Collect the names.
        #current_talkers = list(set(map(lambda x: x["target"] if x["source"] == center else x["source"], results)))
        current_talkers = list(itertools.chain(*map(lambda x: [x["target"], x["source"]], results)))
        talkers = talkers.union(current_talkers)

        # Compute updates to everyone's distance from center.
        for t in current_talkers:
            if t not in distance:
                distance[t] = i+1

        # Rewind and save the cursor.
        results.rewind()
        all_results.append(results)

    # Construct a canonical graph structure from the set of talkers and the list
    # of tweets.
    #
    # Start with an index map of the talkers.
    talkers = list(talkers)
    talker_index = {name: index for (index, name) in enumerate(talkers)}

    # Create a chained iterable from all the rewound partial results.
    all_results = itertools.chain(*all_results)

    # Create a list of graph edges suitable for use by D3 - replace each record
    # in the data with one that carries an index into the tweeters list.
    edges = []
    for result in all_results:
        source = result["source"]
        target = result["target"]
        #ident = str(result["_id"])
        rec = { "source": talker_index[source],
                "target": talker_index[target]}
                #"id": ident }
        edges.append(rec)
        
    talkers = [{"tweet": n, "distance": distance[n]} for n in talkers]

    # Stuff the graph data into the response object, and return it.
    response["result"] = { "nodes": talkers,
                           "edges": edges }
    connection.close()
    # return the total size of the community, not the detail of the community
    return len(response['result']['nodes'])


#----------------------- suppress false hop count matches ------------
# If the 1 and 2 hop count values are both 1, then it often means we don't have any other
# information about this entity. (e.g. they were a target of a message).  Therefore, detect the
# case where one or the other is all ones in order to handle these cases specially


def hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
    a_is_not_alone = ga_hopcount[0]['1hop'] != 1 
    b_is_not_alone = gb_hopcount[0]['1hop'] != 1
    return a_is_not_alone and b_is_not_alone


#----------------------- initialization of mongo collection connections ------------

ga_dataset_name = 'twitter_nodelink'
ga_hop_collection_name = 'twitter_mentions_hop_analysis'

gb_dataset_name = 'instagram_nodelink'
gb_hop_collection_name = 'instagram_mentions_hop_analysis'

ground_truth_collection_name = 'ground_truth'
discovered_truth = 'discovered'

client = MongoClient("localhost")

# set up the databases
dba = client['july']
dbb = client['july']
challenge_db = client['july']

ga_coll = dba[ga_dataset_name]
gb_coll = dbb[gb_dataset_name]
ga_hop_collection = dba[ga_hop_collection_name]
gb_hop_collection = dbb[gb_hop_collection_name]
ground_truth_collection = dbb[ground_truth_collection_name]
discovered_collection = dbb[discovered_truth]
write_coll = challenge_db['topk_'+ga_dataset_name+'_'+gb_dataset_name]


# -------------- main processing loop: calculate separate quantities and write out for each pair
# -------------- of entities in the graphA and graphB collection that have proper names assigned

# how many candidate options do we want to be able to display as the 'top k' candidates?

k_value = 15

# this is a routine to find top-k matches for two string-based algorithms for each node in a graph. 
count = 0

print 'collections set, starting traversal'
sys.stdout.flush()

a_node_list = []
a_nodes_cursor = ga_coll.find({'type':'node'},timeout=False)
for anode in a_nodes_cursor:
    a_node_list.append(anode)
    
print 'found' ,len(a_node_list),'entries in ga'
sys.stdout.flush()

writecount = 0
#for a_node in a_node_list[75000:99999]:
for a_node in a_node_list[:9999]:
    if 'user_name' in a_node['data']:
        ga_name = a_node['data']['user_name']
        ga_id = a_node['data']['id']
        #print 'gA:',ga_name
        lev_heap = []
        substring_heap = []
        # go through each node in gB, calculate all the relative matches, and enter them in the heap
        for b_node in gb_coll.find({'type':'node'},timeout=False):
            if 'user_name' in b_node['data']:
                gb_name = b_node['data']['user_name']
                gb_id = b_node['data']['id']
                # calculate the matching value for this pair of nodes.  For each metrid, we insert a tuple into the heap,
                # indexed by the value of the similarity. 
                heapq.heappush(lev_heap,(lev_similarity(ga_name,gb_name),{'gb':gb_id,'name':gb_name} ))
                # insert the substring
                heapq.heappush(substring_heap,(substring_similarity(ga_name,gb_name), {'gb':gb_id,'name':gb_name}))
        # we have made a complete pass through graphB, lets output a top-k record that contains the results for each algorithm
        lev_topk = heapq.nlargest(k_value,lev_heap)
        substring_topk = heapq.nlargest(k_value,substring_heap)
            #print lev_topk

        # resort the top-k entries to be around the candidates's names instead to pass to LineUp
        sortdict = {}
        for entry in lev_topk:
            # start a dictionary entry for each
            #print 'lev-entry:', entry
            if entry[1]['name'] not in sortdict.keys():
                sortdict[entry[1]['name']] = {}
            sortdict[entry[1]['name']]['lev'] = entry[0]
            # we may not need this entry if LineUp is tolerant of sparse datalines, but do it anyway
            sortdict[entry[1]['name']]['substring'] = 0.0
        for entry in substring_topk:
            # start a dictionary entry for each
            #print 'lev-entry:', entry
            if entry[1]['name'] not in sortdict.keys():
                sortdict[entry[1]['name']] = {}
            sortdict[entry[1]['name']]['substring'] = entry[0]
            # if there had been no lev, then add a zero:
            if 'lev' not in sortdict[entry[1]['name']]:
                sortdict[entry[1]['name']]['lev'] = 0
        #print sortdict
        # done entering all the top-k values for this vertex from ga. output the top-k records:    
        for entry in sortdict.keys():
            record = {}
            record['ga']  = ga_name
            record['entity'] = entry
            record['lev'] = sortdict[entry]['lev']
            record['substring'] = sortdict[entry]['substring']
            #print record

            # add the ground truth
            record['apriori'] = ground_truth_similarity(ga_name,entry)
            if record['apriori']>0:
                print 'declared truth: ',ga_name,entry
                sys.stdout.flush()
                discovered_collection.insert({'ga':ga_name,'gb':entry})

            # now add the 1,2,3 hop info.  We look up each entity's values and then create a 0 to 1 value
            # where 1 is no difference in size of the neighborhood

            ga_hopcount = ga_hop_collection.find({'entity':ga_name})
            #print 'hop a:',ga_name,ga_hopcount[0]
            gb_hopcount = gb_hop_collection.find({'entity':entry})
            #print 'hop b:',entry,gb_hopcount[0]
            if (ga_hopcount.count()>0) and (gb_hopcount.count()>0) and hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
                record['1hop'] = 1.0/(1.0+abs(ga_hopcount[0]['1hop']-float(gb_hopcount[0]['1hop'])))
                record['2hop'] = 1.0/(1.0+abs(ga_hopcount[0]['2hop']-float(gb_hopcount[0]['2hop'])))
                #record['3hop'] = 1.0/(1.0+abs(ga_hopcount[0]['3hop']-gb_hopcount[0]['3hop']))
            else:
                record['1hop'] = record['2hop']  = 0.0
            #print record
            write_coll.insert(record)
            writecount +=1
            if (writecount % 500) == 0:
                print writecount,'ga=',ga_id,'gb=',entry
        
    #print record
    count += 1
    #if count > 35:
    #    break
    
print 'finished! Processed ', count, 'record pairs'
client.close()
