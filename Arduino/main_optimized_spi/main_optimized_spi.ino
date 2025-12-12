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
#define SI_PIN   51  // MOSI
#define CLK_PIN  52  // SCK
#define LE_PIN   53  // SS

#define NUM_ELEMENTS 16

// ------------Variables------------------
uint8_t phase;
uint8_t phases[NUM_ELEMENTS];
bool phaseOPT = 0;
uint8_t addr;
uint16_t control_word;

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
    Serial.readBytes(phases,NUM_ELEMENTS);//more bullet proof
    //debug: repeat back control word
    //uint16_t control_debug[NUM_ELEMENTS];
    for (uint8_t i = 0; i < NUM_ELEMENTS; i++) {
      phase = phases[i];
      // OPT bit mirrors 90 degree bit
      phaseOPT = (phase >> 6) & 0x1;
      addr = (i & 0xF);
      control_word = (addr << 9) | (phaseOPT << 8) | phase;
      //control_debug[i] = control_word << 3;
      sendControlWord(control_word);
    }
    //debug repeat back
    // Send each 16-bit word as 2 bytes (low byte, high byte)
    // for (uint8_t i = 0; i < NUM_ELEMENTS; i++) {
    //    Serial.write(control_debug[i] & 0xFF);        // Low byte
    //    Serial.write((control_debug[i] >> 8) & 0xFF); // High byte
    //  }
  }
}

// --------------Send Control Word via Hardware SPI ----------
void sendControlWord(uint16_t word) {
  /*
   * Sends a 13-bit control word using 16-bit SPI transfer.
   * Pads the LSBs with zeros.
   * Pulses LE after transfer to latch.
   */

  uint16_t tx_word = word << 3; // Align 13-bit word into MSBs of 16-bit transfer
  
  // Transfer 16 bits via SPI
  SPI.transfer16(tx_word);
  //this is clever we send 16 bits but only the 13 closest to the latch enable are stored into the register.
  // Pulse LE (latch enable)
   *le_port |= le_bit;  // LE high
   asm volatile ("nop\n\t""nop\n\t"); // tiny delay to meet tLE timing
   *le_port &= ~le_bit; // LE low
}