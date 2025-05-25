import joblib
from data_cleaning_pipeline import DataCleaningPipeline
cleaning_pipeline = DataCleaningPipeline()
joblib.dump(cleaning_pipeline, 'cleaning_pipeline.pkl')
print("cleaning pipeline pickled successfully!")
