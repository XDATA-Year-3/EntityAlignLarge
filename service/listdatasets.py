import bson
import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import tangelo



def run(host,database):
    # Create an empty response object.
    response = {}
    collectionNames = []

   # look through the collections in the ivaan database and return the name of all collections
   # that match the naming profile for tables.  This is matching to see if the collection name
   # begins with "table_"

    connection = Connection(host, 27017)
    db = connection[database]
    # get a list of all collections (excluding system collections)
    collection_list = db.collection_names(False)
    for coll in collection_list:
        # if it is a table, then add it to the response
        if (str(coll[:6]) =='table_'):
            print "found table:", coll
            collectionNames.append(coll)

    connection.close()

    # Pack the results into the response object, and return it.
    response['result'] = collectionNames

    # Return the response object.
    tangelo.log(str(response))
    return json.dumps(response)
