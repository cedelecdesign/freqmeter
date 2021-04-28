/* FreqCount based Arduino frequency counter.
*  Designed to be used with a python3/PyQt5 interface
*  Copyright 2020 Cedric Pereira.
*  Released under GNU GPL 3 license.
 */
#include <FreqCount.h>

uint8_t scale = 1;
uint8_t ledpin = 13;

void setup() {
  Serial.begin(57600);
  FreqCount.begin(1000);
  pinMode(ledpin, OUTPUT);
  digitalWrite(ledpin, LOW);
}

void loop() {
  String str = "";
  // read frequency if available
  if (FreqCount.available()) {
    unsigned long count = FreqCount.read();
    Serial.println(count * scale);
  }
  // proceed a command if availabe
  if (Serial.available()>= 1) {
    str = Serial.readStringUntil('\n');
    // go to slow mode
    if (str.equals("s")) {
      FreqCount.end();
      scale = 1;
      digitalWrite(ledpin,HIGH);
      delay(100);
      digitalWrite(ledpin,LOW);
      FreqCount.begin(1000);
    }
    //go to fast mode
    else if (str.equals("f")) {
      FreqCount.end();
      scale = 10;
      digitalWrite(ledpin,HIGH);
      delay(100);
      digitalWrite(ledpin,LOW);
      FreqCount.begin(100);
    }
  }
}
