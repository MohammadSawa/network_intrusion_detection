class MainPipeline:
    """Takes raw DF --> returns predictions (df/series)"""
    def __init__(self, cleaning_pipeline, model_pipeline):
        self.cleaning_pipeline = cleaning_pipeline
        self.model_pipeline = model_pipeline

    def transform_and_predict(self, data):
        # Clean the data using the cleaning pipeline
        cleaned_data = self.cleaning_pipeline.transform(data)
        # Predict using the model pipeline
        predictions = self.model_pipeline.predict(cleaned_data)
        return predictions
