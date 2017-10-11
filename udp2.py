import time
import socket

    """
    UDPTuner is a tool which allows one to test the flow of UDP packets
    throughout a network. The tool works by sending a variety of network
    packets which are then used for analysis.
    -- Eli Diaz
    """

class udp_sender:
    """ A class used for creating a sending socket """

    def __init__(self, host, port, error_q):
        self.host = host
        self.port = port
        self.addr = (self.host, self.port)
        self.type = socket.AF_INET
        self.socket = socket.socket(self.type, socket.AF_DGRAM)
        self.msg = ''
        self.errors = error_q

    def send(self):
        try:
            self.socket.sendto(self.msg.encode('UTF-8'), self.addr)
           self.errors.put(e)
