#ifndef Hardware_h
#define Hardware_h

#include <Arduino.h>
#include <eurorack_sd.h>

#define MEMPOOL_SIZE 48*1024

class Hardware {
    public:
        static Hardware hw;
        void init();

        // Memory pool
        static char memPoolBuffer[MEMPOOL_SIZE];
        MemPool<char> memPool = MemPool<char>(Hardware::memPoolBuffer, MEMPOOL_SIZE);

        // SD Card
        FileSystem fs = FileSystem("/ml");

};

#endif