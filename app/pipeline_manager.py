import os
import sys
import subprocess
import pandas as pd
import joblib
import warnings
from main_pipeline import MainPipeline
from data_cleaning_pipeline import DataCleaningPipeline

# Get the path to the Python interpreter in the current virtual environment
PYTHON_EXECUTABLE = sys.executable

# Get the directory where this script is located (app directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

model_pickle_name = 'rf_pipeline_without_smote.pkl'


def check_files_exist():
	"""Check if all required files exist in the app directory"""
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
	"""Run the pipeline creation scripts"""
	# Change to the script directory
	original_dir = os.getcwd()
	os.chdir(SCRIPT_DIR)
	
	try:
		# Run the first script
		try:
			print("Running create_cleaning_pipeline.py...")
			subprocess.run([PYTHON_EXECUTABLE, "create_cleaning_pipeline.py"], check=True)
			print("Successfully created cleaning pipeline pickle.")
		except subprocess.CalledProcessError as e:
			print("Error: Failed to run create_cleaning_pipeline.py")
			raise e

		# Run the second script
		try:
			print("Running create_main_pipeline.py...")
			subprocess.run([PYTHON_EXECUTABLE, "create_main_pipeline.py"], check=True)
			print("Successfully created main pipeline pickle.")
		except subprocess.CalledProcessError as e:
			print("Error: Failed to run create_main_pipeline.py")
			raise e

		print("All scripts executed successfully.")
	finally:
		# Change back to original directory
		os.chdir(original_dir)


def get_pipeline():
	"""Get the main pipeline, creating it if necessary.
	This function is used by the API to get the pipeline.
	
	Returns:
		MainPipeline: The loaded or created pipeline.
	"""
	pipeline_path = os.path.join(SCRIPT_DIR, "main_pipeline.pkl")
	
	# Check if the pipeline exists
	if not os.path.exists(pipeline_path):
		print("Pipeline not found, creating it...")
		check_files_exist()
		run_scripts()
	
	# Load the pipeline
	if os.path.exists(pipeline_path):
		print("Loading existing pipeline...")
		main_pipeline = joblib.load(pipeline_path)
		print(f"Pipeline loaded, type: {type(main_pipeline)}")
		
		# Verify it's the right type and has the required methods
		if not isinstance(main_pipeline, MainPipeline):
			raise TypeError("Loaded pipeline is not of type MainPipeline")
		
		if not hasattr(main_pipeline, 'transform_and_predict'):
			raise AttributeError("Loaded pipeline doesn't have transform_and_predict method")
		
		return main_pipeline
	else:
		raise FileNotFoundError("Failed to create pipeline")


def process_file(file_path):
	"""Process a CSV file and return predictions.
	
	Args:
		file_path: Path to the CSV file to process
		
	Returns:
		numpy.ndarray: Array of predictions
	"""
	pipeline_path = os.path.join(SCRIPT_DIR, "main_pipeline.pkl")
	
	# Make sure we have a pipeline
	if not os.path.exists(pipeline_path):
		print("Pipeline not found, creating it...")
		check_files_exist()
		run_scripts()
	
	# Load the pipeline and process data
	print(f"Loading pipeline and processing file: {file_path}")
	main_pipeline = joblib.load(pipeline_path)
	data = pd.read_csv(file_path)
	print(f"CSV loaded with shape: {data.shape}")
	predictions = main_pipeline.transform_and_predict(data)
	print(f"Generated {len(predictions)} predictions")
	return predictions

if __name__ == "__main__":
	# If run as a script, process the file specified as an argument
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


