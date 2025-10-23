/*
 * Project:   GUI Controlled Phase Shifter
 * File:      main.ino
 * Author:    Kobe Prior
 * Board:     Arduino Mega (ATmega 2560)
 *
 * Description:
 *    Drives the PE44280 8-bit phase shifter using serial input from a GUI.
 *    Implements faster clock generation using direct port manipulation
 *    for more precise timing (~1 µs high/low).
 */
#include <math.h>
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

// -------------Setup----------------------
void setup() {
  Serial.begin(115200);

  pinMode(SI_PIN, OUTPUT);
  pinMode(CLK_PIN, OUTPUT);
  pinMode(LE_PIN, OUTPUT);

  digitalWrite(SI_PIN, LOW);
  digitalWrite(CLK_PIN, LOW);
  digitalWrite(LE_PIN, LOW);
}

// -------------Main Loop------------------
void loop() {
  if (Serial.available() >= NUM_ELEMENTS) {
    for (uint8_t i = 0; i < NUM_ELEMENTS; i++) {
      phase = Serial.read();
      //the opt bit mirrors the 90 degree bit
      phaseOPT = (phase >> 7) & 0x1;
      addr = (i & 0xF);
      control_word = (addr << 9) | (phaseOPT << 8) | phase;
      sendControlWord(control_word);
    }
  }
}


static inline void short_nop_delay_5(){
  asm volatile (
    "nop\n\t"
    "nop\n\t"
    "nop\n\t"
    "nop\n\t"
    "nop\n\t"
    ::: "memory"
  );
}
// --------------Fast Bit-Banging ----------
void sendControlWord(uint16_t word) {
  /*
  @brief sends control word LSB to MSB as directed by datashee
  */
  
  // Get direct port registers for speed
  //digitalPinToPort returns port
  // portOutputRegister returns a pointer to emmory mapped output registor for port
  //This allows us direct access to flip the actual bits in the port hardware registers
  volatile uint8_t *clk_port = portOutputRegister(digitalPinToPort(CLK_PIN));
  volatile uint8_t *si_port  = portOutputRegister(digitalPinToPort(SI_PIN));
  volatile uint8_t *le_port  = portOutputRegister(digitalPinToPort(LE_PIN));
  //each port controls 8 pins these functions identify which bit is which pin
  uint8_t clk_bit = digitalPinToBitMask(CLK_PIN);
  uint8_t si_bit  = digitalPinToBitMask(SI_PIN);
  uint8_t le_bit  = digitalPinToBitMask(LE_PIN);

  //iterate through the 13 bit control word lsb first
  for (uint8_t i = 0; i < 13; i++) {
    if ((word >> i) & 0x1)
      //if the bit is 1 set SI high
      //or it with the mask
      *si_port |= si_bit;
    else
      //if the bit 0 low set SI low
      *si_port &= ~si_bit;

    // ~1 µs pulse using tuned NOP delay
    short_nop_delay_5();
    *clk_port |= clk_bit; //clock high
    short_nop_delay_5();
    *clk_port &= ~clk_bit; //clock low
    short_nop_delay_5();
  }

  // LE pulse (latch enable)
  *le_port |= le_bit; //latch high
  short_nop_delay_5();
  *le_port &= ~le_bit; //latch low

}
