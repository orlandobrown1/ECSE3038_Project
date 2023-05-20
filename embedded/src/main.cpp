#include <Arduino.h>
#include <Wifi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "env.h"



const int fan_Pin = 22;
const int light_Pin = 23;
const int presence_pin = 24;

float getvolt(){
  return random(21.0, 33.0);
}
float getpresence(){
  return random(0, 1);
}

void setup() {
  Serial.begin(9600);
  pinMode(fan_Pin, OUTPUT);
  pinMode(light_Pin, OUTPUT);
  pinMode(presence_pin, OUTPUT);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  Serial.println("");

  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // put your main code here, to run repeatedly:
  if(WiFi.status()== WL_CONNECTED){
    HTTPClient http;
    
    String http_response;


    String url = "https://orlando-lab6.onrender.com/api/temperature";
    http.begin(url);
      
      // Specify content-type header
    
      http.addHeader("Content-Type", "application/json");

      StaticJsonDocument<1024> doc;
      String httpRequestData;

      // Serialise JSON object into a string to be sent to the API
    
      doc["temperature"] = getvolt();
      doc["presence"]= getpresence();


      // convert JSON document, doc, to string and copies it into httpRequestData
      serializeJson(doc, httpRequestData);

      // Send HTTP PUT request
      int httpResponseCode = http.PUT(httpRequestData);
      String http_response;

      // check reuslt of PUT request. negative response code means server wasn't reached
      if (httpResponseCode>0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);

        Serial.print("HTTP Response from server: ");
        http_response = http.getString();
        Serial.println(http_response);
      }
      else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
      }
      delay(2000);
      
      http.end(); 
      url = "https://orlando-lab6.onrender.com/api/temperature";    
    http.begin(url);
    httpResponseCode = http.GET();
  




    int httpResponseCode = http.GET();

    Serial.println("");
    Serial.println("");

    if (httpResponseCode>0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);

        Serial.print("Response from server: ");
        http_response = http.getString();
        Serial.println(http_response);
      }
      else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
      }


      StaticJsonDocument<1024> doc;

      DeserializationError error = deserializeJson(doc, http_response);

      if (error) {
        Serial.print("deserializeJson() failed: ");
        Serial.println(error.c_str());
        return;
      }
      
      bool temp = doc["temperature"]; 
      digitalWrite(fan_Pin, temp);

      bool sst = doc["light"]; 
      digitalWrite(light_Pin, sst);

      bool set = doc["presence"];
      digitalWrite(presence_pin, set); 


    http.end();

   }
  else {
    return;
  }
}



