import tensorflow as tf
import os


class AbstractModel:
    def __init__(self, path = None, name = None):
        self.path = path
        self.name = name


    def saveModel(self, model, name, format='h5'):
        if format == 'h5':
            tf.keras.saving.save_model(model, f"{self.path}/{name}.h5", save_format="h5")
        elif format == 'tflite':
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            tflite_model = converter.convert()
            open(f"{self.path}/{name}.tflite", "wb").write(tflite_model)
            basic_model_size = os.path.getsize(f"{self.path}/{name}.tflite")
            print("Model is %d bytes" % basic_model_size)


    def loadModel(self, name, format='h5'):
        return tf.keras.saving.load_model(f"{self.path}/{name}.h5", compile=False)