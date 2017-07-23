import binascii
import simple_pb2  # protoc appends _pb2, even if proto3!

''' 
    An example that illustrates the use of a simple protocol with a single
    message type.
'''

def serialize(t, h):
    msg = simple_pb2.SensorData()
    msg.temperature = t
    msg.humidity = h
    msg.units = simple_pb2.SensorData.REBEL
    return msg.SerializeToString()

def deserialize(serialized_data):
    msg = simple_pb2.SensorData()
    msg.ParseFromString(serialized_data)
    t = msg.temperature
    h = msg.humidity
    units = msg.units
    if units == simple_pb2.SensorData.IMPERIAL:
        t = (t - 32) * 5.0 / 9.0
    return (t, h)


def main():
    payload = serialize(27.33, 56)
    print("Payload len: {}".format(len(payload)))
    print("Payload: " + binascii.hexlify(payload))
    t, h = deserialize(payload)
    print("Temperature: {0:.2f} C  Humidity: {1:d} %".format(t, h))

if __name__ == "__main__":
    main()
