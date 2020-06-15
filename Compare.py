#Levent Batakci
#6/9/2020
#
#This program is concerned witht he comparison of merge trees
import networkx as nx
from lib.Tools import f_, get_leaves, list_append, listify_nodes

#MEMOIZATION VARIABLES
global D
D={}

global matching
matching={}

global branching
branching = [{},{}]

#The associated cost of matching a pair of vertices
#from two rooted representations of branchings
def match_cost(U,V, mu,su , mv,sv):
    #m represents the minima
    #s represents the saddle
    return max(abs(f_(U.nodes[mu])-f_(V.nodes[mv])), abs(f_(U.nodes[su])-f_(V.nodes[sv])))

#The associated cost of removing a vertex 
#from a rooted representation of a branching
def remove_cost(A, u,v):
    return abs(f_(A.nodes[u])-f_(A.nodes[v]))/2

#Gets all of the child subtrees of a given root branch
def get_child_subtrees(root, minima, T):
    last = minima
    p = T.nodes[minima]['p']
     
    #print("root: " + str(root) + " minima: " + str(minima))
    #print("Root and Minima contained in tree: " + str(root in list(T.nodes) and minima in list(T.nodes)))
    
    subtrees = []
    while(True):
        #print(p)
        neighbors = T[p]
        
        #Add all the subtrees with child saddle p
        for n in neighbors:
            #Check that n is a child and not an ancestor of minima
            if (n != last and f_(T.nodes[n]) < f_(T.nodes[p])):
                stree = sub_special(T, n)
                subtrees.append(stree)
                #print("subtree: " + str(list(stree.nodes)))
                #print("root: " + str(stree.graph['root']))
        
        #We've traced back to the root
        if(p == root):
            return subtrees
        
        last = p #Update the last variable
        p = T.nodes[p]['p'] #Move to the next ancestor

#Gets a list including n and all of its descendants, recursively
def descendants(G, n):
    neighbors = G[n]
    
    d = [n]
    for nei in neighbors:
        if(f_(G.nodes[nei]) < f_(G.nodes[n])):
            #Check if already computed
            if(str(nei) not in D):
                D[str(nei)] = descendants(G, nei)
            list_append(d, D[str(nei)])
    
    return d

#Returns the special subgraph identified by the almost-root
#The almost-root is first node in the graph. 
def sub_special(G, n):
    nodes = []
    nodes.append(G.nodes[n]['p'])
    list_append(nodes, descendants(G, n))

    #Induce the subgraph and return it
    g = nx.Graph.subgraph(G, nodes)
    g = g.copy()
    g.graph['root'] = G.nodes[n]['p']
    g.graph['ID'] = n
    return g

#Creates a bipartite graph to represent the connections between two
#sets of child subtrees
def create_bip(list_A, list_B):
    bip = nx.Graph()
    
    #Add all the nodes to the two bipartitions
    #Reliant on the fact that the subtrees were generated by IsEpsSimilar
    for a in list_A:
        bip.add_node(a)       
    for b in list_B:
        bip.add_node(b)
        
    return bip

#returns a list of ID nodenames
def node_list(subtrees):
    x = []
    for s in subtrees:
        x.append(s.graph['ID'])

    return x

#Computes whether two subtrees a and b are matchable. Calls IsEpsSimilar
#    in the case that the computation hasn't yet been computed.
def compute_matchability(a, b, e, memo):

    #These indices always pull the ID and roots because of how the subtrees are
    #constructed in a previous method. Generally, this will NOT work on subtrees not
    #computed through IsEpsSimilar!!
    root_a = a.graph['root'] 
    id_a = a.graph['ID']
    root_b= b.graph['root']
    id_b = b.graph['ID']
    
    #Check if subtree 'a' has an entry corresponding to it in memo
    #Note: because of the input order, we only ever need entries in the
    #      in the order (a,b)
    if(id_a not in memo or id_b not in memo[id_a]): #Result not computed yet
        if(id_a not in memo):
            memo[id_a] = {}
            
        memo[id_a][id_b] = IsEpsSimilar(a, b, e, [root_a, root_b], memo)
    
    #Return the result (True or False)
    return memo[id_a][id_b]

#Compute all the removal costs at and below a root
#Return the resulting cost dictionary
def compute_costs(A, root, e, costs={}):
        
    if(root in costs):
        return costs
    
    #Base removal cost
    #print("Saddle and Minima in tree: " + str(root in A and A.nodes[root]['p'] in A))
    c = remove_cost(A, root, A.nodes[root]['p'])
    
    #Account for the necessary removal of descendants
    #Use memoization to speed things up
    f = f_(A.nodes[root])
    neighbors = A[root]
    for nei in neighbors:
        #If nei is a child but its cost hasn't been computed...
        if(f_(A.nodes[nei]) < f):
            if(nei not in costs):
                costs[nei] = compute_costs(A, nei, e, costs)[nei]
            c += costs[nei]
    
    costs[root] = c
    return costs

#Add all the ghosts to the bipartite graph
def who_you_gonna_call(subtrees_A, subtrees_B, costs_A, costs_B, bip, e):
    for a in subtrees_A:
        id_a = a.graph['ID']
        #Could be removed..
        if(costs_A[id_a] <= e):
            bip.add_node("GHOST " + str(id_a))
            bip.add_edge(id_a, "GHOST " + str(id_a))
    for b in subtrees_B:
        id_b = b.graph['ID']
        #Could be removed..
        if(costs_B[id_b] <= e):
            bip.add_node("GHOST " + str(id_b))
            bip.add_edge(id_b, "GHOST " + str(id_b))

def has_ghost(A, a):
    nodes = list(A.nodes)
    
    return ("GHOST " + str(a)) in nodes

def is_ghost(a):
    return (isinstance(a, str) and len(a) >= 5 and a[0:5] == "GHOST")

#Check if good match
#yeah, this comment is bad
def good_match(A):
    nodes = list(A.nodes)
    
    global matching    
    for a in nodes:
        if not is_ghost(a) and len(A[a]) == 0:
            return False
        elif not is_ghost(a):
            if(is_ghost(list(A[a])[0])):
                update_matching(list(A[a])[0], a)
        
    return True

def update_matching(a, b):
    global matching
    if(is_ghost(a)):
        matching[b] = "DELETED"
    else:
        matching[a] = b

#Returns a subgraph induced by removign certain nodes
def subgraph_without(G, exclude):
    nodes = list(G.nodes)
    
    for ex in exclude:
        nodes.remove(ex)
        
    return G.subgraph(nodes)
    
#determines whether a perfect matching exists in the context of ghost vertices
def has_perfect_matching(bip, part_A, part_B, results=None):
    if(results==None):
        results={}
    
    #Parts A and B are lists of non-ghost nodenames
    #ID is used to identify a result
    ID = str(part_A)+"SPLIT"+str(part_B)

    #Check if already computed
    if(ID in results):
        return results[ID]
    
    #BASE CASE, ONE SET IS EMPTY
    #In this case, check that the non-empty set only contains ghosts
    #and deletable nodes
    if(len(part_A) == 0):
        results[ID] = good_match(bip)
        return results[ID]
    if(len(part_B) == 0):
        results[ID] = good_match(bip)
        return results[ID]
    
    #NONEMPTY SET, resort to recursion
    #iterate over all possible matches for the first vert in part_A
    #and recursively determine if there's a possible perfect matching
    a = part_A[0]
    
    #Iterate over the possibilities
    neighbors = list(bip[a])
    for nei in neighbors:
        
        #Delete the chosen nodes from the list and graph.
        b = subgraph_without(bip, [a, nei])
        
        new_A = part_A.copy()
        new_A.remove(a)
        
        new_B = part_B.copy()
        if(nei in new_B):
            new_B.remove(nei)
            
        
        #Recursively solve the subproblem
        if(has_perfect_matching(b, new_A, new_B, results)):
            results[ID] = True
            #update_matching(a,nei)
            return results[ID]
        
    results[ID] = False
    return results[ID]
    
def find_root(T):
     nodes = listify_nodes(T)
     
     max_ = f_(nodes[0])
     max_node = nodes[0]
     for n in nodes:
         if(f_(n) > max_):
             max_ = f_(n)
             max_node = n
             
     return max_node['name']
    
def relabel(G, tag):
    nodes = list(G.nodes)
    
    new_names = {}    
    
    for n in nodes:
        new_names[n] = tag + str(n)
        G.nodes[n]['p'] = tag + str(G.nodes[n]['p'])
    
    nx.relabel.relabel_nodes(G, new_names, copy=False)
        
def update_branching(B, saddle, minima):
    if(saddle not in B):
        B[saddle] = []
    
    B[saddle].append(minima)
    
#S and M are two trees to compare
#e is the cost maximum
#roots is an array containing the roots of A and B
#The function returns whether or not the two merge trees are matchable within e
def IsEpsSimilar(A, B, e, roots=None, memo=None):
    if(memo==None):
        memo = {}
    if(roots==None):
        roots = [find_root(A), find_root(B)]
    
    #Find the root - the highest vertex - of each tree
    root_A = roots[0]
    root_B = roots[1]

    #Compute all costs for later ghost-vertex marking
    costs_A = compute_costs(A, root_A, e)
    costs_B = compute_costs(B, root_B, e)
    
    #Get the minima of the two treees.
    #These are crucial to the construction of branch decompositions
    minima_A = get_leaves(A)
    minima_B = get_leaves(B)
    
    #Next, Iterate over all root-branch posibilities for each graph.
    #At each step, we will check if pairing the two root-branches is feasible.
    #If it is feasible, we will iterate over all child subtree pairings, and
    #    we will recursively check for epsilon similarity. We will construct a
    #    bipartite graph with vertices representing the child subtrees. In the
    #    case that a pairing is matchable, an edge will be drawn between the
    #    corresponding vertices in the bipartite representation
    global branching
    for mA in minima_A:
        for mB in minima_B:
            
            #At this point, a root-branch pairing will be specified.
            #Check if the initial cost of matching this pairing is prohibitive.
            #If it isn't check if the rest of the graph is matchable by considering
            #   all of the child subtrees.
            if(match_cost(A,B, mA, root_A, mB, root_B) <= e):
                update_matching(mA, mB)
                update_matching(root_A, root_B)
                
                update_branching(branching[0], root_A, mA)
                update_branching(branching[1], root_B, mB)
                
                #Get a list of all the child subtrees of each root-branch
                subtrees_A = get_child_subtrees(root_A, mA, A)
                subtrees_B = get_child_subtrees(root_B, mB, B)
                
                #Create a bipartite graph representating the matchability of
                #    subtree pairings between the two lists above. Also, save
                #    all of the nodes in lists.
                list_A = node_list(subtrees_A)
                list_B = node_list(subtrees_B)
                bip = create_bip(list_A, list_B)
                
                #Iterate over all child-subtree pairing and compute matchability.
                #Use memoization to use the results of previous computations.
                #Also, fill in the bipartite edges where applicable
                for a in subtrees_A:
                    for b in subtrees_B:
                        if(compute_matchability(a, b, e, memo)):
                            bip.add_edge(a.graph['ID'], b.graph['ID'])
                
                #At this point, we should have a bipartite graph that encodes the
                #matchability of each child-subtree pairing at the current level.
                #
                #However, we need to account for the posibility of deletion!
                #To do this, we will iterate over all the current vertices in the 
                #bip. graph and mark ghosts by checking their removal cost.
                who_you_gonna_call(subtrees_A, subtrees_B, costs_A, costs_B, bip, e)
                
                #Make sure the node lists only contain the necessary nodes
                for a in list_A:
                    if(has_ghost(bip, a)):
                        list_A.remove(a)
                for b in list_B:
                    if(has_ghost(bip, b)):
                        list_B.remove(b)
                
                #NOW, everything should be set up properly to check for a perfect
                #     matching.
                if(has_perfect_matching(bip, list_A, list_B)):
                    return True
    
    if(root_A in branching[0]):            
        branching[0].pop(root_A)
    if(root_B in branching[1]):            
        branching[1].pop(root_B)
    #No matching was found!
    return False

###### I (Candace) added the function below but I'm not sure if it works yet 
###### because idek how isEpsSimilar works (which I realize is probably because
###### it's not done yet) so for now when I try to test this I just feed it the
###### same tree twice which is basically just for the purpose of testing the 
###### binary search functionality
##### I am also very open to renaming this function I just didn't know what to call it
# Takes two merge trees and finds the distance between them
# within a certain radius of accuracy
def morozov_distance(T1, T2, radius = 0.05):
    
    T1 = T1.copy()
    T2 = T2.copy()
    
    relabel(T1, "*")
    relabel(T2, "~")
    
    # Find the larger amplitude between the two trees as our starting epsilon
    vals1 = [i[1]["value"]for i in list(T1.nodes.data())] # I feel like there is definitely an easier way to find max/mins than making lists
    amp1 = abs(max(vals1)-min(vals1)) # amplitude for T1
    vals2 = [j[1]["value"]for j in list(T2.nodes.data())]
    amp2 = abs(max(vals2)-min(vals2)) # amplitude for T2

    maximum = max(amp1,amp2) # Find the biggest of the two amplitudes
    print("max: " + str(maximum))
    
    roots = [find_root(T1), find_root(T2)]
    
    # Placeholder until i understand how IsEpsSimilar works
    #similar = True
    epsilon = maximum
    similar = IsEpsSimilar(T1,T2, epsilon, roots)
    delta = epsilon
    
    its = 0
    # Continue the binary search until we get within our desired margin of error for accuracy
    while delta >= radius:
        global matching
        matching.clear()
        
        its+=1
        delta=delta/2
    # Decrease epsilon by half of the size between current epsilon and the lower end of the interval we're convergin on
        if similar == True:
            epsilon = epsilon - delta
            similar = IsEpsSimilar(T1,T2, epsilon, roots)
        else:
        # Increase epsilon by half of the size between current epsilon and the upper end of the interval we're convergin on
            epsilon = epsilon+delta
            similar = IsEpsSimilar(T1,T2, epsilon, roots)
        # Debug statement, will remove later
        #print(epsilon)
        
    # Pretty print statement for debugging, will remove later
    print("Morozov Distance:", epsilon, "\nMargin of Error:",radius, "\nIterations:",its)
    return epsilon
