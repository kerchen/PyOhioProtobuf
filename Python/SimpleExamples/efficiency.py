#import binascii
import efficiency_pb2  # protoc appends _pb2, even if proto3!
import simple_pb2

'''
    An example that demonstrates encoding efficiency.
'''


def serialize_float(base_temp):
    msg = efficiency_pb2.SensorDataHistory()

    for i in range(20):
        reading = msg.history.add()
        reading.temperature = base_temp + i
        reading.humidity = 55 + i
        reading.units = simple_pb2.SensorData.REBEL

    return msg.SerializeToString()

def serialize_sint32(base_temp):
    msg = efficiency_pb2.Sint32SensorDataHistory()

    for i in range(20):
        reading = msg.history.add()
        # Scale by 10 to preserve tenths of degree
        reading.temperature = (base_temp + i) * 10 
        reading.humidity = 55 + i
        reading.units = simple_pb2.SensorData.REBEL

    return msg.SerializeToString()

def serialize_int32(base_temp):
    msg = efficiency_pb2.Int32SensorDataHistory()

    for i in range(20):
        reading = msg.history.add()
        # Scale by 10 to preserve tenths of degree
        reading.temperature = (base_temp + i) * 10 
        reading.humidity = 55 + i
        reading.units = simple_pb2.SensorData.REBEL

    return msg.SerializeToString()


def main():
    for base_temp in [-30, 50, 5000, 5000000]:
        print("For base temp = " + str(base_temp))
        payload = serialize_float(base_temp)
        print("   Payload len (float): {}".format(len(payload)))
        payload = serialize_sint32(base_temp)
        print("   Payload len (sint32): {}".format(len(payload)))
        payload = serialize_int32(base_temp)
        print("   Payload len (int32): {}".format(len(payload)))

if __name__ == "__main__":
    main()
