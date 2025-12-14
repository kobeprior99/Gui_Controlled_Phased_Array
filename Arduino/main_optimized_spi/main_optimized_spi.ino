/*
 * Project:   GUI Controlled Phase Shifter
 * File:      main_optimized_spi.ino
 * Author:    Kobe Prior (optimized)
 * Board:     Arduino Mega (ATmega 2560)
 *
 * Description:
 *    Drives the PE44280 8-bit phase shifter using serial input from a GUI.
 *    Uses hardware SPI for speed with 16-bit transfers to handle 13-bit control words.
 */

#include <SPI.h>

// -----------PIN Assignments----------------
// #define SI_PIN   51  // MOSI
// #define CLK_PIN  52  // SCK
#define LE_PIN   10  // LATCH
#define NUM_ELEMENTS 16

// -----Variables----
uint8_t phases[NUM_ELEMENTS];
// Direct port pointers for LE (still bit-banging LE for speed)
volatile uint8_t *le_port;
uint8_t le_bit;


// -------------Setup----------------------
void setup() {
  Serial.begin(115200);
  while(!Serial);
  pinMode(LE_PIN, OUTPUT);
  digitalWrite(LE_PIN, LOW);

  // Direct port for LE
  le_port = portOutputRegister(digitalPinToPort(LE_PIN));
  le_bit  = digitalPinToBitMask(LE_PIN);

  // Setup SPI
  SPI.begin();
  SPI.beginTransaction(SPISettings(8000000, LSBFIRST, SPI_MODE0)); // 8 MHz, LSB first, mode 0

}

// -------------Main Loop------------------
void loop() {
  // Wait until we have NUM_ELEMENTS bytes from Serial
  if (Serial.available() >= NUM_ELEMENTS) {
    //get phases
    for (uint8_t i = 0; i < NUM_ELEMENTS; i++){
      phases[i] = Serial.read();
    }

    //send phases to shifters in control word format
    //disable interupts for the spi burst
    noInterrupts();
    for (uint8_t i = 0; i < NUM_ELEMENTS; i++) {
      uint8_t phase = phases[i];
      uint8_t addr = i;
      //the middle is syhcronize to the ninety degree bit
      uint16_t control_word = ((addr << 9) | ((phase & 0x40) << 2) | phase) << 3;
      //note the right shift puts the control word closest to the latch
      //MSB FIRST IS FASTER so reverse it
      SPI.transfer16(control_word);
      //pulse latch
      //no delay needed the time it takes per clock cycle is enough.
      *le_port |= le_bit;  // LE high
      //asm volatile ("nop\n\t"); // tiny delay to meet tLE timing
      *le_port &= ~le_bit; // LE low
    }
    //reenable interupts after spi burst:
    interrupts();
  
  }
}
