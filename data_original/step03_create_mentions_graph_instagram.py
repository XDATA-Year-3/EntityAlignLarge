#!/usr/bin/env python

from pymongo import MongoClient
import re
import sys

# used for time conversion, lets put human readable time into the record sice Clique will directly display it. 
import arrow

unknowntargets = 0
unknownsources = 0

regexp = re.compile(".*@(\w+).*")

def find_mentions(collection_read, collection_write):
  global unknowntargets
  global unknownsources
  for result in collection_read.find({"msg": regexp}):
    #print "processing: ",result
    # had to add force to string around source and target expressions because of some all integer tweeter names
    source = str(result["user_name"]).lower()
    target = str(regexp.search(result["msg"]).group(1)).lower()
    if source == target:
      continue
    document = {}
    document["source"] = source
    document["target"] = target
    #document["date"] = arrow.get(result["msg_date"])
    document["date"] = result["msg_date"]

    # find the user IDs
    try:
      document['source_user_id'] = int(collection_read.find_one({'user_name':source})['user_id'])
    except Exception:
      print 'could not find user_id for source',source
      unknownsources += 1

    try:
      document['target_user_id'] = int(collection_read.find_one({'user_name':target})['user_id'])
    except Exception:
      #print 'could not find user_id for target',target
      unknowntargets += 1

    collection_write.save(document)

if __name__ == "__main__":
  try:
    if len(sys.argv) > 1:
      client = MongoClient(sys.argv[1])
    else:
      client = MongoClient()
  except Exception as e:
    print "Error connecting to MongoDB on " + sys.argv[1]
    sys.exit(1)

  db = client['july']
  collection_read = db['instagram']
  collection_write = db['instagram_mentions']
  num_tweets = collection_write.find().count()
  print "number of documents before: %d" % num_tweets

  find_mentions(collection_read, collection_write)

  print "done"
  num_tweets = collection_write.count()
  print "number of documents after: %d" % num_tweets
  print "unknown sources: ",unknownsources
  print "unknown targets:",unknowntargets
