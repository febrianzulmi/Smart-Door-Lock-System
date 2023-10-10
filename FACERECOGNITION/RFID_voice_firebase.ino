#include <ESP8266WiFi.h>
#include <FirebaseESP8266.h>
#include <SPI.h>
#include <MFRC522.h>
#include "VoiceRecognitionV3.h"  // Sertakan library untuk Voice Recognition V3
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

// Wi-Fi Settings
const char* ssid = "Epel";
const char* password = "00000001";

// Firebase Settings
#define FIREBASE_HOST "https://faceattendacerealtime-45f98-default-rtdb.firebaseio.com/"
#define FIREBASE_AUTH "WhMAVXjWTNQHGO21S7DUlHzUqWP1y77R7yDEDgSS"

FirebaseData firebaseData;

#define RELAY_PIN D3


MFRC522 mfrc522(D0, A0);  // Pin SDA_PIN dan RST_PIN untuk MFRC522

struct CardData {
  String cardUID;
  String databasePath;
  String nama;
};

CardData cardDataArray[] = {
  { "80D21950", "/Students/1306620032", "Febrian" },
  { "53A8B91D", "/Students/1306620081", "Rofid" },
  { "BAF0DA8A", "/Students/1306620014", "Nugraha" },
  { "E2834A19", "/Students/130662002", "Elon Musk" },
  { "6A266C80", "/Students/321654", "Oppenheimer" },
  // Tambahkan data kartu lain jika diperlukan.
};

bool relayActive = false;
bool relayManuallyOn = false;
unsigned long relayOnTime = 0;
const unsigned long relayDuration = 2000;  // 2 detik

unsigned long previousMillis = 0;
const long interval = 5000;  // Interval antara pergantian tampilan (dalam milisecond)

int screenState = 0;  // Posisi tampilan saat ini

VR myVR(D8, D4);  // RX pin = D5, TX pin = D6 untuk Wemos D1 Mini
uint8_t records[7];
uint8_t buf[64];
#define onRecord (0)
#define offRecord (1)

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  digitalWrite(RELAY_PIN, HIGH);
  Serial.println(ssid);
  lcd.setCursor(0, 0);
  lcd.print("Connecting to ");



  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    lcd.setCursor(0, 1);
    lcd.print(ssid);
    lcd.print(" . ");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  digitalWrite(RELAY_PIN, LOW);
  lcd.setCursor(0, 0);
  lcd.print("WiFi connected");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());
}

void setupFirebase() {
  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);
}

void printVR(uint8_t* buf) {
  Serial.println("VR Index\tGroup\tRecordNum\tSignature");
  for (int i = 0; i < 7; i++) {
    Serial.print(buf[i], HEX);
    Serial.print("\t");
  }
  Serial.println();
}

String getCardUID() {
  String cardUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    cardUID += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
    cardUID += String(mfrc522.uid.uidByte[i], HEX);
  }
  cardUID.toUpperCase();
  return cardUID;
}

void turnOnRelay() {
  if (!relayActive) {
    digitalWrite(RELAY_PIN, HIGH);

    relayActive = true;
    relayOnTime = millis();
    Firebase.setString(firebaseData, "/RelayStatus", "ON");
    Firebase.setString(firebaseData, "/Students/1306620032/RelayControl", "ON");
    Firebase.setString(firebaseData, "/Students/1306620081/RelayControl", "ON");
    Firebase.setString(firebaseData, "/Students/1306620014/RelayControl", "ON");
    Firebase.setString(firebaseData, "/Students/130662002/RelayControl", "ON");
    Firebase.setString(firebaseData, "/Students/321654/RelayControl", "ON");
  }
}

void turnOffRelay() {
  if (relayActive) {
    digitalWrite(RELAY_PIN, LOW);

    relayActive = false;
    Firebase.setString(firebaseData, "/RelayStatus", "OFF");
    Firebase.setString(firebaseData, "/Students/1306620032/RelayControl", "OFF");
    Firebase.setString(firebaseData, "/Students/1306620081/RelayControl", "Off");
    Firebase.setString(firebaseData, "/Students/1306620014/RelayControl", "OFF");
    Firebase.setString(firebaseData, "/Students/130662002/RelayControl", "OFF");
    Firebase.setString(firebaseData, "/Students/321654/RelayControl", "OFF");
  }
}


void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  lcd.init();
  lcd.backlight();

  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  setupWiFi();
  setupFirebase();

  myVR.begin(9600);
  Serial.println("Elechouse Voice Recognition V3 Module\r\nControl LED sample");

  if (myVR.clear() == 0) {
    Serial.println("Recognizer cleared.");
  } else {
    Serial.println("Not find VoiceRecognitionModule.");
    Serial.println("Please check connection and restart Arduino.");
    while (1)
      ;
  }

  if (myVR.load((uint8_t)onRecord) >= 0) {
    Serial.println("onRecord loaded");
  }

  if (myVR.load((uint8_t)offRecord) >= 0) {
    Serial.println("offRecord loaded");
  }
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval) {
    // Simpan waktu terakhir tampilan diperbarui
    previousMillis = currentMillis;

    // Pergantian tampilan sesuai posisi saat ini
    switch (screenState) {
      case 0:
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Welcome!");
        lcd.setCursor(0, 1);
        lcd.print("System Biometric");
        break;
      case 1:
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("TAP YOUR CARD");
        lcd.setCursor(0, 1);
        lcd.print("SPEAK YOUR VOICE");
        break;
    }

    // Pergantian ke tampilan berikutnya
    screenState = (screenState + 1) % 2;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Resetting ESP...");
    setupWiFi();
  }
  // Check if the relay status is changed manually via Firebase
  if (Firebase.getString(firebaseData, "/Students/1306620032/RelayControl") && firebaseData.dataType() == "string") {
    String relayStatus = firebaseData.stringData();

    // If the relay status is "ON" and not already manually on, turn on the relay
    if (relayStatus == "ON" && !relayManuallyOn) {
      turnOnRelay();
      relayManuallyOn = true;
    }
    // If the relay status is "OFF", turn off the relay
    else if (relayStatus == "OFF") {
      turnOffRelay();
      relayManuallyOn = false;
    }
  }

  if (Firebase.getString(firebaseData, "/Students/1306620081/RelayControl") && firebaseData.dataType() == "string") {
    String relayStatus = firebaseData.stringData();

    // If the relay status is "ON" and not already manually on, turn on the relay
    if (relayStatus == "ON" && !relayManuallyOn) {
      turnOnRelay();
      relayManuallyOn = true;
    }
    // If the relay status is "OFF", turn off the relay
    else if (relayStatus == "OFF") {
      turnOffRelay();
      relayManuallyOn = false;
    }
  }
  if (Firebase.getString(firebaseData, "/Students/1306620014/RelayControl") && firebaseData.dataType() == "string") {
    String relayStatus = firebaseData.stringData();

    // If the relay status is "ON" and not already manually on, turn on the relay
    if (relayStatus == "ON" && !relayManuallyOn) {
      turnOnRelay();
      relayManuallyOn = true;
    }
    // If the relay status is "OFF", turn off the relay
    else if (relayStatus == "OFF") {
      turnOffRelay();
      relayManuallyOn = false;
    }
  }
  if (Firebase.getString(firebaseData, "/Students/130662002/RelayControl") && firebaseData.dataType() == "string") {
    String relayStatus = firebaseData.stringData();

    // If the relay status is "ON" and not already manually on, turn on the relay
    if (relayStatus == "ON" && !relayManuallyOn) {
      turnOnRelay();
      relayManuallyOn = true;
    }
    // If the relay status is "OFF", turn off the relay
    else if (relayStatus == "OFF") {
      turnOffRelay();
      relayManuallyOn = false;
    }
  }
  if (Firebase.getString(firebaseData, "/Students/321654/RelayControl") && firebaseData.dataType() == "string") {
    String relayStatus = firebaseData.stringData();

    // If the relay status is "ON" and not already manually on, turn on the relay
    if (relayStatus == "ON" && !relayManuallyOn) {
      turnOnRelay();
      relayManuallyOn = true;
    }
    // If the relay status is "OFF", turn off the relay
    else if (relayStatus == "OFF") {
      turnOffRelay();
      relayManuallyOn = false;
    }
  }
  // Periksa kartu RFID
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String currentCardUID = getCardUID();
    Serial.println("Detected card UID: " + currentCardUID);

    bool cardMatched = false;
    String databasePath;
    String nama;

    for (int i = 0; i < sizeof(cardDataArray) / sizeof(cardDataArray[0]); i++) {
      if (currentCardUID.equals(cardDataArray[i].cardUID)) {
        cardMatched = true;
        databasePath = cardDataArray[i].databasePath;
        nama = cardDataArray[i].nama;
        break;
      }
    }

    if (cardMatched) {
      turnOnRelay();
      lcd.setCursor(0, 0);
      lcd.print("Access Card");
      lcd.setCursor(0, 1);
      lcd.print("Success: " + nama);
      delay(2000);
      lcd.clear();
    } else {
      lcd.setCursor(0, 0);
      lcd.print("Card Not Detected");
      lcd.setCursor(0, 1);
      lcd.print("Please Register");
      delay(2000);
      lcd.clear();
    }
    mfrc522.PICC_HaltA();
  }


  // Periksa perintah suara yang diterima
  int ret;
  ret = myVR.recognize(buf, 50);
  if (ret > 0) {
    switch (buf[1]) {
      case onRecord:
        /** turn on relay */
        turnOnRelay();
        lcd.setCursor(0, 0);
        lcd.print("Access Voice");
        lcd.setCursor(0, 1);
        lcd.print("Granted ");
        delay(2000);  // Tampilkan informasi selama 2 detik
        lcd.clear();
        break;
      case offRecord:
        /** turn off relay */
        turnOffRelay();
        break;
      default:
        Serial.println("Record function undefined");
        break;
    }
    /** voice recognized */
    printVR(buf);
  }
  // Periksa apakah relay perlu dimatikan setelah waktu tertentu
  if (relayActive && (millis() - relayOnTime >= relayDuration)) {
    turnOffRelay();
  }
}
