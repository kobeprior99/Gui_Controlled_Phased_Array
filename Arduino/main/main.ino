/*
 * Project:   GUI Controlled Phase Shifter
 * File:      main.ino
 * Author:    Kobe Prior
 * Date:      September 10, 2025
 * Board:     Arduino Mega (ATmega 2560)
 *
 * Description:
 *    This file allows the arduino to listens for serial input from the graphical user inteface
 *    script for a list of phase excitations to apply to each port. These phases are converted to digital phase words 
 *    in the format expected by the PE44280 8 bit phase shifter.
 *
 * Hardware Connections:
 *   - GND (Arduino) -> GND (Custom PCB)
 *   - 5V (Arduino) -> 5V (Custom PCB)
 *   - SCL (Arduino) -> CLK (Custom PCB)
 *   - MOSI (Arduino) -> SI (Custom PCB)
 *   - Pin 53 (Arduino) -> LE (Custom PCB)
 *   
 * Dependencies:
 *   - None (uses standard Arduino libraries)
 *
 * Notes:
 *   -Min pulse width for TLEPW = 30ns We can target ~ >60ns 
 */

//include SPI library
#include <SPI.h>

//define constants
#define NUM_ELEMENTS 16

//constant fixed phase resolution (step)
const float PHASE_STEP 1.40625

//intermediate phase value before converted into phase word
uint16_t phase; 

//the phase word we want to send (8 bits)
uint8_t digital_word; 

//Phase optimization bit (1 bit) -> tied to 90deg bit in phase word
bool phaseOPT = 0; 

//the address of the port that we want to send a command to (4 bits)
uint8_t addr; 

//Use SS pin as LE
const uint8_t LE_PIN = 53; 

//We will stitch together the phase word opt bit and address into the control word
uint16_t control_word;


void setup() {

  //Recieve Data from the GUI
  Serial.begin(115200);

  //configure latch enable pin
  pinMode(LE_PIN, OUTPUT);
  digitalWrite(LE_PIN, LOW);

  //Start SPI
  SPI.begin();
  SPI.beginTransaction(SPISettings(14000000, LSBFIRST, SPI_MODE0));
}

void loop(){

  if (Serial.available() >= 2 * NUM_ELEMENTS){

    for (uint8_t i=0; i < NUM_ELEMENTS; i++){
      //read high and low bytes
      byte high = Serial.read();
      byte low = Serial.read();

      //stich high and low bytes together to form 16 bit integer[highbyte lowbyte] -> 16 bit integer
      phase = ( high << 8 ) | low; 

      //the phase opt bit is synchronized with the 90 degree bit
      //the right shift by 7 to get the second most significant bit value which is the 90 degree bit
      phaseOPT = ( phase >> 7 ) & 0x1;

      //if i is 2 addr will be 0010
      addr = (i & 0xF); 

      //we bit wise & with 11111111 so any overflow like 256 wraps back to 0.
      digital_word = (uint8_t)( round( ( phase / PHASE_STEP ) ) & ( 0xFF );

      //so the phase word looks like (MSB > LSB) A3 A2 A1 A0 OPT D7 D6 D5 D4 D3 D2 D1 D0
      control_word = ( addr << 9 ) | ( phaseOPT << 8 ) | phase;

      //send control word
      sendControlWord (control_word);

    }

  }

}

void sendControlWord(uint16_t control_word){
  //Send control word LSB to MSB

  //latch width should be a minimum of 30ns we'll use 60ns to be save
  digitalWrite(LE_PIN, HIGH);
  //use 1 no operation for 62.5ns delay ~60ns since we know 30ns is the minimum LE width
  __asm__("nop\n\t");
  digitalWrite(LE_PIN, LOW);
}
