import socket
import time
import sys

from threading import Thread
from queue import Queue

    """
    UDPTuner is a tool which allows one to test the flow of UDP packets
    throughout a network. The tool works by sending a variety of network
    packets which are then used for analysis.
    -- Eli Diaz
    """

def logger(msg):
    sys.stdout.write('\n' + ' -' * 30 + '\n')
    sys.stdout.write('\t')
    sys.stdout.write(str(msg))
    sys.stdout.write('\n' + ' -' * 30 + '\n')

def payload_gen(size, pkt_size, **kwargs):
    """ Returns an empty payload with x amount of packets """
    ## Packet format:
    ## ((id), (timestamp), ('misc'), (padded size))
    return [{'id':id_, 'timestamp':'', 'misc':kwargs, 'size':pkt_size} for id_ in range(size)]

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
        for pkt in self.payload:
            misc = [k + '|' + str(v) for k, v in pkt['misc'].items()]
            pkt['timestamp'] = str(time.time())
            header = (pkt['id'] + '|' pkt['timestamp'] + '|' +
                      misc).encode('utf-8')
            padding = b'0' * pkt['size']
            packet = header + padding[:pkt['size'] - len(header)]
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

class server(Thread):

    def __init__(self):
        self.socket = None
        self.socket_type = socket.AF_INET
        self.ports = [80, 443, 554, 587, 8080, 9090, 60000]
        self.handshake_msg = b'#' * 8

    def start(self):
        self.run()

    def run(self):
        self._create_socket()
        self._bind()
        self._listen()

    def terminate(self):
        logger('Terminating . . . ')
        self.socket.close()
        exit()

    def _bind(self):
        self.socket = socket.socket(self.socket_type, socket.SOCK_STREAM)
        # Failsafe bind
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
                self.client_sock, self.client_addr = self.socket.accept()
                self._handle_client()
            except KeyboardInterrupt:
                logger('Received CTRL+C')
                self.terminate()
            except socket.error as e:
                logger(e)

    def _handle_client(self):
        addr = self.client_addr
        logger('Received connection from %s on port %s' % (addr[0], addr[1]))
        logger('Syncing with client . . .')
        ## Handshake
        self.client_sock.send(self.handshake_msg)
        data = self.client_sock.recv(512)
        if data and data == self.handshake_msg:
            self.sync_time()
        else:
            logger('Received invalid handshake!')
            logger('Waiting for new connection . . .')
            self.client_sock.close()
            self._listen()

    def sync_time(self):
        logger('Syncing time . . .')
        stamps = ':'.join([str(time.time()) for x in range(30)])
        self.client_sock.send(stamps.encode('UTF-8'))
        data = self.client_sock.recv(1024).decode()
        stamps = stamps.split(':')
        client_stamps = data.split(':')
        if len(client_stamps) == 30:
            stamps = [float(x) for x in stamps]
            client_stamps = [float(x) for x in client_stamps]
            deltas = [x - y for x in stamps for y in client_stamps]
            self.time_delta = sum(deltas)/float(len(deltas))
            logger('Time Delta: ' + str(round(self.time_delta, 4)) + 'ms')
            self._start_test()

    def _start_test(self):
        payload = payload_gen(60000, 1024)
        host, _ = self.client_addr
        self.sender = udp_sender(host, 30000, payload)
        logger('Creating client payload . . .')
        payload_data = str(len(payload)) + ':' + '30000'
        logger('Sending client metadata . . .')
        self.client_sock.send(payload_data.encode('UTF-8'))
        logger('Waiting for client . . .')
        data = self.client_sock.recv(512)
        if data and data == b'UDPTunerClientREADY!':
            logger('Sending UDP payload . . .')
            self.sender.send_payload()
            self.sender.payload = [b'@******#']
            self.sender.send_payload()
        logger('Done, waiting for client report . . .')
        data = self.client_sock.recv(512)
        logger(data.decode())
        self.terminate()

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
            logger('Time Delta: ' + str(round(self.time_delta, 4)) + 'ms')
            self._start_test()

    def _start_test(self):
        logger('Waiting for server . . .')
        data = self.socket.recv(512)
        pkts, recv_port = data.decode('UTF-8').split(':', 2)
        self.udp_sock = socket.socket(self.socket_type, socket.SOCK_DGRAM)
        logger('Binding UDP socket on port %s' % recv_port)
        try:
            self.udp_sock.bind(('', int(recv_port)))
            self.udp_sock.settimeout(5.0)
        except socket.error as e:
            logger(e)
        payload = b''
        logger('Ready to receive UDP data . . .')
        self.socket.send(b'UDPTunerClientREADY!')
        while True:
            try:
                data = self.udp_sock.recv(4096)
            except socket.timeout:
                logger('UDP socket timed out')
                break
            payload += data
            if len(data) == 0:
                break
        logger('Data tranfer complete, now terminating . . .')
        data_len = str(len(payload))
        self.socket.send(('Client received %s bytes of data' %
                         data_len).encode())

        time.sleep(10)
        self.terminate()

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

if sys.argv[1] == 'server':
    server = sync_server()
    server.start()
elif sys.argv[1] == 'client':
    client = sync_client(sys.argv[2], int(sys.argv[3]))
    client.start()
