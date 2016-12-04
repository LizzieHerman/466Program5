'''
Created on Oct 12, 2016

@author: mwitt_000, LizzieHerman, ColleenRothe, Jason Sanders
'''
from __future__ import print_function
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    #  @param cost - of the interface used in routing
    #  @param capacity - the capacity of the link in bps
    def __init__(self, cost=0, maxsize=0, capacity=500):
        self.in_queue = queue.PriorityQueue(maxsize);
        self.out_queue = queue.PriorityQueue(maxsize);
        self.cost = cost
        self.capacity = capacity  # serialization rate
        self.next_avail_time = 0  # the next time the interface can transmit a packet
        self.num_prior_out_zero = 0
        self.num_prior_out_one = 0
        self.num_prior_in_zero = 0
        self.num_prior_in_one = 0

    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                tuple_S = self.in_queue.get(False)
                pkt_S = tuple_S[1]
                if 1 - tuple_S[0] == 0:
                    self.num_prior_in_zero -= 1
                if 1 - tuple_S[0] == 1:
                    self.num_prior_in_one -= 1
                # if pkt_S is not None:
                #                     print('getting packet from the IN queue')
                return pkt_S
            else:
                tuple_S = self.out_queue.get(False)
                pkt_S = tuple_S[1]
                if 1 - tuple_S[0] == 0:
                    self.num_prior_out_zero -= 1
                if 1 - tuple_S[0] == 1:
                    self.num_prior_out_one -= 1
                # if pkt_S is not None:
                #                     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None

    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, priority, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            if 1-priority == 0:
                self.num_prior_out_zero += 1
            if 1-priority == 1:
                self.num_prior_out_one += 1
            # print('putting packet in the OUT queue')
            self.out_queue.put((priority, pkt), block)

        else:
            if 1-priority == 0:
                self.num_prior_in_zero += 1
            if 1-priority == 1:
                self.num_prior_in_one += 1
            # print('putting packet in the IN queue')
            self.in_queue.put((priority, pkt), block)


## Implements a network layer packet (different from the RDT packet
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    # packet encoding lengths
    src_addr_S_length = 5
    dst_addr_S_length = 5
    prot_S_length = 1
    prior_S_length = 1

    ##@param priority: priority of the packet
    # @param dst_addr: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, priority, src_addr, dst_addr, prot_S, data_S):
        self.priority = priority
        self.src_addr = src_addr
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.prot_S = prot_S

    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()

    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.priority)
        byte_S += str(self.src_addr).zfill(self.src_addr_S_length)
        byte_S += str(self.dst_addr).zfill(self.dst_addr_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        elif self.prot_S == 'reply':
            byte_S += '3'
        else:
            raise ('%s: unknown prot_S option: %s' % (self, self.prot_S))
        byte_S += self.data_S
        return byte_S

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        priority = int(byte_S[0: NetworkPacket.prior_S_length])
        src_addr = int(byte_S[NetworkPacket.prior_S_length: NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length])
        dst_addr = int(
            byte_S[NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length: NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length])
        prot_S = byte_S[
                 NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length: NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        elif prot_S == '3':
            prot_S = 'reply'
        else:
            raise ('%s: unknown prot_S field: %s' % (self, prot_S))
        data_S = byte_S[NetworkPacket.prior_S_length + NetworkPacket.src_addr_S_length + NetworkPacket.dst_addr_S_length + NetworkPacket.prot_S_length:]
        return self(priority, src_addr, dst_addr, prot_S, data_S)


class MPLS_Frame:
    label_S_length = 2
    flag_S_length = 1
    def __init__(self, label, pkt):
        self.flag = '#'
        self.label = label
        self.pkt = pkt

    def to_byte_S(self):
        byte_S = str(self.flag).zfill(self.flag_S_length)
        byte_S += str(self.label).zfill(self.label_S_length)
        byte_S += self.pkt.to_byte_S()
        return byte_S

    @classmethod
    def from_byte_S(self, byte_S):
        label = byte_S[self.flag_S_length : self.flag_S_length + self.label_S_length]
        pkt_S = byte_S[self.flag_S_length + self.label_S_length :]
        pkt = NetworkPacket.from_byte_S(pkt_S)
        return self(label, pkt)


## Implements a network host for receiving and transmitting data
class Host:
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False  # for thread termination

    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)

    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    # @param priority: packet priority
    def udt_send(self, priority, src_addr, dst_addr, prot_S, data_S):
        p = NetworkPacket(priority, src_addr, dst_addr, prot_S, data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(1-priority, p.to_byte_S(), 'out')  # send packets always enqueued successfully

    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            p = NetworkPacket.from_byte_S(pkt_S)
            if p.prot_S == 'data':
                print('%s: received packet "%s"\nPacket has a priority of %d' % (self, pkt_S, p.priority))
                #message = "Reply to: " + p.data_S
                #p2 = NetworkPacket(p.priority, p.dst_addr, p.src_addr, 'reply', message)
                #print('%s: sending a reply packet "%s" to Router %s' % (self, message, p.src_addr))
                #self.udt_send(p.priority, self.addr, p.src_addr, 'reply', p2.to_byte_S())
            elif p.prot_S == 'control':
                # print('%s: received a control packet "%s"\nPacket has a priority of %d' % (self, pkt_S, p.priority))
                print('%s: received a control packet with priority %d' % (self, p.priority))
            elif p.prot_S == 'reply':
                # print('%s: reply packet received  "%s"\nPacket has a priority of %d' % (self, pkt_S, p.priority))
                print('%s: reply packet received with priority %d' % (self, p.priority))
            else:
                raise Exception(
                    '%s: Unknown packet type in packet "%s"\nPacket has a priority of %d' % (self, pkt_S, p.priority))

    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return


# You will need to come up with a message that encodes the state of your routing tables.
# My advise would be to come up with a message class that has a to byte S() from byte S() functions.

class Message:
    num_intf_length = 1
    route_length = 1
    table_item_length = 1
    message_length = 30

    def __init__(self, route_from, num_intf, table):
        self.route_from = route_from
        self.num_intf = num_intf
        self.table = table

    def __str__(self):
        return self.to_byte_S()

    def to_byte_S(self):
        mes = ""
        mes += str(self.route_from).zfill(self.route_length)
        mes += str(self.num_intf).zfill(self.num_intf_length)
        for x in self.table:
            for y in x:
                mes += str(y).zfill(self.table_item_length)

        byte_S =  str(mes).zfill(self.message_length)
        return byte_S

    @classmethod
    def from_byte_S(self, byte_S):
        route_from = str(byte_S[0: self.route_length])
        num_intf = int(byte_S[self.route_length : self.route_length + self.num_intf_length])
        start = self.route_length + self.num_intf_length
        end = self.route_length + self.num_intf_length + self.table_item_length
        table = []
        for i in range(7):
            temp = []
            for j in range(num_intf):
                cost = str(byte_S[start: end])
                if cost is not '~':
                    cost = int(cost)
                temp.append(cost)
                start += self.table_item_length
                end += self.table_item_length

            table.append(temp)

        return self(route_from, num_intf, table)


## Implements a multi-interface router described in class
class Router:
    ##@param name: friendly router name for debugging
    # @param intf_cost_L: outgoing cost of interfaces (and interface number)
    # @param intf_capacity_L: capacities of outgoing interfaces in bps
    # @param rt_tbl_D: routing table dictionary (starting reachability), eg. {1: {1: 1}} # packet to host 1 through interface 1 for cost 1
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_cost_L, intf_capacity_L, rt_tbl_D, max_queue_size, mpls_tbl):
        self.stop = False  # for thread termination
        self.name = name
        # create a list of interfaces
        # note the number of interfaces is set up by out_intf_cost_L
        assert (len(intf_cost_L) == len(intf_capacity_L))
        self.intf_L = []
        for i in range(len(intf_cost_L)):
            self.intf_L.append(Interface(intf_cost_L[i], max_queue_size, intf_capacity_L[i]))
        # set up the routing table for connected hosts
        self.rt_tbl_D = rt_tbl_D
        self.n_intf = len(self.intf_L)
        self.mpls_tbl = mpls_tbl

        ## called when printing the object

    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(self.n_intf):
            pkt_S = None
            # get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            # if packet exists make a forwarding decision
            if pkt_S is not None:
                if pkt_S[0] == '#':
                    mpls = MPLS_Frame.from_byte_S(pkt_S)
                    p = mpls.pkt
                    if p.prot_S == 'data':
                        self.forward_packet(mpls, i)
                    elif p.prot_S == 'reply':
                        self.forward_packet(mpls, i)
                    elif p.prot_S == 'control':
                        self.update_routes(mpls, i)
                    else:
                        raise Exception('%s: Unknown packet type in packet %s' % (self, p))

                else:
                    p = NetworkPacket.from_byte_S(pkt_S)
                    if p.prot_S == 'data':
                        self.forward_packet(p, i)
                    elif p.prot_S == 'reply':
                        self.forward_packet(p, i)
                    elif p.prot_S == 'control':
                        self.update_routes(p, i)
                    else:
                        raise Exception('%s: Unknown packet type in packet %s' % (self, p))

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            net_pkt = None
            j = 0
            if self.name is 'A':
                print('got into a forwarding')
                net_pkt = p
                in_intf = self.mpls_tbl.get('in_intf')
                if str(i) in in_intf:
                    j = in_intf.index(str(i))
            else:
                print(p is MPLS_Frame)
                in_label = p.label
                net_pkt = p.pkt
                in_labels = self.mpls_tbl.get('in_label')
                if in_label in in_labels:
                    j = in_labels.index(in_label)

            out_label = self.mpls_tbl.get('out_label')[j]
            out_intf = int(self.mpls_tbl.get('out_intf')[j])
            if self.name == 'D':
                self.intf_L[out_intf].put( 1- net_pkt.priority, net_pkt.to_byte_S(), 'out', True)
            else:
                mpls_pkt = MPLS_Frame(out_label, net_pkt)
                self.intf_L[out_intf].put(1 - net_pkt.priority, mpls_pkt.to_byte_S(), 'out', True)

        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        print('%s: Received routing update %s' % (self, p))
        send = False
        # get rid of the first six characters....only want the routing table
        p2 = p.to_byte_S()
        p2 = p2[11: len(p2)]
        # get rid of all the excess zeros
        i = 0
        for a in p2:
            if a == '0' or a == '2':
                i += 1
                continue
            else:
                break
        p2 = p2[i: len(p2)]
        # convert this byte_S to a table
        mes = Message.from_byte_S(p2)
        route = str(mes.route_from)
        # find what interfaces and costs to get from self to route
        col_to = self.rt_tbl_D[route]
        cost_to = []
        for q in col_to:
            cost_to.append(col_to[q])

        for row in range(self.n_intf):
            a = cost_to[row]
            if a is '~':
                continue
            else:
                route_table = list(mes.table)
                col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
                col = 0
                for x in route_table:
                    for y in x:
                        # add cost to values from route_table
                        if y is not "~":
                            y = int(y) + int(a)
                            cur_col = self.rt_tbl_D.get(col_nam[col])
                            cur_val = cur_col.get(row)
                            if cur_val is not '~':
                                cur_val= int(cur_val)
                                if cur_val > y:
                                    self.rt_tbl_D[col_nam[col]][row] = y
                                    send = True
                            else:
                                self.rt_tbl_D[col_nam[col]][row] = y
                                send = True
                    col += 1

        # print("UPDATE table is", self.rt_tbl_D)

        # need some kind of boolean/loop to keep going until no change
        if send is True:
            if self.name == 'A':
                self.send_routes(1) # send routes to B
                self.send_routes(2) # send routes to C
            if self.name == 'B':
                self.send_routes(0) # send routes to A
                self.send_routes(1) # send routes to D
            if self.name == 'C':
                self.send_routes(0) # send routes to A
                self.send_routes(1) # send routes to D
            if self.name == 'D':
                self.send_routes(0) # send routes to B
                self.send_routes(2) # send routes to C

    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        table = []
        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            temp = []
            cur = self.rt_tbl_D.get(name)
            for j in range(self.n_intf):
                temp.append(cur.get(j))
            table.append(temp)

        p2 = Message(self.name, self.n_intf, table)

        priority = 1 # I think the control packets should be high priority

        p = NetworkPacket(priority, 0, 0, 'control', p2.to_byte_S())

        try:
            # TODO: add logic to send out a route update
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(1-priority, p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        num = 11 + self.n_intf * 3
        if num % 2 != 0:
            num += 1
        for i in range(num):
            if i == num/2:
                print("COST", end="")
            else:
                print("-", end="")

        print("-\nFrom Interface:", end="")
        for i in range(self.n_intf):
            print(" ", i, end="")

        print("\n\t       -", end="")
        for i in range(self.n_intf):
            print("---", end="")

        col_nam = ['1', '2', '3', 'A', 'B', 'C', 'D']
        for name in col_nam:
            x = self.rt_tbl_D.get(name)
            if name == '1':
                print("\nTo Host:   ", name, "|", end="")
            elif name == 'A':
                    print("\nTo Router: ", name, "|", end="")
            #elif name == 'B':
            #    print("   Cost\n\t   ", name, "|", end="")
            else:
                print("\n\t   ", name, "|", end="")
            for y in x:
                print(" ", x[y], end="")

        print("\n")#\t\tCost\n")


    ## thread target for the host to keep forwarding data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print(threading.currentThread().getName() + ': Ending')
                return

