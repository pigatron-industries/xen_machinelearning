#!/bin/bash

if [ -d "tmp/tflite-micro-arduino" ]; then
    cd tmp/tflite-micro-arduino
    git pull
else
    mkdir -p tmp
    cd tmp
    git clone https://github.com/tensorflow/tflite-micro-arduino-examples.git tflite-micro-arduino
    cd tflite-micro
fi

cd ../..

rm -rf lib/tflite-micro
mkdir -p lib/tflite-micro/tensorflow
cp -r ./tmp/tflite-micro/src/tensorflow ./lib/tflite-micro/tensorflow
cp -r ./tmp/tflite-micro/src/peripherals ./lib/tflite-micro/peripherals
cp -r ./tmp/tflite-micro/src/third_party ./lib/tflite-micro/third_party
