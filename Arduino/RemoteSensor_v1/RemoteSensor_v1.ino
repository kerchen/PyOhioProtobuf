#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUdp.h>

#include <pb.h>
#include <pb_common.h>
#include <pb_decode.h>
#include <pb_encode.h>
#include "simple.pb.h"

// Enter a MAC address for your controller below.
// Newer Ethernet shields have a MAC address printed on a sticker on the shield
byte mac[] = { 0x90, 0xA2, 0xDA, 0x00, 0xD6, 0xE6 };
IPAddress server(192,168,254,47);
int port = 48003;

char packetBuffer[UDP_TX_PACKET_MAX_SIZE];  //buffer to hold incoming packet

// Set the static IP address to use if the DHCP fails to assign
IPAddress ip(192, 168, 254, 15);

EthernetUDP client;


void setup()
{
    Serial.begin(9600);
    while (!Serial) {
      ; // wait for serial port to connect. Needed for native USB port only
    }

    // start the Ethernet connection:
    if (Ethernet.begin(mac) == 0) {
      Serial.println("Failed to configure Ethernet using DHCP");
      // try to congifure using IP address instead of DHCP:
      Ethernet.begin(mac, ip);
    }
    Serial.print("IP address: ");
    Serial.println(Ethernet.localIP());

    // give the Ethernet shield a second to initialize:
    delay(1000);
    Serial.println("connecting...");
  
    // if you get a connection, report back via serial:
    //if (client.connect(server, port)) {
    //    Serial.println("connected");
    //} else {
      // if you didn't get a connection to the server:
    //    Serial.println("connection failed");
    //}
    client.begin(port);

    /* This is the buffer where we will store our message. */
    uint8_t buffer[128];
    size_t message_length;
    bool status;
    
    /* Encode our message */
    {
        /* Allocate space on the stack to store the message data.
         *
         * Nanopb generates simple struct definitions for all the messages.
         * - check out the contents of simple.pb.h!
         * It is a good idea to always initialize your structures
         * so that you do not have garbage data from RAM in there.
         */
        SimpleMessage message = SimpleMessage_init_zero;
        
        /* Create a stream that will write to our buffer. */
        pb_ostream_t stream = pb_ostream_from_buffer(buffer, sizeof(buffer));
        
        /* Fill in the lucky number */
        message.lucky_number = 13;
        
        /* Now we are ready to encode the message! */
        status = pb_encode(&stream, SimpleMessage_fields, &message);
        message_length = stream.bytes_written;
        
        /* Then just check for any errors.. */
        if (!status)
        {
            Serial.println("Encoding failed"); //: %s", PB_GET_ERROR(&stream));
        }
    }
    
    /* Now we could transmit the message over network, store it in a file or
     * wrap it to a pigeon's leg.
     */

    /* But because we are lazy, we will just decode it immediately. */
    
    {
        /* Allocate space for the decoded message. */
        SimpleMessage message = SimpleMessage_init_zero;
        
        /* Create a stream that reads from the buffer. */
        pb_istream_t stream = pb_istream_from_buffer(buffer, message_length);
        
        /* Now we are ready to decode the message. */
        status = pb_decode(&stream, SimpleMessage_fields, &message);
        
        /* Check for errors... */
        if (!status)
        {
            Serial.println("Decoding failed:");// %s", PB_GET_ERROR(&stream));
        }
        
        /* Print the data contained in the message. */
        Serial.print("Your lucky number was ");// %d!\n", message.lucky_number);
    }


}

void loop() {
    int pkt_size = client.parsePacket();

    if ( pkt_size )
    {
        Serial.print("Incoming! ");
        Serial.print(pkt_size);
        Serial.println(" bytes");
        client.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
        Serial.println("Contents:");
        Serial.println(packetBuffer);
    }

    delay(5000);
    if ( client.beginPacket(server, port ) )
    {
        client.write("hello periodic");
        client.endPacket();
    }
    else
    {
        Serial.println("Error sending UDP packet.");
    }
}
