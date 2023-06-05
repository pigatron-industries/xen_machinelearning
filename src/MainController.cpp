#include "MainController.h"
#include "Hardware.h"

#include <Arduino.h>
#include <SPI.h>
#include <math.h>

MainController* MainController::mainController = nullptr;

MainController::MainController(float sampleRate) {
    MainController::mainController = this;
}

void MainController::init() {
    Hardware::hw.init();

}

void MainController::update() {

}
