import binascii
import threading
import time
import sensor_pb2_v2_pb2 as sensor_pb2_pb2
import socket
import SocketServer
from collections import namedtuple

''' Updated to use protocol version 2. '''

Node = namedtuple("Node", "address id name keeps_history")
attached_nodes = []

def handle_connect(con_msg, client_address):
    print("  Device ID: {0:d} (0x{0:x})".format(con_msg.dev_id.id))
    if con_msg.dev_id.HasField('name'):
        print("  Device name: " + con_msg.dev_id.name)
    print("  Keeps history: " + str(con_msg.dev_id.keeps_history))
    n = Node(client_address,
             con_msg.dev_id.id,
             con_msg.dev_id.name,
             con_msg.dev_id.keeps_history)
    attached_nodes.append(n)

def print_data(d):
    if d.HasField('temperature'):
        print("  t: {:2.1f}".format(d.temperature/10.0)),
    if d.HasField('humidity'):
        print("  h: {:2.1f}".format(d.humidity/10.0)),
    if d.HasField('rainfall'):
        print("  r: {:2.1f}".format(d.rainfall)),
    if d.HasField('pressure'):
        print("  p: {:2.1f}".format(d.pressure))
    else:
        print("")

def handle_report(rpt_msg):
    print("Rec'd data report from {0:d} (0x{0:x})".format(rpt_msg.dev_id.id))
    if rpt_msg.HasField('data'):
        print_data(rpt_msg.data)
    for d in rpt_msg.data_history:
        print_data(d)

class UDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]
        print("Packet from {0}:{1}".format(
                self.client_address[0], self.client_address[1]))
        #print(binascii.hexlify(data[1:]))
        msg = sensor_pb2_pb2.Msg()
        msg.ParseFromString(data[1:])
        if msg.msg_type == sensor_pb2_pb2.Msg.CONNECT:
            handle_connect(msg.connect_msg, self.client_address)
        elif msg.msg_type == sensor_pb2_pb2.Msg.REPORT:
            handle_report(msg.report_msg)
        else:
            print("Unknown message type.")


class ThreadedServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "192.168.254.47", 48003
    #HOST, PORT = "localhost", 48003
    server = ThreadedServer((HOST, PORT), UDPHandler)
    ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:" + server_thread.name)

    hist_count = 0
    cmd_name = 'REPORT'
    while True:
        # Tell all attached nodes to report their current data.
        if len(attached_nodes):
            print("{} node(s) attached".format(len(attached_nodes)))
        for n in attached_nodes:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg = sensor_pb2_pb2.Msg()
            msg.msg_type = sensor_pb2_pb2.Msg.COMMAND

            cmd_msg = sensor_pb2_pb2.Command()
            if n.keeps_history:
                hist_count += 1
                if hist_count < 12:
                    cmd_msg.cmd_type = sensor_pb2_pb2.Command.REPORT_DATA_HISTORY
                    cmd_name = 'REPORT_DATA_HISTORY'
                else:
                    hist_count = 0
                    cmd_msg.cmd_type = sensor_pb2_pb2.Command.CLEAR_DATA_HISTORY
                    cmd_name = 'CLEAR_DATA_HISTORY'
            else:
                cmd_msg.cmd_type = sensor_pb2_pb2.Command.REPORT_DATA
                cmd_name = 'REPORT'

            msg.command_msg.CopyFrom(cmd_msg)
            payload = msg.SerializeToString()

            header = bytearray(1)
            header[0] = len(payload)

            sock.sendto(header+payload, (n.address[0], n.address[1]))
            print("Sent '{0}' command to {1:d} (0x{1:x}){2} {3}".format(
                    cmd_name, n.id, " \""+n.name+"\"" if n.name else "",
                    n.address))

        time.sleep(5)

    server.shutdown()
    server.server_close()
