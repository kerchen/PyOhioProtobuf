#include <EEPROM.h>

// The following values will be written to EEPROM.
byte g_mac[6] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
byte g_controller_IP[4] = { 192, 168, 0, 1 };
uint32_t g_controller_port = 48003;
byte g_static_IP[4] = { 192, 168, 0, 100 };
// End of values to be written to EEPROM.

void setup()
{
    Serial.begin(9600);
    while ( !Serial )
    {
      ; // Wait for serial port to connect. Needed for native USB port only
    }

    Serial.println("Writing values to EEPROM");

    int addr = 0;

    // Write MAC
    for ( int i = 0; i < 6; ++i )
        EEPROM.write(addr++, g_mac[i]);

    // Write controller IP address
    for ( int i = 0; i < 4; ++i )
        EEPROM.write(addr++, g_controller_IP[i]);

    // Write controller port
    for ( int i = 0; i < 4; ++i )
        EEPROM.write(addr++, 0xFF & (g_controller_port >> (i * 8)));

    // Write static IP address
    for ( int i = 0; i < 4; ++i )
        EEPROM.write(addr++, g_static_IP[i]);

    Serial.println("Values written to EEPROM");
}

void print_mismatch_error( char* var_name, int b, int a )
{
    Serial.print("Uh oh! ");
    Serial.print(var_name);
    Serial.print(" mismatch in byte ");
    Serial.print(b);
    Serial.print(", read from address ");
    Serial.println(a);
}


void loop()
{
    // Verify that what was written in setup() is as expected
    byte value;
    uint32_t port = 0;
    int addr = 0;
    bool error_found = false;

    Serial.println("Verifying values written to EEPROM");

    // Check MAC
    for ( int i = 0; i < 6; ++i )
    {
        value = EEPROM.read(addr++);
        if ( value != g_mac[i] )
        {
            error_found = true;
            print_mismatch_error("MAC", i, addr-1);
        }
    }

    // Check controller IP address
    for ( int i = 0; i < 4; ++i )
    {
        value = EEPROM.read(addr++);
        if ( value != g_controller_IP[i] )
        {
            error_found = true;
            print_mismatch_error("Controller IP", i, addr-1);
        }
    }

    // Check controller port
    for ( int i = 0; i < 4; ++i )
    {
        value = EEPROM.read(addr++);
        if ( value != (0xFF & (g_controller_port >> (i * 8))) )
        {
            error_found = true;
            print_mismatch_error("Controller Port", i, addr-1);
        }
    }

    // Check static IP address
    for ( int i = 0; i < 4; ++i )
    {
        value = EEPROM.read(addr++);
        if ( value != g_static_IP[i] )
        {
            error_found = true;
            print_mismatch_error("Controller IP", i, addr-1);
        }
    }

    if ( ! error_found )
        Serial.println("EEPROM verification SUCCEEDED.");
    else
        Serial.println("EEPROM verification FAILED.");

    delay(30000);
}

