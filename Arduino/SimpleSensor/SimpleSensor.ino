#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

// To make it easier to to use this sketch with multiple Arduinos, the network
// settings variables can be read from the Arduino's EEPROM to overwrite their
// initial values defined in this sketch. To use the values stored in EEPROM,
// uncomment the following line (or otherwise #define INIT_FROM_EEPROM). See
// the accompanying WriteEEPROM sketch, which can be used to write the proper
// values in the expected location and order.
// Using EEPROM in this way has some overhead in terms of RAM/ROM usage: 538
// bytes of program space and 104 bytes of dynamic memory. Therefore, if you
// don't need to use multiple Arduinos or if you really need those bytes, leave
// this #define commented out and make sure the intializers of the network
// settings variables below match your hardware and network.
#define INIT_FROM_EEPROM

#ifdef INIT_FROM_EEPROM
#include <EEPROM.h>
#endif

#include <pb.h>
#include <pb_common.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include "sensor_net.pb.h"

// ****** Start of settings that can be initialized from EEPROM ******

// MAC address of Ethernet shield (if MAC_IN_EEPROM is defined, these values
// will be updated to the values read from EEPROM).
byte g_mac[6] = { 0x90, 0xA2, 0xDA, 0x00, 0xD6, 0xE6 };

// Controller IP and port
IPAddress g_controller_IP(192,168,254,47);
uint32_t g_controller_port = 48003;

// Set the static IP address to use if the DHCP fails to assign
IPAddress g_static_IP(192, 168, 254, 15);

// ****** End of settings that can be initialized from EEPROM. ******


// The packet buffer should be big enough to hold an encoded Msg + 1 byte for
// the size of that encoded Msg.
// To conserve RAM/ROM, we don't send a name string in our DeviceIdentification
// messages, so we can make our packet buffer fairly small. Exactly how small
// we can make it depends on the largest message we'll ever send or receive,
// which, in turn, depends on how protobuf encodes messages. So, we'll *ahem*
// empirically find a good max size.
#define MAX_MESSAGE_SIZE 20

char g_packet_buffer[MAX_MESSAGE_SIZE+1];

// Ethernet shield interface 
EthernetUDP g_network_connection;


#ifdef INIT_FROM_EEPROM
void init_from_EEPROM()
{
    int addr = 0;
    byte buffer[4];

    Serial.println("Reading network parameters from EEPROM.");

    // Get MAC
    Serial.print("MAC address: ");
    for ( int i = 0; i < 6; ++i )
    {
        g_mac[i] = EEPROM.read(addr++);
        Serial.print(g_mac[i], HEX);
        if ( i < 5 )
            Serial.print(" ");
    }
    Serial.println("");

    // Get controller IP address
    Serial.print("Controller IP: ");
    for ( int i = 0; i < 4; ++i )
    {
        buffer[i] = EEPROM.read(addr++);
        Serial.print(buffer[i], DEC);
        if ( i < 3 )
            Serial.print(".");
    }
    Serial.println("");
    g_controller_IP = IPAddress( buffer[0], buffer[1], buffer[2], buffer[3] ); 

    // Get controller port
    Serial.print("Controller Port: ");
    byte value;
    g_controller_port = 0;
    for ( int i = 0; i < 4; ++i )
    {
        value = EEPROM.read(addr++);
        g_controller_port += uint32_t(value) << (i * 8);
    }
    Serial.println(g_controller_port, DEC);

    // Check static IP address
    Serial.print("Static IP: ");
    for ( int i = 0; i < 4; ++i )
    {
        buffer[i] = EEPROM.read(addr++);
        Serial.print(buffer[i], DEC);
        if ( i < 3 )
            Serial.print(".");
    }
    Serial.println("");
    g_static_IP = IPAddress( buffer[0], buffer[1], buffer[2], buffer[3] ); 
}

#endif // INIT_FROM_EEPROM

void init_device_id( DeviceIdentification& dev_id )
{
    // Use bytes 2-5 of MAC address to create a unique ID. It should be unique
    // if all sensors are using Ethernet shields from the same manufacturer.
    dev_id = DeviceIdentification_init_zero;
    for ( int i = 2; i < 6; ++i )
    {
        dev_id.id += uint32_t(g_mac[i]) << ( (5-i) * 8 );
    }
    // The 'name' field is optional, so we'll leave it empty to save storage.
}


bool send_message( Msg& msg )
{
    uint8_t message_length;
    bool status = false;

    pb_ostream_t stream =
        pb_ostream_from_buffer(g_packet_buffer, sizeof(g_packet_buffer));

    status = pb_encode(&stream, Msg_fields, &msg);
    message_length = stream.bytes_written;

    if ( message_length > sizeof(g_packet_buffer) )
    {
        Serial.print("Uh oh. The encoded message was longer than the buffer.");
        status = false;
    }

    if ( ! status )
    {
        Serial.print("Message encoding failed.");
        return status;
    }

    Serial.print("Sending message. Encoded length: ");
    Serial.print(message_length);
    Serial.println(" bytes");

    if ( g_network_connection.beginPacket(g_controller_IP, g_controller_port))
    {
        g_network_connection.write((char*)(&message_length), 1);
        g_network_connection.write(g_packet_buffer, message_length);
        g_network_connection.endPacket();
    }
    else
    {
        Serial.println("Error sending UDP packet.");
        status = false;
    }

    return status;
}


bool connect_to_controller()
{
    Msg msg = Msg_init_zero;
    msg.msg_type = Msg_MsgType_CONNECT;
    msg.has_connect_msg = true;
    msg.connect_msg = Connect_init_zero;
    init_device_id( msg.connect_msg.dev_id );

    return send_message( msg );
}


void setup()
{
    Serial.begin(9600);
    while ( !Serial )
    {
      ; // Wait for serial port to connect. Needed for native USB port only
    }

#ifdef INIT_FROM_EEPROM
    init_from_EEPROM();
#endif // INIT_FROM_EEPROM

    // Start the Ethernet interface.
    if (Ethernet.begin(g_mac) == 0)
    {
        Serial.println("Failed to configure Ethernet using DHCP");
        Ethernet.begin(g_mac, g_static_IP);
    }
    Serial.print("IP address: ");
    Serial.println(Ethernet.localIP());

    // Give the Ethernet shield a second to initialize.
    delay(1000);
  
    g_network_connection.begin(g_controller_port);

    Serial.print("Packet buffer size: ");
    Serial.println(sizeof(g_packet_buffer));

    Serial.println("Attempting connection to the controller.");
    while ( ! connect_to_controller() )
    {
        delay(3000);
        Serial.println("Failed to send connection msg to the controller. Retrying.");
    }
}


void loop()
{
#ifndef ARDUINO_AVR_UNO
    int pkt_size = g_network_connection.parsePacket();

    if ( pkt_size )
    {
        bool status;

        Serial.print("Incoming! ");
        Serial.print(pkt_size);
        Serial.println(" bytes");
        g_network_connection.read(g_packet_buffer, sizeof(g_packet_buffer)-1);

        Msg msg = Msg_init_zero;
        pb_istream_t stream = pb_istream_from_buffer(&g_packet_buffer[1], g_packet_buffer[0]);
        status = pb_decode(&stream, Msg_fields, &msg);

        if ( status )
        {
            Serial.print("Decoded message type: ");
            Serial.println(msg.msg_type);
        }
        else
        {
            Serial.println("Decode failed. :(");
        }
    }

    delay(5000);
#endif
    /*
    if ( g_network_connection.beginPacket(g_controller_IP, g_controller_port ) )
    {
        g_network_connection.write("hello periodic");
        g_network_connection.endPacket();
    }
    else
    {
        Serial.println("Error sending UDP packet.");
    }
    */
}
