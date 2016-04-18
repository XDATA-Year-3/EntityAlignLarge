import bson.json_util

import neighborhood


def run(host=None, db=None, coll=None, node=None, outgoing='true',
        incoming='true', undirected='true', offset=0, limit=0):
    fetch = neighborhood.run(host, db, coll, node, 1, withLinkId=True)

    AlwaysUndirected = False

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
    return bson.json_util.dumps(links)
