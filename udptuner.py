import socket
import time
import sys

from threading import Thread
from queue import Queue

def logger(msg):
    sys.stdout.write('\n - - - - - - - - - - - - \n')
    sys.stdout.write(str(msg))
    sys.stdout.write('\n - - - - - - - - - - - - \n')

class udp_sender:

    def __init__(self, host, port, payload):
        self.host = host
        self.port = port
        self.addr = (self.host, self. port)
        self.socket_type = socket.AF_INET
        self.socket = socket.socket(self.socket_type, socket.SOCK_DGRAM)
        self.payload = payload
        self.errors = []
        self.counter = 0

    def send_payload(self):
        for packet in self.payload:
            if type(packet) != bytes:
                packet = packet.encode('UTF-8')
            self._send(packet)

    def completed(self):
        if len(self.errors) > 0:  # Check for errors
            return False
        if self.counter > 0:  # Check if data was sent
            return True

    def _send(self, msg):
        try:
            self.socket.sendto(msg, self.addr)
            self.counter += 1
        except socket.error as e:
            self.errors.append(('Packet %s' % self.counter, e))

class sync_client(Thread):

    def __init__(self, host):
        self.host = host
        self.socket_type = socket.AF_INET
        self.socket = None
        self.ports = [80, 443, 554, 587, 8080, 9090, 60000]

    def start(self):
        self.run()

    def run(self):
        self._create_socket()
        self._try_to_bind()
        self.do_listen()

    def do_listen(self):
        self.socket.listen()
        data = self.socket.recv(4096)
        if data:
            self.data += data

    def _create_socket(self):
        try:
            self.socket = socket.socket(self.socket_type, socket.SOCK_STREAM)
        except socket.error as e:
            logger(e)

    def _try_to_bind(self):
        for port in self.ports:
            try:
                self.socket.bind(('', port))
                self.port = port
                logger('Listening on port %s' % port)
                return
            except:
                logger('Unable to bind on port %s' % port)


