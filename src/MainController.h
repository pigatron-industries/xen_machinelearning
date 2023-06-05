#ifndef MainController_h
#define MainController_h

#include <eurorack.h>
#include <inttypes.h>

#include "Hardware.h"

class MainController {

public:
    MainController(float sampleRate);
    void init();
    void update();

private:
    static MainController* mainController;

};

#endif
