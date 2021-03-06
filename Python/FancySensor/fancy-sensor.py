import argparse
import binascii
import random
import sensor_pb2
import socket
import sys
import time
from collections import namedtuple

Reading = namedtuple("Reading", "temperature humidity")

last_reading = Reading(27, 50)

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

def send_packet(sock, host, port, payload):
    ''' Sends header and payload to controller. '''
    payload_len = len(payload)
    header = bytearray(1)
    header[0] = payload_len
    assert(payload_len == header[0]) # Make sure one byte is enough for len!
    #print(binascii.hexlify(msg_bytes))
    bc = sock.sendto(header+payload, (host, port))
    print("Sent {} bytes".format(bc))
    return bc

def send_connect(sock, host, port, dev_id):
    ''' Sends a Connect message to the controller '''
    msg = sensor_pb2.Msg()
    msg.connect_msg.dev_id.CopyFrom(dev_id)

    payload = msg.SerializeToString()
    return send_packet(sock, host, port, payload)

def send_report(sock, host, port, dev_id, reading):
    ''' Sends a Report message to the controller '''
    msg = sensor_pb2.Msg()
    msg.report_msg.dev_id.CopyFrom(dev_id)
    msg.report_msg.data.temperature = int(reading.temperature * 10)
    msg.report_msg.data.humidity = int(reading.humidity * 10)

    payload = msg.SerializeToString()
    return send_packet(sock, host, port, payload)

def handle_command(sock, host, port, cmd_type, dev_id):
    ''' Process Command messages coming from the controller. '''
    global last_reading
    if cmd_type == sensor_pb2.Command.REPORT_DATA:
        print("Sending latest sensor reading.")
        send_report(sock, host, port, dev_id, last_reading)
    else:
        print("Unknown command.")

def take_reading():
    ''' Simulate reading data from somewhere. '''
    global last_reading
    t = last_reading.temperature + random.uniform(-0.25, 0.25)
    h = last_reading.humidity + random.uniform(-1, 1)
    d = Reading(t, h)
    last_reading = d
    return d

def main():
    args = parse_args()

    # Create our ID object
    my_id = sensor_pb2.DeviceIdentification()
    my_id.id = args.dev_id
    if args.dev_name:
        my_id.name = args.dev_name

    # Set up UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(0)

    # Tell the controller we exist
    send_connect(sock, args.host, args.port, my_id)

    time_to_next_reading = 5

    while True:
        # See if we've gotten anything from the controller.
        try:
            packet = sock.recv(1024)
            msg = sensor_pb2.Msg()
            msg.ParseFromString(packet[1:])
            if msg.WhichOneof("msg_type") == "command_msg":
                handle_command(sock, args.host, args.port, msg.command_msg.cmd_type, my_id)
            else:
                print("Unexpected message type rec'd")

        except Exception as ex:
            #template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            #message = template.format(type(ex).__name__, ex.args)
            #print message
            time.sleep(1)

        # Take another sensor reading?
        time_to_next_reading -= 1
        if time_to_next_reading <= 0:
            take_reading()
            time_to_next_reading = 5

    sys.exit(0)


if __name__ == "__main__":
    main()
