#include <Arduino.h>
#include <eurorack.h>

#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_log.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"

void setup() {
    Serial.begin(115200);
    Serial.println();
    Serial.println("===================================");
    Serial.println("*     Pigatron Industries         *");
    Serial.println("===================================");
    Serial.println();

    // mainController.init();
}

void loop() {
    // mainController.update();
}
