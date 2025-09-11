/*
 * Project:   GUI Controlled Phase Shifter
 * File:      main.ino
 * Author:    Kobe Prior
 * Date:      September 10, 2025
 * Board:     Arduino Mega (ATmega 2560)
 *
 * Description:
 *    This file listens for serial input from the graphical user inteface
 *    script for a list of phase excitations to apply to each port. These phases are converted to digital phase words 
 *    in the format expected by the PE44280 8 bit phase shifter.
 *
 * Hardware Connections:
 *   - GND (Arduino) -> GND (Custom PCB)
 *   - 5V (Arduino) -> 5V (Custom PCB)
 *   - SCL (Arduino) -> CLK (Custom PCB)
 *   - TX2 (Arduino) -> SI1 (Custom PCB)
 *   
 * Dependencies:
 *   - None (uses standard Arduino libraries)
 *
 * Notes:
 *   -
 */

const int NUM_ELEMENTS = 16;
const int PHASE_STEP = 1.40625;
uint16_t phase; //intermediate phase value before converted into phase word

uint8_t digital_word; //the phase word we want to send (8 bits)
bool phaseOPT = 0; //Phase optimization bit(1 bit)
uint8_t addr; //the address of the port that we want to send a command to (4 bits)

//Pack digitalWord [0...7], phaseOPT [8], portAddr in bits (A0-A3) [9..12]
uint16_t control_words[NUM_ELEMENTS];

//flip a byte from MSB->LSB to LSB->MSB
//example 00000011 -> 11000000
byte flipByte(byte b){
  byte r = 0;
  for (int i =0; i< 8; i++){
    r|=((b>>i) &0x1) << (7-i);
  }
  return r; 
}
//example 0011 -> 1100
byte flip4Bits(byte b){
  return ((b & 0x1) << 3) | ((b & 0x2) << 1) | ((b & 0x4) >> 1) | ((b & 0x8) >> 3);
}

void sendControlWord(uint16_t word){
  //shift out 16 bits LSB first
  for (int i = 0; i < 16; i++){
    digitalWrite(DATA_PIN, (word >> i) & 0x1) // send the LSB first
    digitalWrite(CLOCK, HIGH);
    delayMicroseconds(1); //short pulse
    digitalWrite(CLOCK_PIN, LOW);
    delayMicroseconds(1);
  }
  digitalWrit
}


void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  //Recieve Data from the GUI
  Serial.begin(115200);

  //Deliver Commands to 2 groups of phase shifters
  Serial1.begin(115200);
  Serial2.begin(115200);

}

void loop(){

  if (Serial.available() >= 2 * NUM_ELEMENTS){
    for (int i=0; i < NUM_ELEMENTS; i++){

      byte high = Serial.read();
      byte low = Serial.read();
      phase = (high << 8) | low; //16 bits [highbyte lowbyte] -> 16 bit integer

      //the phase opt bit is synchronized with the 90 degree bit
      //the right shift by 1 to get the second least significant bit value which is the 90 degree bit

      phaseOPT = ( phase >> 7 ) & 0x1; //will output 1 if the 90 degree bit is 1 and 0 otherwise
      addr = (i & 0xF); //if i is 2 addr will be 0010
      //flip the address A3 A2 A1 A0 -> A0 A1 A2 A3
      addr = flip4Bits(addr);
      //we bit wise & with 11111111 so any overflow like 256 wraps back to 0.
      digital_word = (round( (phase / PHASE_STEP) ) & ( (1 << N_BITS) - 1);
      //flip digital word D7 D6 D5 D4 D3 D2 D1 D0 -> D0 D1 D2 D3 D4 D5 D6 D7
      digital_word = flipByte(digital_word); 
      //so the phase word looks like A0 A1 A2 A3 OPT D0 D1 D2 D3 D4 D5 D6 D7
      control_words[i] = digital_word | (phaseOPT << 8) | (addr << 9);
      

    }
  //TODO: send control words over serial


  }
}