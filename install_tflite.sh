#!/bin/bash

if [ -d "tmp/tflite-micro" ]; then
    cd tmp/tflite-micro
    git pull
else
    mkdir -p tmp
    cd tmp
    # git clone https://github.com/tensorflow/tflite-micro.git
    git clone https://github.com/tensorflow/tflite-micro-arduino-examples.git tflite-micro
    cd tflite-micro
fi

cd ../..

rm -rf lib/tflite-micro
mkdir -p lib/tflite-micro/tensorflow
cp -r ./tmp/tflite-micro/src/tensorflow/lite ./lib/tflite-micro/tensorflow/lite
cp -r ./tmp/tflite-micro/src/third_party ./lib/tflite-micro/third_party
