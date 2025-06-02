class MainPipeline:
    def __init__(self, cleaning_pipeline, model_pipeline):
        self.cleaning_pipeline = cleaning_pipeline
        self.model_pipeline = model_pipeline

    def transform_and_predict(self, data):
        
        cleaned_data = self.cleaning_pipeline.transform(data)
        
        predictions = self.model_pipeline.predict(cleaned_data)
        return predictions
