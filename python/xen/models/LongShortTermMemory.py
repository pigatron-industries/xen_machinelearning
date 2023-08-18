from .AbstractModel import AbstractModel
from tensorflow.python.framework.ops import disable_eager_execution
from tensorflow.keras.layers import Input, Dense, Layer, Lambda
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.optimizers.legacy import Adam
from tensorflow.keras import backend as K
from tensorflow.keras import metrics
from tensorflow.keras.utils import custom_object_scope
import tensorflow as tf
import os



class LongShortTermMemory(AbstractModel):

    lstm_suffix = "lstm"

    def __init__(self, path, name):
        super().__init__(path, name)
        disable_eager_execution()
            

    @classmethod
    def from_pretrained(cls, path, name):
        model = cls(path = path, name = name)
        model.load()
        return model


    @classmethod
    def from_new(cls, inputShape, lstmDim, path, name):
        model = cls(path = path, name = name)
        model.create(inputShape, lstmDim)
        return model


    def create(self, inputShape, lstmDim = 128):
        self.inputShape = inputShape
        self.inputLayer = tf.keras.Input(inputShape)
        self.lstmLayer = tf.keras.layers.LSTM(128)(self.inputLayer)
        self.outputLayer = tf.keras.layers.Dense(lstmDim)(self.lstmLayer)
        pass

    

    # def compile(self, optimizer=Adam(learning_rate=0.01)):
    #     self.vaeModel.compile(optimizer=optimizer, loss=self.vaeLoss)


    def train(self, traindata, epochs, batchSize = 32):
        self.lstmModel.fit(traindata, traindata, epochs = epochs, batch_size=batchSize)


    def predict(self, inputdata):
        return self.lstmModel.predict(inputdata)
    

    def save(self, quantize = None, metadata = None):
        modelName = f"{self.name}_{self.lstm_suffix}"
        self.saveModelH5(self.lstmModel, modelName)
        self.saveModelTfLite(self.lstmModel, modelName, quantize, metadata)


    def load(self):
        modelName = f"{self.name}_{self.lstm_suffix}"
        self.model = self.loadModel(modelName)
