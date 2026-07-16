int bigbluebutton = D10;
int ledpin = D4;

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64   // use 32 if your display is the 128x32 variant
#define OLED_RESET -1      // no reset pin used
#define SCREEN_ADDRESS 0x3C  // common address; try 0x3D if this doesn't work

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#include <Adafruit_NeoPixel.h>

#define LED_PIN    ledpin
#define LED_COUNT  10

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

#include <random>

int randomlight = rand() % 5;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200); //set up serial
  //setup serial for UART
  Serial1.begin(115200);

  //set up inputs
  pinMode(bigbluebutton, INPUT);

  Serial.begin(9600);

  //screen shenanigans
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("SSD1306 no worky bruh");
    while (1); // halt
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("hello neighbor"); //print to the display with this function
  display.display();



  //led stuff
  strip.begin();
  strip.setBrightness(50); // 0-255, keep it modest to start
  strip.show(); // initialize all off

  // fill with a color to test
  for (int i = 0; i < LED_COUNT; i++) {
    strip.setPixelColor(i, strip.Color(13, 203, 255)); // im blue da boo dee da boo die
  }
  strip.show();


}

void loop() {
  // put your main code here, to run repeatedly:
  // send signal to blahaj
  /*
  if (randomlight = 1) {
      Serial1.println("LIGHTON+LEFT");
      Serial.println("ping!");
    } else if (randomlight = 2) {
      Serial1.println("LIGHTON+RIGHT");
      Serial.println("ping!");
    } else if (randomlight = 3) {
      Serial1.println("LIGHTON+UP");
      Serial.println("ping!");
    }else if (randomlight = 4) {
      Serial1.println("LIGHTON+DOWN");
      Serial.println("ping!");
    }

  //wait until a signal is given
  if (Serial1.available()) {
    String message = Serial1.readStringUntil('\n');
    message.trim();
    Serial.print("Received: ");
    Serial.println(message);

    //send signal to
    if (message == "LEFT") { //player hit the left button
      // trigger whatever you want here — NeoPixels, OLED, etc.
      Serial.println("they hit left AHHHHH");
    }
  }
  */

  //make random light to start
  Serial1.println("LIGHTON+LEFT"); //pong
  Serial.println("17 38. ay wasup hello");

  delay(5000);
}