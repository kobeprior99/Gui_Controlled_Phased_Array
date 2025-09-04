const int NUM_ELEMENTS = 16;
const int NUM_BITS = 8;
//uint16_t phases[NUM_ELEMENTS];
int digital_words[NUM_ELEMENTS];
const int LED_PIN = 7;

//digital pins controlling chip select 3-8 demux
//group 1
const int CS1 = 23;
const int CS2 = 24;
const int CS3 = 25;
//group 2
const int CS4 = 26;
const int CS5 = 27;
const int CS6 = 28;
const float PHASE_STEP = 1.40625;
void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(CS1, OUTPUT);
  pinMode(CS2, OUTPUT);
  pinMode(CS3, OUTPUT);
  pinMode(CS4, OUTPUT);
  pinMode(CS5, OUTPUT);
  pinMode(CS6, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  Serial.begin(115200);
  //Serial Lines for Group 1 and Group 2
  Serial2.begin(115200);
  Serial2.begin(115200);

}

void loop(){
  if (Serial.available() >= 2 * NUM_ELEMENTS){
    for (int i=0; i < NUM_ELEMENTS; i++){
      byte high = Serial.read();
      byte low = Serial.read();
      //digital words are used for serial communication from arduino to digital phase shifters
      //get the digtial word and wrap if 2^N bits 0 degrees = 360 degrees
      phase = (high << 8)| low)
      //we bit wise and with 11111111 so any overflow like 256 wraps back to 0. 
      int digital_words[i] = (round( (phase / PHASE_STEP) ) & ( (1 << N_BITS) - 1);
      //phases[i] = (high << 8)| low; //16 bits [high bits,lowbits]
    }

  for (int i=0; i < NUM_ELEMENTS / 2 ; i++){
    //Atmega2560 microcontroller only has one core so this isn't truly parallel
    //chips are updated at approx same speed

    //Group 1 (phase shifters 1-8)Chip Select and Serial from phase
    //example
    // CS1, CS2, CS3, selected
    // 0, 0, 0, chip 1 (index 0)
    
    digitalWrite(CS1, (i >> 2) & 0x01);
    digitalWrite(CS2, (i >> 2) & 0x01);
    digitalWrite(CS3, (i >> 2) & 0x01);
    //send phases[i] to chip i+1, e.g., phase[0] to chip 1
    //TODO: insert SPI or serial write here

    digital_words[i];
    //Group 2 (phase shifters 9-16)Chip Select and Serial from phase
    digitalWrite(CS1, (i >> 2) & 0x1);
    digitalWrite(CS2, (i >> 2) & 0x1);
    digitalWrite(CS3, (i >> 2) & 0x1);
    //send phase[i+8] to chip i+9, e.g., phase[8] to chip 9

    //TODO: insert SPI or serial write here
    digital_words[i+8];
  }

  }
}
