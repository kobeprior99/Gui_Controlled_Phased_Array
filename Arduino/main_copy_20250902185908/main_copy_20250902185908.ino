const int NUM_ELEMENTS = 16;
uint16_t phases[NUM_ELEMENTS];
const int LED_PIN = 7;

void setup() {
  pinMode(LED_PIN, OUTPUT);
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
  if (phases[0] == 26){
    digitalWrite(LED_PIN, LOW);
  }
  }
}