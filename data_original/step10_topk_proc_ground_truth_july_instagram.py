from pymongo import MongoClient
import heapq
import sys
import json



#----------------------- initialization of mongo collection connections ------------

ga_dataset_name = 'ground_truth2'

gb_dataset_name = 'twitter_nodelink'

ground_truth_collection_name = 'ground_truth2'
discovered_truth = 'discovered'

client = MongoClient("localhost")

# set up the databases
dba = client['july']
dbb = client['july']
challenge_db = client['july']

ga_coll = dba[ga_dataset_name]
gb_coll = dbb[gb_dataset_name]
ground_truth_collection = dbb[ground_truth_collection_name]
discovered_collection = dbb[discovered_truth]
write_coll = challenge_db['topk_matches2_'+ga_dataset_name+'_'+gb_dataset_name]

#------ open the mentions collections ----------------
# this data is from David Manthey of Kitware.  It is a dictionary of dictionaries
# that encodes the edge target and edge count for all mentions in the database

with open('/Volumes/xdata_2tb/2015/july/fromDavid/twittermentions.json') as data_file: 
    for line in data_file.xreadlines():
        # ignore the file header and comment lines
        if (line[0:6] != '[INFO]') and len(line)>5:
            tw_mentions = json.loads(line)
data_file.close()

with open('/Volumes/xdata_2tb/2015/july/fromDavid/instagrammentions.json') as data_file:  
    for line in data_file.xreadlines():
        # ignore the file header and comment lines
        if (line[0:6] != '[INFO]') and len(line)>5:
            inst_mentions = json.loads(line)
data_file.close()

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
def ground_truth_similarity(s2, s1):
    gt_match = ground_truth_collection.find({'$and':[{'twitter_name':s1},{'instagram_name':s2}]})
    return gt_match.count()


#--------------- neighborhood calculation---------------------------

# network is 'twitter' or 'instagram'.  The handle is a name from the dataset. 
def calculateOneHopNetworkSizeAroundHandle(network, handle):
    try:
        if network == 'twitter':
            return  len(tw_mentions[handle].keys())
        else:
            return len(inst_mentions[handle].keys())
    except Exception:
        #print 'onehop calculation exception:',network,handle
        return 1

#----------------------- suppress false hop count matches ------------
# If the 1 and 2 hop count values are both 1, then it often means we don't have any other
# information about this entity. (e.g. they were a target of a message).  Therefore, detect the
# case where one or the other is all ones in order to handle these cases specially

def hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
    a_is_not_alone = ga_hopcount != 1 
    b_is_not_alone = gb_hopcount != 1
    return a_is_not_alone or b_is_not_alone


#--------- local network activity metric ----------------------
#--------------------------------------------------------------

# **** this isn't included yet 

# since the edge count is already compiled in the mentions dictionary hierarchy, just run a sum across
# the entries in the 1-hop mentions network to see how many "mentions" we sent to the local network. 

def messageActivityOfHandle(network, handle):
    if network == 'twitter':
        return  len(tw_mentions[handle].keys())
    else:
        return len(inst_mentions[handle].keys())

# now we can create a metric of normalized activity to the local neighborhood by dividing the message
# activity by the size of the network the activity went into

def normalizedLocalNeighborhoodActivity(network,handle):
    if network == 'twitter':
        return  messageActivityOfHandle/len(tw_mentions[handle].keys())
    else:
        return len(inst_mentions[handle].keys())   



# -------------- main processing loop: calculate separate quantities and write out for each pair
# -------------- of entities in the graphA and graphB collection that have proper names assigned

# how many candidate options do we want to be able to display as the 'top k' candidates?

k_value = 15

# this is a routine to find top-k matches for two string-based algorithms for each node in a graph. 
count = 0

print 'collections set, starting traversal'
sys.stdout.flush()

# -- graphA node list: composed of instagram collection returns plus ground truth added in

a_node_list = []
b_patch_list = []
a_nodes_cursor = ga_coll.find({},timeout=False)
for anode in a_nodes_cursor:
    a_node_list.append(anode['instagram_name'])
    b_patch_list.append(anode['twitter_name'])
a_node_set = set(a_node_list)
a_node_unique = list(a_node_set)   

print 'found' ,len(a_node_list),'entries in ga', len(a_node_unique), 'unique values'
sys.stdout.flush()

# -- graphB list: composed of instagram collection returns plus ground truth added in

b_patch_set = set(b_patch_list)
b_patch_unique = list(b_patch_set)

b_node_list = []
b_nodes_cursor = gb_coll.find({'type':'node'},limit=50000,timeout=False)
for bnode in b_nodes_cursor:
    b_node_list.append(bnode['data']['user_name'])
print 'found' ,len(b_node_list),'entries in gb' 
# patch the b_node_list:
for patch in b_patch_unique:
    b_node_list.append(patch)

b_node_set = set(b_node_list)
b_node_unique = list(b_node_set)  
       
print 'found' ,len(b_node_list),'entries in gb', len(b_node_unique), 'unique b patch values'
sys.stdout.flush()


writecount = 0
#for a_node in a_node_list[75000:99999]:
for a_node in a_node_unique[:9999]:
    #if 'twitter_name' in a_node:
    if True:
        ga_name = a_node
        ga_id = a_node
        #print 'gA:',ga_name
        lev_heap = []
        substring_heap = []
        # go through each node in gB, calculate all the relative matches, and enter them in the heap
        # *** KLUDGE limit the number of gB entries we test against to speed up processing
        for b_node in b_node_unique:
            gb_name = b_node
            gb_id = b_node
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

            ga_hopcount = calculateOneHopNetworkSizeAroundHandle('twitter',ga_name)
            #print 'hop a:',ga_name,ga_hopcount
            gb_hopcount = calculateOneHopNetworkSizeAroundHandle('instagram',entry)
            #print 'hop b:',entry,gb_hopcount
            if hopCountsShowConnectivity(ga_hopcount,gb_hopcount):
                record['1hop'] = 1.0/(1.0+abs(ga_hopcount-float(gb_hopcount)))
                record['2hop'] = record['1hop']
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
