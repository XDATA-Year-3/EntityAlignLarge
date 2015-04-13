import bson
import bson.json_util
import pymongo
import json
from bson import ObjectId
from pymongo import Connection
import string
import tangelo

import networkx as nx
from networkx.readwrite import json_graph
import rpy2.robjects as robjects



# services wrapper around the Seeded Graph Matching algorithm developed by the Johns Hopkins XDATA team.  First several
# support routines are listed, then at the bottom, the main interfacd routine. 


def addNodesToGraph(g,count):
    current_node_count = len(g.nodes())
    for count in range(count):
        g.add_node(current_node_count+count)


# return common names and the matching ID pairs from a pair of graphs.  This uses the 'name' attribute on each
# node to find and return a set of nodes where the names matched.  This can be used to generate seeds for a 
# graph, where it is known that the corresponding entities are supposed to be paired. 

def returnCommonMatches(ga,gb):
    #first, build dictionaries off all the names
    gaNames = {}
    gbNames = {}
    matchingdict = {}
    # insert the names into dictionaries so we have a unique list, eliminate duplicates
    for name in nx.get_node_attributes(ga,'name').values():
        gaNames[name] = name
    for name in nx.get_node_attributes(gb,'name').values():
        gbNames[name] = name
    for name in gaNames.keys():
        if name in gbNames.keys():
            # find the nodeIDs for this name
            id_a = nameToNode(ga,name)
            id_b = nameToNode(gb,name)
            matchingdict[name] = [id_a,id_b]
    return matchingdict



# this shuffles the nodes so any nodes identified in the seed list are placed at the beginning of the list of
# nodes in the graph.  This is a necessary precondition for the SGM algorithm.  It assumes the first m of n 
# vertices in each of the graphs, correspond to the seeds.

def rearrangeGraphWithSeeds(ingraph,seedList):
    # this routine expects a graph with node IDs as character strings of integegers (e.g. '0', '1', etc.) 
    # which is the way networkX reads graphML files.  This routine recognizes a set of seed nodes
    # as seeds and swaps nodes so the seeds are always in the beginning of the graph.
    head = 0
    substitutions = {}
    # copy the seeds into the front of the graph
    for seednode in seedList:
        # if the seed node and head are equal, we don't have to swap anything
        if seednode != head:
            if head in ingraph.nodes():
                # if the node pointed to by seednode has already been moved by a previous seed, then 
                # make this substitution against the node in its new location. 
                if seednode in substitutions.keys():
                    destination = substitution[seednode]
                else:
                    destination = seednode
                # there is already a node where we want to put this seed. Swap the nodes
                mapping = {head : 'temp'}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                mapping = {destination: head}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                mapping = {'temp' : destination}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                substitutions[head] = destination
            else:
                # no node exists where we want to put the seed, just relabel the node
                mapping = {seednode: head}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)            
            head = head+ 1
    return ingraph


def findCorrespondingNodeInMatrix(mat,size, seedcount,node):
    # we are looking for which element of the nodes row is set
    found = False
    for colindex in range(size):
        if mat[(node-1)*size+colindex] == 1:
            found = True;
            return colindex
    if (found == False):
        print "error, couldn't find matching node for ",node
        


def run(graphAnodes,graphAedges,graphBnodes,graphBedges):

    # building graphA, graphB networkX structures from the separate node & link structures 
    # passed from javascript.  For the moment, we don't allow multiple links between edges or directed edges

  # first decode the argument from being passed through a URL
    graphAnodes_obj =  bson.json_util.loads(graphAnodes)
    graphAedges_obj =  bson.json_util.loads(graphAedges)
    graphBnodes_obj =  bson.json_util.loads(graphBnodes)
    graphBedges_obj =  bson.json_util.loads(graphBedges)

    # for some reason, edges are coming across pre-linked with nodes, lets just extract out

    print "reassembling graph A and B"

    # start with an empty graph instance
    ga = nx.Graph()
    # traverse through the nodes from the app and add them to the new graph instance
    for value in graphAnodes_obj.itervalues():
        print value
        ga.add_node(value['id'])
    # traverse through the edges
    for link in graphAedges_obj.itervalues():
        print link
        ga.add_edge(link['source'],link['target'])
    print "received graph A:"
    print ga.nodes()
    print ga.edges()

    # start with an empty graph instance
    gb = nx.Graph()
    # traverse through the nodes from the app and add them to the new graph instance
    for value in graphBnodes_obj.itervalues():
        print value
        gb.add_node(value['id'])
    # traverse through the edges
    for link in graphBedges_obj.itervalues():
        print link
        gb.add_edge(link['source'],link['target'])
    print "received graph B:"
    print gb.nodes()
    print gb.edges()


    # initialize igraph to get JHU SGM algorithm
    print robjects.r('library(igraph)')

    # check the nunber of nodes between the two graphs and add nodes to the smaller graph, so the have
    # the same number of nodes.  The initial version of SGM in igraph required the same cardinality between 
    # nodes sets.  This has since been relaxed, but this step is included in case. 

    ga_num_nodes = len(ga.nodes())
    gb_num_nodes = len(gb.nodes())
    ga_larger_count = ga_num_nodes - gb_num_nodes
    print ga_larger_count
    if ga_larger_count > 0:
        addNodesToGraph(gb,abs(ga_larger_count))
    else:
        addNodesToGraph(ga,abs(ga_larger_count))

    # now both should have the same cardinality
    print nx.info(ga)
    print nx.info(gb)

    num_nodes = len(ga.nodes())

    # get integer node labels
    gan = nx.convert_node_labels_to_integers(ga)
    gbn = nx.convert_node_labels_to_integers(gb)
    match2 = returnCommonMatches(gan,gbn)

    print len(match2.keys()), " nodes match:"
    print match2

    # temporarily write out as a GraphML format (which preserved node order, then read back in on the igraph
    # side.  This is probably unnecessary, but it was done in the initial prototypes, so preserved here. )
    #nx.write_graphml(gan_seeds,"/tmp/gan_seeds.gml")
    #nx.write_graphml(gbn_seeds,"/tmp/gbn_seeds.gml")
    #robjects.r("gA <- read.graph('/tmp/gan_seeds.gml',format='graphML')")
    #robjects.r("gB <- read.graph('/tmp/gbn_seeds.gml',format='graphML')")

    # convert to an adjacency matrix for the SGM algorithm
    #robjects.r("matA <- as.matrix(get.adjacency(gA))")
    #robjects.r("matB <- as.matrix(get.adjacency(gB))")

    # initialize the start matrix.  This is set to uniform values initially, but I think this is 
    # somewhat sensitive to data values
    #number_of_nonseed_nodes = num_nodes - len(seeds)

    #print robjects.r('startMatrix = matrix( 1/(44-6), (44-6),(44-6) )')
    #print robjects.r('startMatrix = matrix( 1/'+number_of_nonseed_nodes+', ('+number_of_nonseed_nodes+')),('+number_of_nonseed_nodes+')')

    # Create an empty response object.
    response = {}

    # Pack the results into the response object, and return it.
    response['result'] = {}
    #response['result']['status'] = fixedNodes
    #response['result']['bijection'] = fixedEdges
    connection.close()

    # Return the response object.
    #tangelo.log(str(response))
    return json.dumps(response)
