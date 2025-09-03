const int NUM_ELEMENTS = 16;
uint16_t phases[NUM_ELEMENTS];
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
}

void loop(){
  if (Serial.available() >= 2 * NUM_ELEMENTS){
    for (int i=0; i < NUM_ELEMENTS; i++){
      byte high = Serial.read();
      byte low = Serial.read();
      phases[i] = (high << 8)| low; //16 bits [high bits,lowbits]
    }

  for (int i=0; i < NUM_ELEMENTS / 2 ; i++){
    //Atmega2560 microcontroller only has one core so this isn't truly parallel

    //Group 1 (phase shifters 1-8)Chip Select and Serial from phase

    //Group 2 (phase shifters 9-16)Chip Select and Serial from phase

  }

  }
}
