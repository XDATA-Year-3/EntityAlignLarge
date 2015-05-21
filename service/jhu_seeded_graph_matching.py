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
        # generally we want to move from the head, but there is a special case that will override
        # this, so a variable is needed
        source = head
        # if the seed node and head are equal, we don't have to swap anything
        if seednode != head:
            if head in ingraph.nodes():
                # if the node pointed to by seednode has already been moved by a previous seed, then 
                # make this substitution against the node in its new location. 
                if seednode in substitutions.keys():
                    source = substitutions[seednode]
                    destination = head
                else:
                    destination = seednode
                # there is already a node where we want to put this seed. Swap the nodes
                mapping = {source : 'temp'}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                mapping = {destination: source}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                mapping = {'temp' : destination}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
                substitutions[source] = destination
            else:
                # no node exists where we want to put the seed, just relabel the node
                mapping = {seednode: source}
                ingraph = nx.relabel_nodes(ingraph,mapping,copy=False)
        # this moves even on the case where the seed matches the head            
        head = head+ 1
    return substitutions


def findCorrespondingNodeInMatrix(mat,size, seedcount,node):
    # we are looking for which element of the nodes row is set
    found = False
    for colindex in range(size):
        offset = (node-1)*size+colindex
        if mat[offset] == 1:
            found = True;
            return colindex
    if (found == False):
        print "error, couldn't find matching node for ",node
        
# was having trouble doing the linear indexing into the result array above, so use R to evaluate
# the sparse matrix        
def findCorrespondingNodeInSparseMatrix(mat,size, seedcount,node):
    # we are looking for which element of the nodes row is set
    found = False
    for colindex in range(size-seedcount-1):
        # make a 2D query because not sure how to index python object successfully
        content = 'P$D['+str(node+1)+','+str(colindex+1)+']'
        if robjects.r(content)[0]  > 0:
            found = True;
            return colindex
    if (found == False):
        #print "error, couldn't find matching node for ",node 
        return -1       

def findCorrelatedNode(size, seedcount,node):
    # we are looking for which element of the nodes row is set
    found = False
    corr = robjects.r('P$corr')
    # make a 1D query because not sure how to index python object successfully
    matching = corr[node+(size)]
    return matching-1


def run(graphAnodes,graphAedges,graphBnodes,graphBedges,seeds):

    # building graphA, graphB networkX structures from the separate node & link structures 
    # passed from javascript.  For the moment, we don't allow multiple links between edges or directed edges

  # first decode the argument from being passed through a URL
    graphAnodes_obj =  bson.json_util.loads(graphAnodes)
    graphAedges_obj =  bson.json_util.loads(graphAedges)
    graphBnodes_obj =  bson.json_util.loads(graphBnodes)
    graphBedges_obj =  bson.json_util.loads(graphBedges)
    seed_obj = bson.json_util.loads(seeds)

    # for some reason, edges are coming across pre-linked with nodes, lets just extract out


    print "reassembling graph A and B"

    # start with an empty graph instance
    ga = nx.Graph()
    # traverse through the nodes from the app and add them to the new graph instance
    for value in graphAnodes_obj.itervalues():
        print value
        ga.add_node(value['id'])
        #  add node attributes, like name, etc. to new node
        for attrib in value['data'][1]:
            #print 'found attrib:', attrib
            ga.node[value['id']][attrib] = value['data'][1][attrib]
    # traverse through the edges
    for link in graphAedges_obj.itervalues():
        #print link
        ga.add_edge(link['source'],link['target'])
    print "received graph A:"
    #print ga.nodes()
    #print ga.edges()

    # start with an empty graph instance
    gb = nx.Graph()
    # traverse through the nodes from the app and add them to the new graph instance
    for value in graphBnodes_obj.itervalues():
        print value
        gb.add_node(value['id'])
        #  add node attributes, like name, etc. to new node
        for attrib in value['data'][1]:
            #print 'found attrib:', attrib
            gb.node[value['id']][attrib] = value['data'][1][attrib]        
    # traverse through the edges
    for link in graphBedges_obj.itervalues():
        #print link
        gb.add_edge(link['source'],link['target'])
    print "received graph B:"
    #print gb.nodes()
    #print gb.edges()


    # initialize igraph to get JHU SGM algorithm
    robjects.r('library(igraph)')

    # check the nunber of nodes between the two graphs and add nodes to the smaller graph, so the have
    # the same number of nodes.  The initial version of SGM in igraph required the same cardinality between 
    # nodes sets.  This has since been relaxed, but this step is included in case. 

    ga_num_nodes = len(ga.nodes())
    gb_num_nodes = len(gb.nodes())
    ga_larger_count = ga_num_nodes - gb_num_nodes 
    print "graph a is larger by: ", ga_larger_count, ' nodes'
    if ga_larger_count > 0:
        addNodesToGraph(gb,abs(ga_larger_count))
    else:
        addNodesToGraph(ga,abs(ga_larger_count))

    # now both should have the same cardinality
    print nx.info(ga)
    print nx.info(gb)

    num_nodes = len(ga.nodes())
    num_seeds = len(seed_obj)

    # get integer node labels
    gan = nx.convert_node_labels_to_integers(ga)
    gbn = nx.convert_node_labels_to_integers(gb)

    # now make separate lists of seeds for each graph
    ga_seeds = []
    gb_seeds = []
    for seed in seed_obj:
        ga_seeds.append(seed['ga'])
        gb_seeds.append(seed['gb'])

    # re-arrange the graphs so the seeds are the first nodes in the graph and will be the lowest
    # indices in the adjacency matrix
    ga_substitutions = rearrangeGraphWithSeeds(gan,ga_seeds)
    gb_substitutions = rearrangeGraphWithSeeds(gbn,gb_seeds)

    print '----- substitutions ga -----'
    print ga_substitutions
    print '----- substitutions gb -----'
    print gb_substitutions

    # temporarily write out as a GraphML format (which preserved node order, then read back in on the igraph
    # side.  This is probably unnecessary, but it was done in the initial prototypes, so preserved here. )
    nx.write_graphml(gan,"/tmp/gan_seeds.gml")
    nx.write_graphml(gbn,"/tmp/gbn_seeds.gml")
    robjects.r("gA <- read.graph('/tmp/gan_seeds.gml',format='graphML')")
    robjects.r("gB <- read.graph('/tmp/gbn_seeds.gml',format='graphML')")

    # convert to an adjacency matrix for the SGM algorithm
    robjects.r("matA <- as.matrix(get.adjacency(gA))")
    robjects.r("matB <- as.matrix(get.adjacency(gB))")

    print robjects.r("gA")
    print robjects.r("gB")

    # initialize the start matrix.  This is set to uniform values initially, but I think this is 
    # somewhat sensitive to data values
    number_of_nonseed_nodes = num_nodes - num_seeds

    # start with a completely uniform start matrix 
    commandstring = 'startMatrix = matrix( 1/'+str(number_of_nonseed_nodes)+', '+str(number_of_nonseed_nodes)+','+str(number_of_nonseed_nodes)+')'
    print 'executing: ',commandstring
    robjects.r(commandstring)

    # run SGM on the two adjacency matrices
    commandstring = 'P <- match_vertices(matA,matB,m='+str(num_seeds)+',start=startMatrix,100)'
    print 'executing: ',commandstring
    robjects.r(commandstring)

    # pull graph match results back from igraph
    result =  robjects.r('P$corr')
    print 'result copied to python:'
    print result
    sizeP = robjects.r('nrow(P$P)')

    # copy results into a new 'matching list' that relates the network from the results discovered by SGM.   Since the graph was re-arranged 
    # for the seeds before going into SGM, we need to use the ID field from the node, so they match up with the networks in the calling application.

    print 'number of matches returned:',sizeP
    print sizeP[0]

    matches = []
    # copy over the match for the seeds
    for index in range(num_seeds):
        record = {'ga': gan.node[index]['id'], 'gb': gbn.node[index]['id'],}
        matches.append(record)

    # now copy over the links returned from SGM
    for index in range(0,number_of_nonseed_nodes-1):
        mappedNode = findCorrelatedNode(number_of_nonseed_nodes,num_seeds,index)
        if (mappedNode>0 and ('id' in gan.node[index+num_seeds]) and ('id' in gbn.node[mappedNode])):
            print index+num_seeds,mappedNode,gan.node[index+num_seeds],gbn.node[mappedNode]
            record = {'ga': gan.node[index+num_seeds]['id'], 'gb': gbn.node[mappedNode]['id']}
            matches.append(record)

    print 'matches:',matches

    # Create an empty response object, then add the output data
    response = {}
    response['result'] = {}
    response['result']['matches'] = matches
  
    # Return the response object.
    return json.dumps(response)
