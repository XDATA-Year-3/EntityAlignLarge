import bson.json_util
from bson.objectid import ObjectId
import json
from pymongo import MongoClient


CachedNodes = {'maxentries': 10000}   # Set to None to disable
CheckedIndices = False


def freeze(rec):
    return (str(rec["_id"]), rec["data"]["id"], bson.json_util.dumps(rec))


def process(frozen):
    rec = json.loads(frozen[2])

    processed = {"key": rec["_id"]["$oid"]}
    processed.update(rec["data"])

    return processed


def ensureLinkIndices(coll):
    """
    Make sure Mongo has the appropriate indices for fast link retreival.

    :param coll: the collection that contains links.
    """
    global CheckedIndices
    if not CheckedIndices:
        coll.ensure_index([('data.id', 1)])
        coll.ensure_index([('data.source', 1)])
        coll.ensure_index([('data.target', 1)])
        coll.ensure_index([('type', 1)])
        CheckedIndices = True


def run(host=None, db=None, coll=None, center=None, radius=None,
        deleted=json.dumps(False), withLinkId=False):
    # Connect to the Mongo collection
    client = MongoClient(host)
    db = client[db]
    graph = db[coll]
    ensureLinkIndices(graph)
    if CachedNodes:
        CachedNodes.setdefault(coll, {})
        if len(CachedNodes[coll]) > CachedNodes['maxentries']:
            CachedNodes[coll] = {}

    # Prepare the arguments.
    radius = int(radius)
    deleted = json.loads(deleted)

    frontier = set()
    neighbor_nodes = set()
    neighbor_links = []

    # Find the center node in the database.
    center_node = graph.find_one({"_id": ObjectId(center)})

    if (center_node is not None and deleted or
            not center_node["data"].get("deleted")):
        frozen = freeze(center_node)

        neighbor_nodes.add(frozen)
        frontier.add(frozen)

    for i in range(radius):
        new_frontier = set()

        # Compute the next frontier from the current frontier.
        for key, id, _ in frontier:
            # Find all incoming and outgoing links from all nodes in the
            # frontier.
            query = {"$and": [{"type": "link"},
                              {"$or": [{"data.source": id},
                                       {"data.source": str(int(id))},
                                       {"data.target": id},
                                       {"data.target": str(int(id))}]}]}
            links = graph.find(query)

            # Collect the neighbors of the node, and add them to the new
            # frontier if appropriate.
            for link in links:
                source = link["data"]["source"] in [id, str(int(id))]
                neighbor_id = int(source and link["data"]["target"] or
                                  link["data"]["source"])
                if CachedNodes is None or neighbor_id not in CachedNodes[coll]:
                    query_clauses = [{"type": "node"},
                                     {"data.id": neighbor_id}]
                    if not deleted:
                        query_clauses.append({
                            "$or": [{"data.deleted": {"$exists": False}},
                                    {"data.deleted": False}]})
                    neighbor = graph.find_one({"$and": query_clauses})
                    if CachedNodes is not None:
                        CachedNodes[coll][neighbor_id] = neighbor
                else:
                    neighbor = CachedNodes[coll][neighbor_id]
                if neighbor is not None:
                    frozen = freeze(neighbor)
                    if frozen not in neighbor_nodes:
                        new_frontier.add(frozen)
                        neighbor_nodes.add(frozen)

                        if source:
                            neighbor_link = {"source": key,
                                             "target": str(neighbor["_id"])}
                        else:
                            neighbor_link = {"source": str(neighbor["_id"]),
                                             "target": key}
                        if withLinkId:
                            neighbor_link['_id'] = link['_id']
                        neighbor_links.append(neighbor_link)

            frontier = new_frontier

    # processed = map(process, neighbor_nodes)
    processed = map(lambda x: json.loads(x[2]), neighbor_nodes)

    return {"nodes": processed,
            "links": neighbor_links}
