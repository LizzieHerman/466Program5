'''
Created on Oct 12, 2016

@author: mwitt_000, LizzieHerman, ColleenRothe
'''
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
            if 1 - priority == 0:
                self.num_prior_out_zero += 1
            if 1 - priority == 1:
                self.num_prior_out_one += 1
            # print('putting packet in the OUT queue')
            self.out_queue.put((priority, pkt), block)

        else:
            if 1 - priority == 0:
                self.num_prior_in_zero += 1
            if 1 - priority == 1:
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
                print('%s: received packet "%s"' % (self, pkt_S))
                message = "Reply to: " + p.data_S
                p2 = NetworkPacket(p.priority, p.dst_addr, p.src_addr, 'reply', message)
                print('%s: sending a reply packet "%s" to Router %s' % (self, message, p.src_addr))
                self.udt_send(p.priority, self.addr, p.src_addr, 'reply', p2.to_byte_S())
            elif p.prot_S == 'control':
                print('%s: received packet "%s"' % (self, pkt_S))
            elif p.prot_S == 'reply':
                print('%s: reply received packet "%s"' % (self, pkt_S))
            else:
                raise Exception('%s: Unknown packet type in packet %s' % (self, p))

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return


# You will need to come up with a message that encodes the state of your routing tables.
# My advise would be to come up with a message class that has a to byte S() from byte S() functions.

class Message:
    table_item_length = 1  ##1???

    def __init__(self, zero_one, zero_two, one_one, one_two):
        self.table = {1: {0: zero_one, 1: one_one},
                      2: {0: zero_two, 1: one_two}}

    def __str__(self):
        return self.to_byte_S()

    def to_byte_S(self):
        byte_S = str(self.table.get(1).get(0)).zfill(self.table_item_length)
        byte_S += str(self.table.get(2).get(0)).zfill(self.table_item_length)
        byte_S += str(self.table.get(1).get(1)).zfill(self.table_item_length)
        byte_S += str(self.table.get(2).get(1)).zfill(self.table_item_length)
        return byte_S

    @classmethod
    def from_byte_S(self, byte_S):
        zero_one = str(byte_S[0:Message.table_item_length])
        zero_two = str(byte_S[Message.table_item_length: Message.table_item_length + Message.table_item_length])
        one_one = str(byte_S[
                      Message.table_item_length + Message.table_item_length: Message.table_item_length + Message.table_item_length + Message.table_item_length])
        one_two = str(byte_S[Message.table_item_length + Message.table_item_length + Message.table_item_length:])
        return self(zero_one, zero_two, one_one, one_two)


## Implements a multi-interface router described in class
class Router:
    ##@param name: friendly router name for debugging
    # @param intf_cost_L: outgoing cost of interfaces (and interface number)
    # @param intf_capacity_L: capacities of outgoing interfaces in bps
    # @param rt_tbl_D: routing table dictionary (starting reachability), eg. {1: {1: 1}} # packet to host 1 through interface 1 for cost 1
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_cost_L, intf_capacity_L, rt_tbl_D, max_queue_size):
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

        ## called when printing the object

    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            # get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            # if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S)  # parse a packet out
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
            # TODO: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is (i+1)%2
            self.intf_L[(i + 1) % 2].put(1 - p.priority, p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, (i + 1) % 2))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        print('%s: Received routing update %s' % (self, p))
        send = False
        dict = self.rt_tbl_D

        mess = Message.from_byte_S(p.data_S)
        host = {1,2}
        interface = {0,1}

        for i in host:
            this_row = self.rt_tbl_D.get(i)
            that_row = mess.table.get(i)
            for j in interface:
                this_val = this_row.get(j)
                that_val = that_row.get(j)
                if this_val == that_val or that_val == '~':
                    continue
                elif this_val == '~' or int(this_val) > int(that_val):
                    self.rt_tbl_D[i][j] = that_val
                    send = True


        if send:
            if self.name == 'A':
                self.send_routes(1)
            if self.name == 'B':
                self.send_routes(0)

        print('%s: Received routing update %s from interface %d' % (self, p, i))

    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        dict = self.rt_tbl_D
        p2 = Message(dict.get(1).get(0), dict.get(2).get(0), dict.get(1).get(1), dict.get(2).get(1))
        priority = 1
        p = NetworkPacket(priority, 0, 0, 'control', p2.to_byte_S())

        try:
            self.intf_L[i].put(1-p.priority, p.to_byte_S(), 'out', True)
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass

    ## Print routing table
    def print_routes(self):
        print('%s: routing table' % self)
        dict = self.rt_tbl_D
        print('     Cost To:')
        print('         1 2')
        print('        ----')
        print('From: 0| %s %s ' % (dict.get(1).get(0), dict.get(2).get(0)))
        print('      1| %s %s ' % (dict.get(1).get(1), dict.get(2).get(1)))

    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return