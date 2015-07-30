from pymongo import MongoClient
import networkx as nx
from networkx.readwrite import json_graph
import sys

connection2 = MongoClient('localhost')
db = connection2['year3_challenge2_v6']
read_collection = db['twitter']
write_collection = db['twitter_fixed_indexes']

# now loop through the edges in this database to find a list of unique nodes that are referenced
records = read_collection.find({'type':'link'},timeout=False)
fixed = 0
nodes = 0
links = 0
for record in records:
	original = record
	if ('data' in record):
		if ('source' in record['data']):
			record['data']['source'] = int(record['data']['source'])
			record['data']['target'] = int(record['data']['target'])
			write_collection.insert(record)		
			fixed += 1
print 'fixed ',fixed
print 'nodes ',nodes
sys.stdout.flush()

