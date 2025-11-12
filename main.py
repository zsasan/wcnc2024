import networkx as nx
import random
import math
import time
from pyscipopt import Model
from pyscipopt import quicksum
import itertools


def cloud_graph(G1):

    # create an empty graph
    G = nx.Graph()

    G.add_node(1, cost_of_powering_on = 0)
    G.add_node(2, cost_of_powering_on = 0)
    G.add_node(3, cost_of_powering_on = 0)
    G.add_node(4, cost_of_powering_on = 3)
    G.add_node(5, cost_of_powering_on = 0)
    G.add_node(6, cost_of_powering_on = 0)
    G.add_node(7, cost_of_powering_on = 0)
    G.add_node(8, cost_of_powering_on = 0)
    G.add_node(9, cost_of_powering_on = 0)
    G.add_node(10, cost_of_powering_on = 0)
    G.add_node(11, cost_of_powering_on = 0)
    G.add_node(12, cost_of_powering_on = 0)

    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 10)
    G.add_edge(10, 4)
    G.add_edge(1, 5)
    G.add_edge(5, 6)
    G.add_edge(6, 11)
    G.add_edge(11, 12)
    G.add_edge(12, 4)
    G.add_edge(1, 7)
    G.add_edge(7, 8)
    G.add_edge(8, 9)
    G.add_edge(9, 4)

    for node in G.nodes():
        if node == 4:
            G.nodes[node]['capacity'] = G1.nodes[node]['capacity']
            G.nodes[node]['delay'] = G1.nodes[node]['delay']
            G.nodes[node]['cost'] =  G1.nodes[node]['cost']
            continue
        G.nodes[node]['capacity'] = 0
        G.nodes[node]['delay'] = 0
        G.nodes[node]['cost'] = 0
        #print(G.nodes[node]['cost'])
    for edge in G.edges():
        G.edges[edge]['capacity'] = G1.edges[edge]['capacity']
        G.edges[edge]['delay'] = G1.edges[edge]['delay']
        G.edges[edge]['cost'] = G1.edges[edge]['cost']
    
    return G

def static_graph():
    # create an empty graph
    G = nx.Graph()
    cloud_capacity = 300

    G.add_node(1, capacity = 15, cost = 5, cost_of_powering_on = 2)
    G.add_node(2, capacity = 20, cost = 4, cost_of_powering_on = 2)
    G.add_node(3, capacity = 25, cost = 2, cost_of_powering_on = 2)
    G.add_node(10, capacity = 30, cost = 3, cost_of_powering_on = 2)
    G.add_node(4, capacity=cloud_capacity, delay=1, cost_of_powering_on = 3, cost = 7)
    G.add_node(5, capacity = 20, cost = 4, cost_of_powering_on = 2)
    G.add_node(6, capacity = 25, cost = 2, cost_of_powering_on = 2)
    G.add_node(11, capacity = 30, cost = 3, cost_of_powering_on = 2)
    G.add_node(12, capacity = 35, cost = 2, cost_of_powering_on = 2)
    G.add_node(7, capacity = 20, cost = 4, cost_of_powering_on = 2)
    G.add_node(8, capacity = 25, cost = 2, cost_of_powering_on = 2)
    G.add_node(9, capacity = 30, cost = 3, cost_of_powering_on = 2)


    for node in G.nodes():
        if node == 4:
            continue
        G.nodes[node]['delay'] = random.randint(1,2)

    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 10)
    G.add_edge(10, 4)
    G.add_edge(1, 5)
    G.add_edge(5, 6)
    G.add_edge(6, 11)
    G.add_edge(11, 12)
    G.add_edge(12, 4)
    G.add_edge(1, 7)
    G.add_edge(7, 8)
    G.add_edge(8, 9)
    G.add_edge(9, 4)

    link_factor = 0.5
    for edge in G.edges():
        G.edges[edge]['capacity'] = random.randint(int(50*link_factor),int(100*link_factor))
        G.edges[edge]['delay'] = random.randint(1,2)
        G.edges[edge]['cost'] = random.randint(1,2)
    return G

def slice_generator(G, slice_num, user_per_slice):
    
    max_capacity_node = max(G.nodes(), key=lambda n: G.nodes[n]['capacity'])
    # Generate slices with fixed number of users and requirements of data rate and delay
    M = slice_num # Number of slices
    users_per_slice = user_per_slice # Fixed number of users per slice
    slices = []
    slices_data_rate = [10, 5, 15]
    slices_delay = [1000, 1000, 1000]
    for m in range(M):
        slice_users = []
        user_nodes=[]

        for i in range(users_per_slice):
            data_rate = random.randint(int(slices_data_rate[m]*0.5), slices_data_rate[m])
            delay = slices_delay[m]
            slice_users.append({ 'slice_id': m+1, 'node': 1, 'id': i+1, 'data_rate': data_rate, 'delay': delay})
        slices.append(slice_users)
    #print(slices)

    # Find all paths from each user node to the master node
    user_paths = {}
    for slice in slices:
        #print(slice)
        for user in slice:
            user_node = 1
            user['paths'] = list(nx.all_simple_paths(G, user_node, 4))
            #print('----------------------')
            #print(user['paths'])

    return slices
   
def solve_ec_model(G, slices, f):
    
    # Initialize solver
    #model = cp_model.CpModel()
    model = Model("Simple optimization")

    landa_m = {}
    for slice in slices:
        landa_m[str(slice)] = model.addVar(vtype="C", name="landa_m[%s]" % (slice))

    V = list(G.nodes())
    #print(V)
    y_v = {}
    for v in V:
        y_v[str(v)] = model.addVar(vtype="B", name="y_v[%s]" % (v))

    z_m_u_p_ij = {}
    for slice in slices:
        for user in slice:
            P = user['paths']
            #print(P)
            for p in P:
                links = list(zip(p[:-1], p[1:]))
                for e in links:
                    z_m_u_p_ij[str(slice), str(user), str(p), str(e)] = model.addVar(vtype="B", name="z_m_u_p_ij[%s, %s, %s, %s]" % (slice, user, p, e))

    x_m_u_p = {}
    for slice in slices:
        for user in slice:
            PPP = user['paths']
            #print(PPP)
            for ppp in PPP:
                x_m_u_p[str(slice), str(user), str(ppp)] = model.addVar(vtype="B", name="x_m_u_p[%s, %s, %s]" % (slice, user, ppp))

    w_m_u_p_v = {}
    for slice in slices:
        for user in slice:
            PPPP = user['paths']
            #print(PPPP)
            for pppp in PPPP:
                for v in V:
                    w_m_u_p_v[str(slice), str(user), str(pppp), str(v)] = model.addVar(vtype="C", name="w_m_u_p_v[%s, %s, %s, %s]" % (slice, user, pppp, v))

    Epsi = 0.15
    # Define constraints
    for slice in slices:
        model.addCons(landa_m[str(slice)] >= Epsi)

    model.addCons(quicksum(landa_m[str(slice)]  for slice in slices) == 1)

    for slice in slices:
        for user in slice:
            paths = user['paths']
            model.addCons(quicksum(x_m_u_p[str(slice), str(user), str(p)] for p in paths) <= 1)

    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                model.addCons(quicksum(w_m_u_p_v[str(slice), str(user), str(p), str(v)] for v in p) == user['data_rate']*x_m_u_p[str(slice), str(user), str(p)])

    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                for v in p:
                    model.addCons(w_m_u_p_v[str(slice), str(user), str(p), str(v)] == y_v[str(v)] * w_m_u_p_v[str(slice), str(user), str(p), str(v)])

    for slice in slices:
        for user in slice:
            paths = user['paths']
            for path in paths:
                for v in path:
                    before_nodes=[]
                    for vv in path:
                        if vv != v:
                            before_nodes.append(vv)
                        else:
                            before_nodes.append(vv)
                            break
                    links = list(zip(before_nodes[:-1], before_nodes[1:]))
                    for e in links:
                        model.addCons(w_m_u_p_v[str(slice), str(user), str(path), str(v)] <= z_m_u_p_ij[str(slice), str(user), str(path), str(e)]*1000)
    '''
    for slice in slices:
        for user in slice:
            paths = user['paths']
            break  
        for p in paths:
            for v in p:
                if v == 1 or v ==4:
                    model.addCons(quicksum(w_m_u_p_v[str(slice), str(user), str(p), str(v)] for user in slice) <= landa_m[str(slice)]*G.nodes[v]['capacity']/3)
                else:
                    model.addCons(quicksum(w_m_u_p_v[str(slice), str(user), str(p), str(v)] for user in slice) <= landa_m[str(slice)]*G.nodes[v]['capacity'])

    '''

    for v in G.nodes():
        for slice in slices:
            for user in slice:
                paths = user['paths']
                break
            candid_paths = []
            for p in paths: 
                if p.count(v) != 0:
                    candid_paths.append(p)
            model.addCons(quicksum(w_m_u_p_v[str(slice), str(user), str(p), str(v)] for user in slice for p in candid_paths) <= landa_m[str(slice)]*G.nodes[v]['capacity'])

            

    for slice in slices:
        slice_paths =[]
        for user in slice:
            PP = user['paths']
            for pathss in PP:
                slice_paths.append(pathss)
        for pp in slice_paths:
            candid_users = []
            links = list(zip(pp[:-1], pp[1:]))
            for user in slice:
                if user['paths'].count(pp) != 0:
                    candid_users.append(user) 
            for e in links:
                model.addCons(quicksum(z_m_u_p_ij[str(slice), str(user), str(pp), str(e)]*user['data_rate'] for user in candid_users) <= landa_m[str(slice)]*G.edges[e]['capacity'])
       
    for slice in slices:
        slice_paths =[]
        for user in slice:
            PP = user['paths']
            for pathss in PP:
                slice_paths.append(pathss)
        for p in slice_paths:
            candid_users = []
            links = list(zip(p[:-1], p[1:]))
            for user in slice:
                if user['paths'].count(p) != 0:
                    candid_users.append(user) 
            for user in candid_users:
                model.addCons(quicksum(w_m_u_p_v[str(slice), str(user), str(p), str(v)]*G.nodes[v]['delay'] for v in p) + quicksum(G.edges[e]['delay']* z_m_u_p_ij[str(slice), str(user), str(p), str(e)]*user['data_rate'] for e in links) <= user['delay'])
                
    # Define objective function
    temp1 = []
    for slice in slices:
        slice_paths =[]
        for user in slice:
            PP = user['paths']
            for pathss in PP:
                slice_paths.append(pathss)
        for p in slice_paths:
            candid_users = []
            for user in slice:
                if user['paths'].count(p) != 0:
                    candid_users.append(user) 
            for user in candid_users:
                for v in p:
                    temp1.append(w_m_u_p_v[str(slice), str(user), str(p), str(v)] * G.nodes[v]['cost'])

    temp2=[]
    for slice in slices:
        slice_paths =[]
        for user in slice:
            PP = user['paths']
            for pathss in PP:
                slice_paths.append(pathss)
        for p in slice_paths:
            candid_users = []
            for user in slice:
                if user['paths'].count(p) != 0:
                    candid_users.append(user) 
            links = list(zip(p[:-1], p[1:]))
            for user in candid_users:
                for e in links:
                    temp2.append(z_m_u_p_ij[str(slice), str(user), str(p), str(e)] * G.edges[e]['cost']*user['data_rate'])

    temp3 = []
    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                temp3.append(x_m_u_p[str(slice), str(user), str(p)])
    
    temp4 = []
    for v in V:
        temp4.append(y_v[str(v)]*G.nodes[v]['cost_of_powering_on'])
    
    objvar1 = model.addVar(name="objvar1", vtype= "C", lb=None, ub=None)
    model.addCons(objvar1 >= sum(temp1) + sum(temp2) + sum(temp4) - 1000000*sum(temp3))
    model.setObjective(objvar1, "minimize")
    #model.setObjective(sum(temp3), "maximize")
    model.optimize()
    print(model.getStatus())
    if model.getStatus() == "optimal":
        #print("Optimal value Minimum Cost:", model.getObjVal())

        '''
        print("Solution:")
        for v in V:
            print("  y_v = ",v, model.getVal(y_v[str(v)]))
        print("---------")
        for slice in slices:
                print("---------")
                print("  landa_m = ", model.getVal(landa_m[str(slice)]))
        print("---------")
        '''

        accepted_count = 0
        bandwidth_usage = 0 
        total_cost = 0 
        for slice in slices:
            #print("------")
            for user in slice:
                paths = user['paths']
                for p in paths:
                    #print("  x_m_u_p = ", user['node'], p, model.getVal(x_m_u_p[str(slice), str(user), str(p)]))
                    if model.getVal(x_m_u_p[str(slice), str(user), str(p)]) >= 0.9:
                        #print(model.getVal(x_m_u_p[str(slice), str(user), str(p)]))
                        accepted_count = accepted_count +1
                        links = list(zip(p[:-1], p[1:]))
                        for e in links:
                            bandwidth_usage = bandwidth_usage + model.getVal(z_m_u_p_ij[str(slice), str(user), str(p), str(e)])*user['data_rate']
                            total_cost = total_cost + model.getVal(z_m_u_p_ij[str(slice), str(user), str(p), str(e)])*user['data_rate']*G.edges[e]['cost']
                        for v in p:
                            if v == 1 or v == 4:
                                total_cost = total_cost + model.getVal(w_m_u_p_v[str(slice), str(user), str(p), str(v)])*G.nodes[v]['cost']
                            else:
                                total_cost = total_cost + model.getVal(w_m_u_p_v[str(slice), str(user), str(p), str(v)])*G.nodes[v]['cost']
        for v in G.nodes():
            total_cost = total_cost + model.getVal(y_v[str(v)])*G.nodes[v]['cost_of_powering_on']
                        
        print("accepted requests number is: ", accepted_count, file=f)
        print("Optimal value Minimum Cost:", total_cost, file=f)
        print('Bandwidth usage optimal: ', bandwidth_usage, file=f)

        '''      
        for slice in slices:
            #print("------")
            for user in slice:
                paths = user['paths']
                for p in paths:
                    if model.getVal(x_m_u_p[str(slice), str(user), str(p)]) >= 0.9:
                        print("user data rate is: ", user['data_rate'])
                        for v in p:
                            print("w_m_u_p_v = ", p, v,  model.getVal(w_m_u_p_v[str(slice), str(user), str(p), str(v)]), ' node share:  ', G.nodes[v]['capacity']*model.getVal(landa_m[str(slice)]), ' node capacity  ', G.nodes[v]['capacity'])

                        links = list(zip(p[:-1], p[1:]))
                        for e in links:
                            print("z_m_u_p_v = ", p, e, model.getVal(z_m_u_p_ij[str(slice), str(user), str(p), str(e)]), ' link share: ', G.edges[e]['capacity']*model.getVal(landa_m[str(slice)]), ' edge capacity  ', G.edges[e]['capacity'])
        '''

def solve_heuristic(G, slices, f):
    landa_m={}
    y_v = {}
    x_m_u_p = {}
    w_m_u_p_v = {}
    z_m_u_p_e = {}

    fixed_share=0.15 
    all_data = 0
    for slice in slices:
        slice_all_data = 0
        slice_data_rate = 0
        for user in slice:
            slice_data_rate = user['data_rate']
        slice_all_data = len(slice)*slice_data_rate
        all_data = all_data + slice_all_data

    #print(all_data)
    for slice in slices:
        slice_data_rate = 0
        slice_all_rate = 0
        user_num = len(slice)
        for user in slice:
            slice_data_rate = user['data_rate']
            break
        slice_all_rate = len(slice)*slice_data_rate
        other_share = 1 - len(slices)*fixed_share
        landa_m[str(slice)] = fixed_share + other_share*(slice_all_rate/all_data)
        #print('landa_m  ', landa_m[str(slice)])
    
    path_user_cost = {}
    links_remaining_capacity = {}
    nodes_remaining_capacity = {}

    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                x_m_u_p[str(slice), str(user), str(p)] = 0
                path_user_cost[str(slice), str(user), str(p)] = 0
                
                for e in links:
                    links_remaining_capacity[str(slice), str(e)] = G.edges[e]['capacity']*landa_m[str(slice)]
                    z_m_u_p_e[str(slice), str(user), str(p), str(e)] = 0

                for v in p:
                    y_v[str(v)] = 0
                    nodes_remaining_capacity[str(slice), str(v)] = G.nodes[v]['capacity']*landa_m[str(slice)]
                    w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0
    
    for slice in slices:
        for user in slice:
            paths = user['paths']
            mapping_permut = {}
            for p in paths:
             
                links = list(zip(p[:-1], p[1:]))
                temp1 = 0
                temp2 = 0
                path_total_delay = 0
                user_remaining_rate = user['data_rate']
                link_cap_flag = True
                
                for node in p:    
                    if user_remaining_rate == 0:
                        break 
                    if nodes_remaining_capacity[str(slice), str(node)] == 0:
                        continue 
                    if user_remaining_rate <= nodes_remaining_capacity[str(slice), str(node)]:
                        w_m_u_p_v[str(slice), str(user), str(p), str(node)] = user_remaining_rate
                        nodes_remaining_capacity[str(slice), str(node)] = nodes_remaining_capacity[str(slice), str(node)] - user_remaining_rate
                        user_remaining_rate = 0
                    else:
                        w_m_u_p_v[str(slice), str(user), str(p), str(node)] = nodes_remaining_capacity[str(slice), str(node)]
                        user_remaining_rate = user_remaining_rate - nodes_remaining_capacity[str(slice),  str(node)]
                        nodes_remaining_capacity[str(slice), str(node)] = 0
                        
                    path_total_delay += w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['delay']
                    temp1 += w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['cost']
                    #print(user['id'], '  ', p, '  ', node, '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)], '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['cost'])

                for e in links:
                    if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                        for ee in links:
                            if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] != 1:
                                if ee[1] == e[1]:
                                    if links_remaining_capacity[str(slice),  str(ee)] < user['data_rate']:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay']
                                        link_cap_flag = False
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay']  
                                    break  
                                else:
                                    if links_remaining_capacity[str(slice),  str(ee)] < user['data_rate']:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay']
                                        link_cap_flag = False
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay']
                                         
                            
                            
                if path_total_delay > user['delay'] or user_remaining_rate != 0 or link_cap_flag == False:
                    temp1 = 0
                    temp2 = 0  
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] !=0:
                                    if ee[1] == e[1]:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                                        break
                                    else:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                    for v in p:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0:
                            nodes_remaining_capacity[str(slice), str(v)] += w_m_u_p_v[str(slice), str(user), str(p), str(v)]
                            w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0
                else:
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] !=0:
                                    if ee[1] == e[1]:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                                        break
                                    else:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                    for v in p:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0:
                            nodes_remaining_capacity[str(slice), str(v)] += w_m_u_p_v[str(slice), str(user), str(p), str(v)]
                            w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0

                #print(temp1, '  ', temp2)
                mapping_permut[str(p)] = temp1 + temp2

            mapping_permut2 = {}
            for x, y in mapping_permut.items():
                if y != 0:
                    mapping_permut2[x] = y
            mapping_permut = mapping_permut2
            #print(mapping_permut)

            if mapping_permut != {}:
                min_map = min(mapping_permut, key=mapping_permut.get)
            else: 
                min_map = 0

            #print(str(user))
            
            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                user_remaining_rate = user['data_rate']
                if str(p) == min_map:
                    x_m_u_p[str(slice), str(user), str(p)] = 1
                    path_user_cost[str(slice), str(user), str(p)] = mapping_permut[min_map]
                    #print(path_user_cost[str(slice), str(user), str(p)])
                    
                    
                    #print(p)
                    for node in p:    
                        if user_remaining_rate == 0:
                            break 
                        if nodes_remaining_capacity[str(slice), str(node)] == 0:
                            continue 
                        if user_remaining_rate <= nodes_remaining_capacity[str(slice), str(node)]:
                            w_m_u_p_v[str(slice), str(user), str(p), str(node)] = user_remaining_rate
                            #print(node, '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)])
                            nodes_remaining_capacity[str(slice), str(node)] = nodes_remaining_capacity[str(slice), str(node)] - user_remaining_rate
                            user_remaining_rate = 0
                        else:
                            w_m_u_p_v[str(slice), str(user), str(p), str(node)] = nodes_remaining_capacity[str(slice), str(node)]
                            #print(node, '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)])
                            user_remaining_rate = user_remaining_rate - nodes_remaining_capacity[str(slice),  str(node)]
                            nodes_remaining_capacity[str(slice), str(node)] = 0
                    
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] != 1:
                                    if ee[1] == e[1]:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        #print(ee)
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        break
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        #print(ee)
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                    break
                else:
                    x_m_u_p[str(slice), str(user), str(p)] = 0
                    
    accepted_users_count = 0
    total_cost = 0 
    bandwidth_usage = 0 
    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                if x_m_u_p[str(slice), str(user), str(p)] == 1:
                    accepted_users_count += 1
                    total_cost += path_user_cost[str(slice), str(user), str(p)]
                    for e in links:
                        bandwidth_usage += user['data_rate']*z_m_u_p_e[str(slice), str(user), str(p), str(e)]
    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                for v in p:
                    if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0 and y_v[str(v)] == 0:
                        y_v[str(v)] = 1
                        total_cost += y_v[str(v)]*G.nodes[v]['cost_of_powering_on']

    print('---------------------', file=f)
    print("Heurestic", file=f)
    print('Accepted Number Heurestic:  ', accepted_users_count, file=f)
    print('Total Cost Heurestic:  ', total_cost, file=f)
    print('Bandwidth Usage Heurestic: ', bandwidth_usage, file=f)

def solve_random(G, slices, f):
    landa_m={}
    y_v = {}
    x_m_u_p = {}
    w_m_u_p_v = {}
    z_m_u_p_e = {}

    fixed_share=0.15 
    all_data = 0
    for slice in slices:
        slice_all_data = 0
        slice_data_rate = 0
        for user in slice:
            slice_data_rate = user['data_rate']
        slice_all_data = len(slice)*slice_data_rate
        all_data = all_data + slice_all_data

    #print(all_data)
    for slice in slices:
        slice_data_rate = 0
        slice_all_rate = 0
        user_num = len(slice)
        for user in slice:
            slice_data_rate = user['data_rate']
            break
        slice_all_rate = len(slice)*slice_data_rate
        other_share = 1 - len(slices)*fixed_share
        landa_m[str(slice)] = fixed_share + other_share*(slice_all_rate/all_data)
        #print('landa_m  ', landa_m[str(slice)])
    
    path_user_cost = {}
    links_remaining_capacity = {}
    nodes_remaining_capacity = {}

    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                x_m_u_p[str(slice), str(user), str(p)] = 0
                path_user_cost[str(slice), str(user), str(p)] = 0
                
                for e in links:
                    links_remaining_capacity[str(slice), str(e)] = G.edges[e]['capacity']*landa_m[str(slice)]
                    z_m_u_p_e[str(slice), str(user), str(p), str(e)] = 0

                for v in p:
                    y_v[str(v)] = 0
                    nodes_remaining_capacity[str(slice), str(v)] = G.nodes[v]['capacity']*landa_m[str(slice)]
                    w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0
    random_paths ={}
    for slice in slices:
        for user in slice:
            paths = user['paths']
            mapping_permut = {}
            for p in paths:
             
                links = list(zip(p[:-1], p[1:]))
                temp1 = 0
                temp2 = 0
                path_total_delay = 0
                user_remaining_rate = user['data_rate']
                link_cap_flag = True

                random_path = random.sample(p, len(p))
                random_paths[str(slice), str(user), str(p)] = random_path
                
                for node in random_path:    
                    if user_remaining_rate == 0:
                        break 
                    if nodes_remaining_capacity[str(slice), str(node)] == 0:
                        continue 
                    if user_remaining_rate <= nodes_remaining_capacity[str(slice), str(node)]:
                        w_m_u_p_v[str(slice), str(user), str(p), str(node)] = user_remaining_rate
                        nodes_remaining_capacity[str(slice), str(node)] = nodes_remaining_capacity[str(slice), str(node)] - user_remaining_rate
                        user_remaining_rate = 0
                    else:
                        w_m_u_p_v[str(slice), str(user), str(p), str(node)] = nodes_remaining_capacity[str(slice), str(node)]
                        user_remaining_rate = user_remaining_rate - nodes_remaining_capacity[str(slice),  str(node)]
                        nodes_remaining_capacity[str(slice), str(node)] = 0
                        
                    path_total_delay += w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['delay']
                    temp1 += w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['cost']
                    #print(user['id'], '  ', p, '  ', node, '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)], '  ', w_m_u_p_v[str(slice), str(user), str(p), str(node)]*G.nodes[node]['cost'])

                for e in links:
                    if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                        for ee in links:
                            if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] != 1:
                                if ee[1] == e[1]:
                                    if links_remaining_capacity[str(slice),  str(ee)] < user['data_rate']:
                                        link_cap_flag = False
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay']
                                    break
                                   
                                else:
                                    if links_remaining_capacity[str(slice),  str(ee)] < user['data_rate']:
                                        link_cap_flag = False
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        temp2 += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*G.edges[ee]['cost']*user['data_rate']
                                        path_total_delay += z_m_u_p_e[str(slice), str(user), str(p), str(ee)]*user['data_rate']*G.edges[ee]['delay'] 
                            
                if path_total_delay > user['delay'] or user_remaining_rate != 0 or link_cap_flag == False:
                    temp1 = 0
                    temp2 = 0  
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] !=0:
                                    if ee[1] == e[1]:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                                        break
                                    else:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                    for v in p:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0:
                            nodes_remaining_capacity[str(slice), str(v)] += w_m_u_p_v[str(slice), str(user), str(p), str(v)]
                            w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0
                else:
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] !=0:
                                    if ee[1] == e[1]:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                                        break
                                    else:
                                        links_remaining_capacity[str(slice),  str(ee)] += user['data_rate']
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 0
                    for v in p:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0:
                            nodes_remaining_capacity[str(slice), str(v)] += w_m_u_p_v[str(slice), str(user), str(p), str(v)]
                            w_m_u_p_v[str(slice), str(user), str(p), str(v)] = 0

                #print(temp1, '  ', temp2)
                mapping_permut[str(p)] = temp1 + temp2

            mapping_permut2 = {}
            for x, y in mapping_permut.items():
                if y != 0:
                    mapping_permut2[x] = y
            mapping_permut = mapping_permut2
            #print(mapping_permut)

            if mapping_permut != {}:
                min_map = min(mapping_permut, key=mapping_permut.get)
            else: 
                min_map = 0

            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                user_remaining_rate = user['data_rate']
                if str(p) == min_map:
                    x_m_u_p[str(slice), str(user), str(p)] = 1
                    path_user_cost[str(slice), str(user), str(p)] = mapping_permut[min_map]
                    #print(path_user_cost[str(slice), str(user), str(p)])

                    for node in random_path:    
                        if user_remaining_rate == 0:
                            break 
                        if nodes_remaining_capacity[str(slice), str(node)] == 0:
                            continue 
                        if user_remaining_rate <= nodes_remaining_capacity[str(slice), str(node)]:
                            w_m_u_p_v[str(slice), str(user), str(p), str(node)] = user_remaining_rate
                            nodes_remaining_capacity[str(slice), str(node)] = nodes_remaining_capacity[str(slice), str(node)] - user_remaining_rate
                            user_remaining_rate = 0
                        else:
                            w_m_u_p_v[str(slice), str(user), str(p), str(node)] = nodes_remaining_capacity[str(slice), str(node)]
                            user_remaining_rate = user_remaining_rate - nodes_remaining_capacity[str(slice),  str(node)]
                            nodes_remaining_capacity[str(slice), str(node)] = 0
                    
                    for e in links:
                        if w_m_u_p_v[str(slice), str(user), str(p), str(e[1])] != 0:
                            for ee in links:
                                if z_m_u_p_e[str(slice), str(user), str(p), str(ee)] != 1:
                                    if ee[1] == e[1]:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                                        break
                                    else:
                                        z_m_u_p_e[str(slice), str(user), str(p), str(ee)] = 1
                                        links_remaining_capacity[str(slice),  str(ee)] -= user['data_rate']
                    break
                else:
                    x_m_u_p[str(slice), str(user), str(p)] = 0
                    
    accepted_users_count = 0
    total_cost = 0 
    bandwidth_usage = 0 
    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                links = list(zip(p[:-1], p[1:]))
                if x_m_u_p[str(slice), str(user), str(p)] == 1:
                    accepted_users_count += 1
                    total_cost += path_user_cost[str(slice), str(user), str(p)]
                    for e in links:
                        bandwidth_usage += user['data_rate']*z_m_u_p_e[str(slice), str(user), str(p), str(e)]
    for slice in slices:
        for user in slice:
            paths = user['paths']
            for p in paths:
                for v in p:
                    if w_m_u_p_v[str(slice), str(user), str(p), str(v)] != 0 and y_v[str(v)] == 0:
                        y_v[str(v)] = 1
                        total_cost += y_v[str(v)]*G.nodes[v]['cost_of_powering_on']

    print('---------------------', file=f)
    print("Random", file=f)
    print('Accepted Number Random:  ', accepted_users_count, file=f)
    print('Total Cost Random:  ', total_cost, file=f)
    print('Bandwidth Usage Random: ', bandwidth_usage, file=f)               

f = open("output3.txt", "a")

G1 = static_graph()
G2 = cloud_graph(G1)
slice_num = 3
user_per_slice = [5]

for i in range(len(user_per_slice)):
    print('---------------', user_per_slice[i], '------------------')
    slices = slice_generator(G1, slice_num, user_per_slice[i])

    print("---------------Optimal in-Network-----------------", file=f)
    start_time = time.time()
    solve_ec_model(G1, slices, f)
    end_time = time.time()
    time_elapsed1 = end_time - start_time
    print("Algorithm Optimal in-network took", time_elapsed1, "seconds to run.", file=f)

    print("---------------Optimal Cloud-----------------", file=f)
    start_time = time.time()
    solve_ec_model(G2, slices, f)
    end_time = time.time()
    time_elapsed1 = end_time - start_time
    print("Algorithm Optimal cloud took", time_elapsed1, "seconds to run.", file=f)

    start_time = time.time()
    solve_heuristic(G1, slices, f)
    end_time = time.time()
    time_elapsed1 = end_time - start_time
    print("Algorithm Heurestic took", time_elapsed1, "seconds to run.", file=f)

    start_time = time.time()
    solve_random(G1, slices, f)
    end_time = time.time()
    time_elapsed1 = end_time - start_time
    print("Algorithm Random took", time_elapsed1, "seconds to run.", file=f)


f.close()
