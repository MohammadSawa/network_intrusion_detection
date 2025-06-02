import os
import sys
import subprocess
import pandas as pd
import joblib
import warnings
from main_pipeline import MainPipeline
from data_cleaning_pipeline import DataCleaningPipeline


PYTHON_EXECUTABLE = sys.executable


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

model_pickle_name = 'rf_pipeline_without_smote.pkl'


def check_files_exist():
	
	required_files = [
		"data_cleaning_pipeline.py",
		"main_pipeline.py", 
		"create_cleaning_pipeline.py",
		"create_main_pipeline.py",
		model_pickle_name
	]

	missing_files = []

	for file in required_files:
		file_path = os.path.join(SCRIPT_DIR, file)
		if not os.path.exists(file_path):
			missing_files.append(file)

	if missing_files:
		print(f"Error: The following required files are missing: {', '.join(missing_files)}")
		raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

	print("All required files present. Proceeding...")


def run_scripts():
	
	
	original_dir = os.getcwd()
	os.chdir(SCRIPT_DIR)
	
	try:
		
		try:
			print("Running create_cleaning_pipeline.py...")
			subprocess.run([PYTHON_EXECUTABLE, "create_cleaning_pipeline.py"], check=True)
			print("Successfully created cleaning pipeline pickle.")
		except subprocess.CalledProcessError as e:
			print("Error: Failed to run create_cleaning_pipeline.py")
			raise e

		
		try:
			print("Running create_main_pipeline.py...")
			subprocess.run([PYTHON_EXECUTABLE, "create_main_pipeline.py"], check=True)
			print("Successfully created main pipeline pickle.")
		except subprocess.CalledProcessError as e:
			print("Error: Failed to run create_main_pipeline.py")
			raise e

		print("All scripts executed successfully.")
	finally:
		
		os.chdir(original_dir)


def get_pipeline():

	pipeline_path = os.path.join(SCRIPT_DIR, "main_pipeline.pkl")
	
	
	if not os.path.exists(pipeline_path):
		print("Pipeline not found, creating it...")
		check_files_exist()
		run_scripts()
	
	
	if os.path.exists(pipeline_path):
		print("Loading existing pipeline...")
		main_pipeline = joblib.load(pipeline_path)
		print(f"Pipeline loaded, type: {type(main_pipeline)}")
		
		
		if not isinstance(main_pipeline, MainPipeline):
			raise TypeError("Loaded pipeline is not of type MainPipeline")
		
		if not hasattr(main_pipeline, 'transform_and_predict'):
			raise AttributeError("Loaded pipeline doesn't have transform_and_predict method")
		
		return main_pipeline
	else:
		raise FileNotFoundError("Failed to create pipeline")


def process_file(file_path):
	pipeline_path = os.path.join(SCRIPT_DIR, "main_pipeline.pkl")
	
	if not os.path.exists(pipeline_path):
		print("Pipeline not found, creating it...")
		check_files_exist()
		run_scripts()
	
	print(f"Loading pipeline and processing file: {file_path}")
	main_pipeline = joblib.load(pipeline_path)
	data = pd.read_csv(file_path)
	print(f"CSV loaded with shape: {data.shape}")
	predictions = main_pipeline.transform_and_predict(data)
	print(f"Generated {len(predictions)} predictions")
	return predictions

if __name__ == "__main__":
	
	if len(sys.argv) > 1:
		file_path = sys.argv[1]
		if not os.path.exists(file_path):
			print(f"Error: File {file_path} not found")
			sys.exit(1)
		predictions = process_file(file_path)
		print(predictions)
	else:
		print("Usage: python pipeline_manager.py <csv_file>")
		sys.exit(1)


