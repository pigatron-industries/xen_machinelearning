#include "Hardware.h"

Hardware Hardware::hw = Hardware();

char Hardware::memPoolBuffer[MEMPOOL_SIZE];

void Hardware::init() {
    fs.init();
}
