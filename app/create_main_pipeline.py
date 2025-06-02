import pandas as pd
import joblib
from data_cleaning_pipeline import DataCleaningPipeline
from main_pipeline import MainPipeline

cleaning_pipeline = joblib.load('cleaning_pipeline.pkl')
model_pipeline = joblib.load("rf_pipeline_without_smote.pkl")


main_pipeline = MainPipeline(cleaning_pipeline, model_pipeline)
joblib.dump(main_pipeline, 'main_pipeline.pkl')
print("Main pipeline pickled successfully!")

