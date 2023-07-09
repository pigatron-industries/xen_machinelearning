import tensorflow as tf
import os
from tflite_support import metadata as _metadata
from tflite_support import metadata_schema_py_generated as _metadata_fb
from tflite_support import flatbuffers


class ModelMetadata:
    def __init__(self, type = "", metabytes = []):
        self.metabytes = metabytes
        self.type = "xen:" + type
    def getBytes(self):
        return self.type + bytearray(self.metabytes).decode('iso-8859-1')


class AbstractModel:
    def __init__(self, path = None, name = None):
        self.path = path
        self.name = name


    def saveModelH5(self, model, name):
        tf.keras.saving.save_model(model, f"{self.path}/{name}.h5", save_format="h5")


    def saveModelTfLite(self, model, name, quantize = None, metadata = None):
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        if(quantize == "float16"):
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
        elif(quantize == "int8"):
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            # converter.representative_dataset = representative_data_gen TODO
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.uint8
            converter.inference_output_type = tf.uint8

        tflite_model = converter.convert()
        open(f"{self.path}/{name}.tflite", "wb").write(tflite_model)
        basic_model_size = os.path.getsize(f"{self.path}/{name}.tflite")
        print("Model is %d bytes" % basic_model_size)

        if(metadata != None):
            model_meta = _metadata_fb.ModelMetadataT()
            model_meta.name = name
            model_meta.description = metadata.getBytes()
            b = flatbuffers.Builder(0)
            b.Finish(model_meta.Pack(b), _metadata.MetadataPopulator.METADATA_FILE_IDENTIFIER)
            metadata_buf = b.Output()
            populator = _metadata.MetadataPopulator.with_model_file(f"{self.path}/{name}.tflite")
            populator.load_metadata_buffer(metadata_buf)
            populator.populate()


    def loadModel(self, name) -> tf.keras.Model:
        return tf.keras.saving.load_model(f"{self.path}/{name}.h5", compile=False)