#include <WiFi.h>
#include <Wire.h>
#include "LiquidCrystal_I2C.h"
#include "DHT11.h"

// ============================================================================
// LCD
// ============================================================================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ============================================================================
// DHT11 Setup
// ============================================================================
#define DHTPIN 33
DHT11 dht11(DHTPIN);

// ============================================================================
// GPIO Pins
// ============================================================================
const int GAS_PIN   = 35;
const int GREEN_LED = 25;
const int RED_LED   = 26;
const int BUZZER    = 27;
const int BUTTON    = 32;

// ============================================================================
// WiFi Credentials
// ============================================================================
const char* ssid     = "wifi name";
const char* password = "password";

// ============================================================================
// ThingSpeak Credentials
// ============================================================================
unsigned long channelID = channelid;
const char* apiKey      = "apikey";

// ============================================================================
// Sensor Variables
// ============================================================================
float temperature   = 0.0;
float humidity      = 0.0;
float allergenLevel = 0.0;
float riskScore     = 0.0;

bool isSafe = false;

float allergenHistory[10] = {0};

int historyIndex = 0;
int proofCount = 0;

// ============================================================================
// Timing
// ============================================================================
unsigned long lastCloudSync = 0;
const unsigned long CLOUD_SYNC_INTERVAL = 20000;

unsigned long lastDHTRead = 0;
const unsigned long DHT_READ_INTERVAL = 2000;

// ============================================================================
// WiFi Client
// ============================================================================
WiFiClient client;

// ============================================================================
// SETUP
// ============================================================================
void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("====================================");
  Serial.println("  ESP32 + ThingSpeak + DHT11");
  Serial.println("====================================");
  Serial.println();

  // --------------------------------------------------------------------------
  // DHT11
  // --------------------------------------------------------------------------
  Serial.println("Initializing DHT11 on GPIO 33...");
  Serial.println("DHT11 Initialized");

  // --------------------------------------------------------------------------
  // LCD
  // --------------------------------------------------------------------------
  Wire.begin(21, 22);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("ALLERGEN SYSTEM");

  lcd.setCursor(0, 1);
  lcd.print("DHT11 + GAS");

  // --------------------------------------------------------------------------
  // GPIO
  // --------------------------------------------------------------------------
  pinMode(GAS_PIN, INPUT);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  pinMode(BUTTON, INPUT);

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER, LOW);

  // --------------------------------------------------------------------------
  // Initialize allergen history
  // --------------------------------------------------------------------------
  for (int i = 0; i < 10; i++) {
    allergenHistory[i] = 0.0;
  }

  // --------------------------------------------------------------------------
  // WiFi
  // --------------------------------------------------------------------------
  connectToWiFi();

  delay(2000);

  lcd.clear();

  Serial.println("System Ready");
  Serial.println();
}

// ============================================================================
// LOOP
// ============================================================================
void loop() {

  // Read sensors
  readDHT11();
  readGasSensor();

  // Process sensor data
  calibrateSensors();
  calculateContamination();
  calculateRisk();

  // Update outputs
  updateLCD();
  updateLEDs();

  // --------------------------------------------------------------------------
  // ThingSpeak upload every 20 seconds
  // --------------------------------------------------------------------------
  if (millis() - lastCloudSync >= CLOUD_SYNC_INTERVAL) {

    sendToThingSpeak();

    lastCloudSync = millis();
  }

  // --------------------------------------------------------------------------
  // Proof button
  // --------------------------------------------------------------------------
  if (digitalRead(BUTTON) == HIGH) {

    delay(50);

    if (digitalRead(BUTTON) == HIGH) {

      requestProof();

      delay(500);
    }
  }

  delay(1000);
}

// ============================================================================
// WIFI CONNECTION
// ============================================================================
void connectToWiFi() {

  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 20) {

    delay(500);

    Serial.print(".");

    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println();
    Serial.println("WiFi Connected!");

    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected");

    lcd.setCursor(0, 1);
    lcd.print(WiFi.localIP());

    delay(2000);

  } else {

    Serial.println();
    Serial.println("WiFi Failed!");

    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("WiFi Failed");

    lcd.setCursor(0, 1);
    lcd.print("Offline Mode");
  }
}

// ============================================================================
// DHT11 READING
// ============================================================================
void readDHT11() {

  // DHT11 should not be read more frequently than every 2 seconds
  if (millis() - lastDHTRead < DHT_READ_INTERVAL) {
    return;
  }

  lastDHTRead = millis();

  // IMPORTANT:
  // The installed DHT11 library expects int& arguments.
  int tempInt = 0;
  int humidityInt = 0;

  int result = dht11.readTemperatureHumidity(tempInt, humidityInt);

  if (result == 0) {

    // Convert the integer readings to our float variables
    temperature = (float)tempInt;
    humidity = (float)humidityInt;

    Serial.print("DHT11 - Temp: ");
    Serial.print(temperature, 1);

    Serial.print(" C, Humidity: ");
    Serial.print(humidity, 1);

    Serial.println(" %");

  } else {

    Serial.print("DHT11 read error, code = ");
    Serial.println(result);
  }
}

// ============================================================================
// GAS SENSOR
// ============================================================================
void readGasSensor() {

  int gasRaw = analogRead(GAS_PIN);

  // Convert ESP32 ADC reading (0-4095) to 0-500 scale
  allergenLevel = (gasRaw / 4095.0) * 500.0;

  allergenLevel = constrain(allergenLevel, 0.0, 500.0);
}

// ============================================================================
// CALIBRATION / MOVING AVERAGE
// ============================================================================
void calibrateSensors() {

  allergenHistory[historyIndex] = allergenLevel;

  historyIndex = (historyIndex + 1) % 10;

  float sum = 0.0;

  for (int i = 0; i < 10; i++) {

    sum += allergenHistory[i];
  }

  allergenLevel = sum / 10.0;
}

// ============================================================================
// CONTAMINATION CALCULATION
// ============================================================================
void calculateContamination() {

  // Base correction
  allergenLevel *= 0.95;

  // Temperature correction
  if (temperature > 30.0) {

    allergenLevel *= 1.1;
  }

  // Humidity correction
  if (humidity > 70.0) {

    allergenLevel *= 1.05;
  }

  // Limit to maximum value
  allergenLevel = constrain(allergenLevel, 0.0, 500.0);
}

// ============================================================================
// RISK CALCULATION
// ============================================================================
void calculateRisk() {

  riskScore = (allergenLevel / 100.0) * 3.0;

  if (temperature > 30.0) {

    riskScore *= 1.5;
  }

  if (humidity > 70.0) {

    riskScore *= 1.2;
  }

  // Safe if allergen level is below 100
  isSafe = (allergenLevel < 100.0);
}

// ============================================================================
// LCD UPDATE
// ============================================================================
void updateLCD() {

  static unsigned long lastUpdate = 0;

  if (millis() - lastUpdate < 1000) {
    return;
  }

  lastUpdate = millis();

  lcd.clear();

  // First line
  lcd.setCursor(0, 0);
  lcd.print("Allergen:");

  lcd.setCursor(9, 0);
  lcd.print(allergenLevel, 1);

  lcd.print("p");

  // Second line
  lcd.setCursor(0, 1);

  lcd.print("T:");
  lcd.print(temperature, 0);
  lcd.print("C ");

  if (allergenLevel < 100.0) {
    
    lcd.print("SAFE");

  } else if (allergenLevel < 150.0) {
    digitalWrite(BUZZER, LOW);
    lcd.print("WARN");

  } else {

    lcd.print("UNSAFE");
    digitalWrite(BUZZER, HIGH);
  }
}

// ============================================================================
// LED STATUS
// ============================================================================
void updateLEDs() {

  if (allergenLevel < 100.0) {

    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);

  } else if (allergenLevel < 150.0) {

    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, HIGH);

  } else {

    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
  }
}

// ============================================================================
// THINGSPEAK UPLOAD
// ============================================================================
void sendToThingSpeak() {

  if (WiFi.status() != WL_CONNECTED) {

    Serial.println("WiFi not connected - skipping upload");

    return;
  }

  if (!client.connect(server, 80)) {

    Serial.println("Connection to ThingSpeak failed");

    return;
  }

  String url = "/update?api_key=";

  url += apiKey;

  url += "&field1=" + String(allergenLevel, 2);
  url += "&field2=" + String(temperature, 2);
  url += "&field3=" + String(riskScore, 2);
  url += "&field4=" + String(isSafe ? 1 : 0);
  url += "&field5=" + String(humidity, 2);
  url += "&field6=" + String(riskScore, 2);
  url += "&field7=" + String(allergenLevel, 2);
  url += "&field8=" + String(historyIndex);

  client.print("GET ");
  client.print(url);
  client.println(" HTTP/1.1");

  client.print("Host: ");
  client.println(server);

  client.println("Connection: close");
  client.println();

  unsigned long timeout = millis();

  while (client.available() == 0) {

    if (millis() - timeout > 5000) {

      Serial.println("ThingSpeak timeout");

      client.stop();

      return;
    }
  }

  Serial.print("ThingSpeak response: ");

  while (client.available()) {

    String line = client.readStringUntil('\n');

    if (line.length() > 0 &&
        line[0] != '<' &&
        !line.startsWith("HTTP")) {

      Serial.println(line);
    }
  }

  Serial.println();

  client.stop();

  Serial.print("Uploaded: Allergen=");
  Serial.print(allergenLevel, 1);

  Serial.print("ppm Temp=");
  Serial.print(temperature, 1);

  Serial.print("C Humidity=");
  Serial.print(humidity, 1);

  Serial.println("%");
}

// ============================================================================
// PROOF VERIFICATION
// ============================================================================
void requestProof() {

  proofCount++;

  Serial.println();
  Serial.println("====================================");
  Serial.println("PROOF VERIFICATION");
  Serial.println("====================================");

  Serial.print("Temperature (DHT11): ");
  Serial.print(temperature, 1);
  Serial.println(" C");

  Serial.print("Humidity (DHT11): ");
  Serial.print(humidity, 1);
  Serial.println(" %");

  Serial.print("Allergen Level: ");
  Serial.print(allergenLevel, 2);
  Serial.println(" ppm");

  Serial.print("Risk Score: ");
  Serial.println(riskScore, 2);

  Serial.print("Verdict: ");
  Serial.println(isSafe ? "SAFE" : "UNSAFE");

  Serial.println("====================================");
  Serial.println();

  lcd.clear();

  lcd.setCursor(0, 0);

  if (isSafe) {

    lcd.print("PROOF: SAFE");

    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(RED_LED, LOW);

  }
  else {

    lcd.print("PROOF: UNSAFE");

    digitalWrite(GREEN_LED, LOW);
    digitalWrite(RED_LED, HIGH);
    digitalWrite(BUZZER, HIGH);
  }

  lcd.setCursor(0, 1);

  lcd.print("Risk:");
  lcd.print(riskScore, 1);

  // Upload proof data
  sendToThingSpeak();

  delay(3000);
}