import elasticsearch
import json
import pymongo
import urllib


def run(host, database, graphname):
    # Create an empty response object.
    response = {}

    if host == 'elasticsearch':
        collection = urllib.unquote(graphname)
        es = elasticsearch.Elasticsearch(collection, timeout=300)
        res = es.search(body=json.dumps({
            '_source': {'include': [
                'PersonGUID', 'Identity.Name.FullName',
                'Identity.Email.OriginalEmail',
            ]},
            'size': 25000,  # use a number for debug
            'query': {'function_score': {'filter': {'bool': {'must': [
                {'exists': {'field': 'PersonGUID'}}
            ]}}}},
            'sort': {'PersonGUID': 'asc'},
        }))
        namelist = []
        for hit in res['hits']['hits']:
            record = hit['_source']
            name = [record['PersonGUID']]
            ident = record['Identity'][0]
            for fullname in ident['Name']:
                name.append(fullname.get('FullName'))
            if 'Email' in ident:
                for email in ident['Email']:
                    name.append(email.get('OriginalEmail'))
            namelist.append(' - '.join([
                subname for subname in name if subname]))
        response['result'] = {'nodes': namelist}
    else:
        # this method traverses the documents in the selected graph collection
        # and builds a JSON object that represents a list of all nodes in the
        # graph

        client = pymongo.MongoClient(host, 27017)
        db = client[database]
        # get a list of all collections (excluding system collections)
        namehint_coll_name = 'topk_' + graphname + (
            "_instagram" if graphname == "twitter" else "_twitter")
        print 'looking in collection', namehint_coll_name
        collection = db[namehint_coll_name]

        namelist = [x["ga"] for x in collection.find({"selfreport": 1})]

        # loop through the records in the network and take the appropriate
        # action for each type. Suppress the ID field because it doesn't
        # serialize in JSON.  If the node is named, return the name,  else
        # return ID if there is an ID only

        # nodes = collection.find({},{'_id':0}).limit(99999)
        # namelist = []
        # for x in nodes:
        #    #if 'name' in x:
        #        #namelist.append(x['name'])
        #    #elif 'name' in x['data']:
        #        #namelist.append(x['data']['name'])
        #    #elif 'username' in x['data']:
        #        #namelist.append(x['data']['username'])

        # Pack the results into the response object, and return it.
        response['result'] = {}
        response['result']['nodes'] = namelist
        client.close()

    # Return the response object.
    # tangelo.log(str(response))
    return json.dumps(response)
