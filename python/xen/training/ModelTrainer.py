import yaml


class ModelTrainer:
    def __init__(self, modelName, modelPath="../models"):
        self.modelName = modelName
        self.modelPath = modelPath
        self.trainingInfo = []
        self.datasetInfo = {}
        self.modelInfo = {}
        
    def setDataset(self, dataset):
        self.dataset = dataset

    def addTrainingInfo(self, batchSize, epochs, learningRate, minLearningRate, factor, patience, history):
        traininginfo = {}
        traininginfo['batchSize'] = batchSize
        traininginfo['epochs'] = epochs
        traininginfo['learningRate'] = learningRate
        traininginfo['minLearningRate'] = minLearningRate
        traininginfo['factor'] = factor
        traininginfo['patience'] = patience
        traininginfo['loss'] = history['loss'][-1]
        self.trainingInfo.append(traininginfo)

    def saveModelInfo(self, metadata=None):
        info = {}
        info['name'] = self.modelName
        info['training'] = self.trainingInfo
        info['dataset'] = self.datasetInfo
        info['model'] = self.modelInfo
        if metadata is not None:
            info['metadata'] = vars(metadata)
        with open(f'{self.modelPath}/{self.modelName}.yml', 'w') as outfile:
            yaml.dump(info, outfile)
    