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
const float PHASE_STEP = 1.40625;

// ------------Variables------------------
uint8_t phase;
bool phaseOPT = 0;
uint8_t addr;
uint16_t control_word;

// Direct port pointers for LE (still bit-banging LE for speed)
volatile uint8_t *le_port;
uint8_t le_bit;

// -------------Setup----------------------
void setup() {
  Serial.begin(115200);

  pinMode(LE_PIN, OUTPUT);
  digitalWrite(LE_PIN, LOW);

  // Direct port for LE
  le_port = portOutputRegister(digitalPinToPort(LE_PIN));
  le_bit  = digitalPinToBitMask(LE_PIN);

  // Setup SPI
  SPI.begin();
  SPI.beginTransaction(SPISettings(8000000, LSBFIRST, SPI_MODE0)); // 8 MHz, MSB first, mode 0
}

// -------------Main Loop------------------
void loop() {
  // Wait until we have NUM_ELEMENTS bytes from Serial
  if (Serial.available() >= NUM_ELEMENTS) {
    for (uint8_t i = 0; i < NUM_ELEMENTS; i++) {
      phase = Serial.read();
      // OPT bit mirrors 90 degree bit
      phaseOPT = (phase >> 7) & 0x1;
      addr = (i & 0xF);
      control_word = (addr << 9) | (phaseOPT << 8) | phase;

      sendControlWord(control_word);
    }
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
  //this is clever we send 16 bits but on ly the 13 closest to the latch enable are stored into the register.

  // Pulse LE (latch enable)
  *le_port |= le_bit;  // LE high
  asm volatile ("nop\n\t""nop\n\t""nop\n\t"); // tiny delay to meet tLE timing
  *le_port &= ~le_bit; // LE low
}