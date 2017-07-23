import argparse
import binascii
import random
import sensor_v2_pb2 as sensor_pb2
import socket
import sys
import time
from collections import deque
from collections import namedtuple

''' Updated to use protocol version 2. '''

Reading = namedtuple("Reading", "temperature humidity rainfall pressure")

max_readings = 30
reading_history = deque([Reading(27, 50, 0, 1000)], max_readings)

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

def send_report(sock, host, port, dev_id, reading, send_history):
    ''' Sends a Report message to the controller '''
    msg = sensor_pb2.Msg()
    msg.report_msg.dev_id.CopyFrom(dev_id)

    if send_history == True:
        for r in reading:
            data = msg.report_msg.data_history.add()
            data.temperature = int(r.temperature * 10)
            data.humidity = int(r.humidity * 10)
            data.rainfall = int(r.rainfall)
            data.pressure = int(r.pressure)
    else:
        msg.report_msg.data.temperature = int(reading.temperature * 10)
        msg.report_msg.data.humidity = int(reading.humidity * 10)
        msg.report_msg.data.rainfall = int(reading.rainfall)
        msg.report_msg.data.pressure = int(reading.pressure)

    payload = msg.SerializeToString()
    return send_packet(sock, host, port, payload)

def handle_command(sock, host, port, cmd_type, dev_id):
    ''' Process Command messages coming from the controller. '''
    global reading_history
    if cmd_type == sensor_pb2.Command.REPORT_DATA:
        print("Sending latest sensor reading.")
        send_report(sock, host, port, dev_id, reading_history[0], False)
    elif cmd_type == sensor_pb2.Command.REPORT_DATA_HISTORY:
        print("Sending sensor reading history ({} readings).".format(len(reading_history)))
        send_report(sock, host, port, dev_id, reading_history, True)
    elif cmd_type == sensor_pb2.Command.CLEAR_DATA_HISTORY:
        print("Clearing reading history.")
        # Preserve the last reading, but reset rainfall.
        r = reading_history[0]
        d = Reading(r.temperature, r.humidity, 0, r.pressure)
        reading_history.clear()
        reading_history.appendleft(d)
    else:
        print("Unknown command.")

def take_reading():
    ''' Simulate reading data from somewhere. '''
    global reading_history
    t = reading_history[0].temperature + random.uniform(-0.25, 0.25)
    h = reading_history[0].humidity + random.uniform(-1, 1)
    r = reading_history[0].rainfall + random.uniform(0, 2)
    p = reading_history[0].pressure + random.uniform(-5, 5)
    d = Reading(t, h, r, p)
    reading_history.appendleft(d)
    return d

def main():
    args = parse_args()

    # Create our ID object
    my_id = sensor_pb2.DeviceIdentification()
    my_id.id = args.dev_id
    if args.dev_name:
        my_id.name = args.dev_name
    my_id.keeps_history = True

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
