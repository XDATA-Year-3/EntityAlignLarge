from pymongo import MongoClient
import networkx as nx
from networkx.readwrite import json_graph
import sys

connection2 = MongoClient('localhost')
db = connection2['july']
node_collection = db['instagram']
link_collection = db['instagram_mentions']
combined_collection = db['instagram_nodelink']

# now loop through the edges in this database to find a list of unique nodes that are referenced
records = link_collection.find(timeout=False)
namelist = []
for record in records:
    namelist.append(record['source'])
    namelist.append(record['target'])
print 'nodelist length = ',len(namelist)
# remove duplicates
cleanlist = set(namelist)
print 'uniquelist length = ',len(cleanlist)
sys.stdout.flush()

# create an empty graph to fill from the collections.  We need to use networkx because we want to use the
# networkx algorithm to generate 

graph = nx.Graph()

# this routine loops through the edges twice.  It first loads all needed nodes, then it adds edges between the nodes
count = 0
for vertexname in cleanlist:
    #this was the mistake before where we didn't always add the nodes, so NetworkX had to add them...
    graph.add_node(vertexname)

    # look up the full record of this entity
    source_node = node_collection.find({'user_name':vertexname})
    
    # now add the node name and/or any other attributes the nodes have 
    if source_node.count() >0:
        record = {}
        for attrib in source_node[0]:
            if (attrib != '_id'):
                graph.node[vertexname][attrib] = source_node[0][attrib]
    else:
        graph.node[vertexname]['user_name'] = vertexname
    graph.node[vertexname]['name'] = vertexname

# go through the links again, this time adding them to the graph now that all the nodes are in
count = 0
for link in link_collection.find():
    source_name = link['source']
    target_name = link['target']
    graph.add_edge(source_name,target_name)
    
print nx.info(graph)
print nx.graph_clique_number(graph)
print nx.number_connected_components(graph)
sys.stdout.flush()

# output the network metadata
import arrow
now = arrow.utcnow().timestamp
starttime = arrow.get('2014-01-01 00:00:00')
endtime = arrow.get('2014-12-31 11:59:59')
#print now

metadata_record_list = [{'datatype':'TwitterMentions'},
                        {'creationdate': now}, 
                        {'revision': 0.2}, 
                        {'sourcetype':'twitter_2014_gnip'},
                        {'description':'mentions'},
                        {'centralentityname':'unknown'}, 
                        {'starttime': starttime.timestamp},
                        {'endtime': endtime.timestamp}]

for entry in metadata_record_list:
    record = {}
    record['type'] ='metadata'
    record['data'] = entry
    #print record
    combined_collection.insert(record)

print "Convert to integer labels"
sys.stdout.flush()
graph_integers = nx.convert_node_labels_to_integers(graph)
graph_integers_as_json = json_graph.node_link_data(graph_integers)
print "conversion complete"
sys.stdout.flush()

record = {'type': 'graph','data': graph_integers_as_json['graph']}
combined_collection.insert(record)
record = {'type': 'multigraph','data': graph_integers_as_json['multigraph']}
combined_collection.insert(record)

count = 0
for node in graph_integers_as_json['nodes']:
    record = {'type':'node', 'data': node}
    #print record
    combined_collection.insert(record)

    
count = 0
for link in graph_integers_as_json['links']:
    record = {'type':'link', 'data': link}
    #print record
    combined_collection.insert(record)
    
connection2.close()