import binascii
import threading
import time
import sensor_net_pb2
import socket
import SocketServer
from collections import namedtuple

Node = namedtuple("Node", "address id name")
attached_nodes = []

def handle_connect(con_msg, client_address):
    print "  Device ID: {}".format(con_msg.id.id)
    if con_msg.id.HasField('name'):
        print "  Device name: " + con_msg.id.name
    n = Node(client_address, con_msg.id.id, con_msg.id.name)
    attached_nodes.append(n)

class UDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]
        print "Connection from {0}:{1}".format(self.client_address[0], self.client_address[1])
        print binascii.hexlify(data[1:])
        msg = sensor_net_pb2.Msg()
        msg.ParseFromString(data[1:])
        print "  Msg type: {}".format(msg.type)
        if msg.type == sensor_net_pb2.Msg.CONNECT:
            handle_connect(msg.connect_msg, self.client_address)


class ThreadedServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "192.168.254.47", 48003
    server = ThreadedServer((HOST, PORT), UDPHandler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name

    while True:
        if len(attached_nodes):
            print("{} node(s) attached".format(len(attached_nodes)))
        for n in attached_nodes:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = sensor_net_pb2.Msg()
            msg.type = sensor_net_pb2.Msg.COMMAND

            cmd_msg = sensor_net_pb2.Command()
            cmd_msg.cmd = 33

            msg.command_msg.CopyFrom(cmd_msg)
            payload = msg.SerializeToString()

            header = bytearray(1)
            header[0] = len(payload)

            sock.sendto(header+payload, n.address)
            print "Sent command to {0}:{1}".format(n.id, n.name if n.name else "")

        time.sleep(5)

    server.shutdown()
    server.server_close()
