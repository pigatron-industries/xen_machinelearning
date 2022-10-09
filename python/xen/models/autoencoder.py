import tensorflow as tf

class AutoEncoder:
    def __init__(self, inputDim, latentDim):
        self.inputShape = (inputDim)
        self.latentShape = (latentDim)
        # encoder model
        self.encoderInput = tf.keras.layers.Input(shape = self.inputShape)
        self.encoderOutput = tf.keras.layers.Dense(self.latentShape, activation = 'tanh')(self.encoderInput)
        self.encoder = tf.keras.Model(self.encoderInput, self.encoderOutput)
        # decoder model
        self.decoderInput = tf.keras.layers.Input(shape = self.latentShape)
        self.decoderOutput = tf.keras.layers.Dense(self.inputShape, activation = 'sigmoid')(self.decoderInput)
        self.decoder = tf.keras.Model(self.decoderInput, self.decoderOutput)
        # autoencoder model
        self.autoencoder = tf.keras.Model(self.encoderInput, self.decoder(self.encoderOutput))

    def compile(self, loss = 'binary_crossentropy', optimizer=tf.keras.optimizers.Adam(learning_rate=0.01)):
        self.autoencoder.compile(loss=loss, optimizer=optimizer)

    def train(self, traindata, epochs):
        self.autoencoder.fit(traindata, traindata, epochs = epochs)

    def  predict(self, inputdata):
        return self.autoencoder.predict(inputdata)
