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

class sync_server(Thread):

    def __init__(self):
        self.socket = None
        self.socket_type = socket.AF_INET
        self.ports = [80, 443, 554, 587, 8080, 9090, 60000]
        self.handshake_msg = b'UDPTunerSyncMsg'

    def start(self):
        self.run()

    def run(self):
        self._create_socket()
        self._bind()
        self._listen()

    def terminate(self):
        self.socket.close()
        exit()

    def _create_socket(self):
        try:
            self.socket = socket.socket(self.socket_type, socket.SOCK_STREAM)
        except socket.error as e:
            logger(e)

    def _bind(self):
        for port in self.ports:
            try:
                self.socket.bind(('', port))
                self.port = port
                logger('Listening on port %s' % port)
                return
            except:
                logger('Unable to bind on port %s' % port)
        logger('Unable to bind, please try specifying a known free port')

    def _listen(self):
        self.socket.listen(1)
        while True:
            try:
                s, client_addr = self.socket.accept()
                self._handle_client(s, client_addr)
            except KeyboardInterrupt:
                self.terminate()
            except socket.error as e:
                logger(e)

    def _handle_client(self, s, addr):
        logger('Received connection from %s on port %s' % (addr[0], addr[1]))
        self._handshake(s, addr)

    def _handshake(self, sock, addr):
        logger('Syncing with client . . .')
        sock.send(self.handshake_msg)
        data = sock.recv(512)
        if data and data == self.handshake_msg:
            self.sync_time(sock)
        else:
            logger('Received invalid handshake!')
            logger('Waiting for new connection . . .')
            sock.close()
            self._listen()

    def sync_time(self, sock):
        logger('Syncing time . . .')
        stamps = ':'.join([str(time.time()) for x in range(30)])
        sock.send(stamps.encode('UTF-8'))
        data = sock.recv(1024).decode()
        stamps = stamps.split(':')
        client_stamps = data.split(':')
        if len(client_stamps) == 30:
            stamps = [float(x) for x in stamps]
            client_stamps = [float(x) for x in client_stamps]
            deltas = [x - y for x in stamps for y in client_stamps]
            self.time_delta = sum(deltas)/float(len(deltas))
            logger('Time Delta: ' + str(round(self.time_delta, 4)))

class sync_client(sync_server):

    def __init__(self, host, port):
        self.target = (host, port)
        self.socket_type = socket.AF_INET
        self.socket = None
        self.handshake_msg = b'UDPTunerSyncMsg'

    def run(self):
        self._create_socket()
        self._connect()

    def terminate(self):
        try:
            self.socket.close()
        except:
            pass
        exit()

    def sync_time(self):
        logger('Syncing time . . .')
        stamps = ':'.join([str(time.time()) for x in range(30)])
        data = self.socket.recv(1024).decode()
        self.socket.send(stamps.encode('UTF-8'))
        stamps = stamps.split(':')
        client_stamps = data.split(':')
        if len(client_stamps) == 30:
            stamps = [float(x) for x in stamps]
            client_stamps = [float(x) for x in client_stamps]
            deltas = [x - y for x in stamps for y in client_stamps]
            self.time_delta = sum(deltas)/float(len(deltas))
            logger('Time Delta: ' + str(round(self.time_delta, 4)))

    def _connect(self):
        try:
            self.socket.connect(self.target)
            self._handshake()
        except socket.error as e:
            logger(e)

    def _handshake(self):
        data = self.socket.recv(512)
        if data and data == self.handshake_msg:
            self.socket.send(self.handshake_msg)
            self.sync_time()
        else:
            logger('Received invalid handshake!')
            logger('Terminating . . .')
            self.terminate()
