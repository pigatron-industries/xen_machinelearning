

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.dataset = None

    def setModel(self, model):
        self.model = model

    def setDataset(self, dataset):
        self.dataset = dataset