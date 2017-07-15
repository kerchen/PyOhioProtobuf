import argparse
import binascii
import sensor_net_pb2
import socket
import sys
import time

#this_script_dir=os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(this_script_dir, '..', '..'))
#HOST, PORT = "192.168.254.47", 48003

def parse_args():
    parser = argparse.ArgumentParser(description='Protobuf Test Client')

    parser.add_argument(
        "--dev-id",
        required=True,
        type=int,
        help="Numeric device ID.")
    parser.add_argument(
        "--dev-name",
        help="Device name.")
    #parser.add_argument(
        #"--set-flag",
        #action='store_true',
        #default=False,
        #help="Set a flag")
    parser.add_argument(
        "--host",
        default="localhost",
        help="The IP address of the controller.")
    parser.add_argument(
        "--port",
        default=48003,
        type=int,
        help="The port that the controller is listening on.")

    args = parser.parse_args()

    return args

def connect_to_controller(sock, host, port, dev_id):
    con_msg = sensor_net_pb2.Connect()
    con_msg.id.CopyFrom(dev_id)

    msg = sensor_net_pb2.Msg()
    msg.type = sensor_net_pb2.Msg.CONNECT
    msg.connect_msg.CopyFrom(con_msg)

    payload = msg.SerializeToString()
    payload_len = len(payload)
    header = bytearray(1)
    header[0] = payload_len
    assert(payload_len == header[0]) # Make sure one byte is enough for len!
    #print binascii.hexlify(msg_bytes)
    print("Sending payload of {} bytes".format(int(header[0])))
    bc = sock.sendto(header+payload, (host, port))
    print("Sent {} bytes".format(bc))


def handle_command(cmd_msg):
    print "Command rec'd. Cmd id: {}".format(cmd_msg.cmd)

def main():
    args = parse_args()

    # Create our ID object
    my_id = sensor_net_pb2.DeviceIdentification()
    my_id.id = args.dev_id
    if args.dev_name:
        my_id.name = args.dev_name

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(0)

    # Tell the controller we exist
    connect_to_controller(sock, args.host, args.port, my_id)

    while True:
        try:
            received = sock.recv(1024)
            msg = sensor_net_pb2.Msg()
            msg.ParseFromString(received[1:])
            if msg.type == sensor_net_pb2.Msg.COMMAND:
                handle_command(msg.command_msg)

            #print "Received: {}".format(received)
        except:
            time.sleep(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
