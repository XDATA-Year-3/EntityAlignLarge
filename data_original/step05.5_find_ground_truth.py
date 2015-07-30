from pymongo import MongoClient
import heapq
import json
import pprint
count = 0

client = MongoClient("localhost")
db = client["july"]
inst_coll = db['instagram']
twit_coll = db['twitter']
write_coll = db['ground_truth']


pp = pprint.PrettyPrinter(indent=4)

with open('/Volumes/xdata_2tb/2015/july/fromDavid/aliases.json') as data_file: 
#with open('/Users/clisle/proj/xdata/july-EA/mentions.json') as data_file: 
    for line in data_file.xreadlines():
        # ignore the file header and comment lines
        if (line[0:6] != '[INFO]') and len(line)>5:
            #print line
            jsonobj = json.loads(line)
            #pp.pprint(jsonobj)
       

count = 0

for alias in jsonobj['twitter_aliases']:
    twit_id = jsonobj['twitter_aliases'][alias]['twitter_id']
    twit_name = jsonobj['twitter_aliases'][alias]['twitter_names']
    inst_id_list = jsonobj['twitter_aliases'][alias]['instagram_ids']
    for inst_id in inst_id_list:
        inst_record = inst_coll.find_one({'user_id':inst_id})
        try:
            inst_name = inst_record['user_name']
            truthRecord = {'twitter_name':twit_name,'instagram_name':inst_name}
            write_coll.insert(truthRecord)
        except Exception:
            pass
        #print truthRecord
        #count += 1
    #if count > 20:
    #    break