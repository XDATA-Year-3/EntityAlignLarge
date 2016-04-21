import bson.json_util

import neighborhood

CachedResults = {'maxentries': 1000}  # Set to None to disable

# Set to True to return all links as undirected links
AlwaysUndirected = False


def run(host=None, db=None, coll=None, node=None, outgoing='true',
        incoming='true', undirected='true', offset=0, limit=0):
    if CachedResults:
        CachedResults.setdefault(coll, {})
        if len(CachedResults[coll]) > CachedResults['maxentries']:
            CachedResults[coll] = {}
    if not CachedResults or node not in CachedResults[coll]:
        fetch = neighborhood.run(host, db, coll, node, 1, withLinkId=True)

        sources = {link['source']: link for link in fetch['links']
                   if link['source'] != node and link['target'] == node}
        targets = {link['target']: link for link in fetch['links']
                   if link['target'] != node and link['source'] == node}
        links = []
        for source in sources:
            link = sources[source]

            if source in targets or AlwaysUndirected:
                link['undirected'] = True
            else:
                link['incoming'] = True
            links.append(link)
        for target in targets:
            link = targets[target]
            if target not in sources:
                if AlwaysUndirected:
                    link['undirected'] = True
                else:
                    link['outgoing'] = True
                links.append(link)
        for link in links:
            link['type'] = 'link'
        if CachedResults:
            CachedResults[coll][node] = links
    else:
        links = CachedResults[coll][node][:]
    links = [link for link in links if
             (undirected == 'true' and link.get('undirected')) or
             (incoming == 'true' and link.get('incoming')) or
             (outgoing == 'true' and link.get('outgoing'))]
    if offset and offset != '0':
        links = links[int(offset):]
    if limit and limit != '0':
        links = links[:int(limit)]
    return bson.json_util.dumps(links)
