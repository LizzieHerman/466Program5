'''
Created on Oct 12, 2016

@author: mwitt_000, ColleenRothe
'''
import network_2
import link_2
import threading
from time import sleep
import sys

##configuration parameters
router_queue_size = 0  # 0 means unlimited
simulation_time = 20  # give the network sufficient time to transfer all packets before quitting
route_time = 20

if __name__ == '__main__':
    object_L = []  # keeps track of objects, so we can kill their threads

    '''Copying code from last assignment, same topology'''

    # create network hosts
    host_one = network_2.Host(1)
    object_L.append(host_one)
    host_two = network_2.Host(2)
    object_L.append(host_two)
    host_three = network_2.Host(3)
    object_L.append(host_three)

    # create routers and routing tables for connected clients (subnets)
    # destination, interface, cost
    router_a_rt_tbl_D = {'1': {0: 1, 1: '~', 2: '~', 3: '~'},
                         '2': {0: '~', 1: '~', 2: '~', 3: 1},
                         '3': {0: '~', 1: '~', 2: '~', 3: '~'},
                         'A': {0: 0, 1: 0, 2: 0, 3: 0},
                         'B': {0: '~', 1: 1, 2: '~', 3: '~'},
                         'C': {0: '~', 1: '~', 2: 2, 3: '~'},
                         'D': {0: '~', 1: '~', 2: '~', 3: '~'}}

    router_b_rt_tbl_D = {'1': {0: '~', 1: '~'},
                         '2': {0: '~', 1: '~'},
                         '3': {0: '~', 1: '~'},
                         'A': {0: 1, 1: '~'},
                         'B': {0: 0, 1: 0},
                         'C': {0: '~', 1: '~'},
                         'D': {0: '~', 1: 2}}

    router_c_rt_tbl_D = {'1': {0: '~', 1: '~'},
                         '2': {0: '~', 1: '~'},
                         '3': {0: '~', 1: '~'},
                         'A': {0: 2, 1: '~'},
                         'B': {0: '~', 1: '~'},
                         'C': {0: 0, 1: 0},
                         'D': {0: '~', 1: 1}}

    router_d_rt_tbl_D = {'1': {0: '~', 1: '~', 2: '~'},
                         '2': {0: '~', 1: '~', 2: '~'},
                         '3': {0: '~', 1: 1, 2: '~'},
                         'A': {0: '~', 1: '~', 2: '~'},
                         'B': {0: 2, 1: '~', 2: '~'},
                         'C': {0: '~', 1: '~', 2: 1},
                         'D': {0: 0, 1: 0, 2: 0}}

    router_a_mpls_tbl = {'in_label': ['~','~'],'in_intf': ['0','3'], 'out_label': ['10','12'], 'out_intf': ['2','1']}

    router_b_mpls_tbl = {'in_label': ['12'], 'in_intf': ['0'], 'out_label': ['14'], 'out_intf': ['1']}

    router_c_mpls_tbl = {'in_label': ['10'], 'in_intf': ['0'], 'out_label': ['16'], 'out_intf': ['1']}

    router_d_mpls_tbl = {'in_label': ['14', '16'], 'in_intf': ['0', '2'], 'out_label': ['~', '~'], 'out_intf': ['1', '1']}


    router_a = network_2.Router(name='A',
                              intf_cost_L=[1, 1, 2, 1],
                              intf_capacity_L=[500, 500, 100, 500],
                              rt_tbl_D=router_a_rt_tbl_D,
                              max_queue_size=router_queue_size,
                              mpls_tbl=router_a_mpls_tbl)
    object_L.append(router_a)

    router_b = network_2.Router(name='B',
                              intf_cost_L=[1, 2],
                              intf_capacity_L=[500, 100],
                              rt_tbl_D=router_b_rt_tbl_D,
                              max_queue_size=router_queue_size,
                              mpls_tbl=router_b_mpls_tbl)
    object_L.append(router_b)

    router_c = network_2.Router(name='C',
                              intf_cost_L=[2, 1],
                              intf_capacity_L=[100, 500],
                              rt_tbl_D=router_c_rt_tbl_D,
                              max_queue_size=router_queue_size,
                              mpls_tbl=router_c_mpls_tbl)
    object_L.append(router_c)

    router_d = network_2.Router(name='D',
                              intf_cost_L=[2, 1, 1],
                              intf_capacity_L=[100, 500, 500],
                              rt_tbl_D=router_d_rt_tbl_D,
                              max_queue_size=router_queue_size,
                              mpls_tbl=router_d_mpls_tbl)
    object_L.append(router_d)

    # create a Link Layer to keep track of links between network nodes
    link_layer = link_2.LinkLayer()
    object_L.append(link_layer)

    # add all the links
    # from intf, to intf
    link_layer.add_link(link_2.Link(host_one, 0, router_a, 0))
    link_layer.add_link(link_2.Link(host_two, 0, router_a, 3))
    link_layer.add_link(link_2.Link(router_a, 1, router_b, 0))
    link_layer.add_link(link_2.Link(router_a, 2, router_c, 0))
    link_layer.add_link(link_2.Link(router_b, 1, router_d, 0))
    link_layer.add_link(link_2.Link(router_c, 1, router_d, 2))
    link_layer.add_link(link_2.Link(router_d, 1, host_three, 0))

    # start all the objects
    thread_L = []
    for obj in object_L:
        thread_L.append(threading.Thread(name=obj.__str__(), target=obj.run))

    for t in thread_L:
        t.start()

    #for obj in object_L:
    #    if str(type(obj)) == "<class 'network_2.Router'>":
    #        obj.print_routes()

    #router_a.send_routes(1)  # send routes from A to B
    # router_a.send_routes(2)  # send routes from A to C

    #sleep(route_time)
    #print("\n\nstarting sample messages\n\n")

    # create some send events
    ##for i in range(5):
    #    priority = i % 2
    #   print(priority)
    #   host_one.udt_send(0, 1, 3, 'data', 'Sample client data %d' % i)

    # print the MPLS tables
    for obj in object_L:
        if str(type(obj)) == "<class 'network_2.Router'>":
            obj.print_MPLS()

    host_one.udt_send(0, 1, 3, 'data', 'me: you should really start the Networks assignment; me to me: nah, you have two weeks')
    host_two.udt_send(1, 2, 3, 'data', 'I can\'t believe you called this a dbz meme, that is obviously young Goku and Krillin')

    # give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)


    # join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()

    print("All simulation threads joined")



    # writes to host periodically