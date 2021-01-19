/*
 *  Bluetooth Low Energy Board Debugging
 *  for WaWiCo Tests
 *  
 *  by: Joshua Hrisko
 *      Maker Portal x WaWiCo
 * 
 */

String str = "";
bool ser_input = false;

void setup() {
  SerialUSB.begin(9600);
  while (!SerialUSB){};
  Serial1.begin(9600);
  while (!Serial1){};
}

void loop() {
  if (Serial1.available()){
    char ser_byte = Serial1.read();
    str+=ser_byte;
    if (ser_byte=='\n'){
      SerialUSB.print(str);
      str="";
      ser_input=false;
    }
  }
  if (SerialUSB.available()){
    Serial1.write(SerialUSB.read());
  }
}
