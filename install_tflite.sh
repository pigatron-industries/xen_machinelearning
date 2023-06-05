#!/bin/bash
# https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/docs/new_platform_support.md

if [ -d "tmp/tflite-micro" ]; then
    cd tmp/tflite-micro
    git pull
else
    mkdir -p tmp
    cd tmp
    git clone https://github.com/tensorflow/tflite-micro.git
    cd tflite-micro
fi

rm -rf tflm-tree
python tensorflow/lite/micro/tools/project_generation/create_tflm_tree.py -e hello_world ../tflm-tree

cd ../..
rm -rf src/tflite
mkdir -p src/tflite
cp -r ./tmp/tflm-tree/tensorflow ./src/tflite/tensorflow
cp -r ./tmp/tflm-tree/third_party ./src/tflite/third_party
