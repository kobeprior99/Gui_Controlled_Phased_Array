const int NUM_ELEMENTS = 16;
uint16_t phases[NUM_ELEMENTS];
const int LED_PIN = 7;

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0){
    //if there is data available at serial
    String msg = Serial.readString();
    if (msg == 'Hi'){
      digitalWrite(LED_PIN, HIGH);
      delay(1000);
      digitalWrite(LED_PIN, LOW);
    }
  }
}
