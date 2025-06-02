import pandas as pd
import joblib
import subprocess
import os
import warnings
import numpy as np


warnings.filterwarnings('ignore')


import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main_pipeline import MainPipeline
from app.data_cleaning_pipeline import DataCleaningPipeline


PYTHON_EXECUTABLE = sys.executable

model_pickle_name = 'rf_pipeline_without_smote.pkl'


def check_files_exist():
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    required_files = [
        os.path.join(app_dir, "data_cleaning_pipeline.py"),
        os.path.join(app_dir, "main_pipeline.py"),
        os.path.join(app_dir, "create_cleaning_pipeline.py"),
        os.path.join(app_dir, "create_main_pipeline.py"),
        os.path.join(app_dir, model_pickle_name)
    ]

    missing_files = []

    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    if missing_files:
        print(f"Error: The following required files are missing: {', '.join(missing_files)}")
        sys.exit(1)

    print("All required files present. Proceeding...")


def run_scripts():
    
    original_dir = os.getcwd()
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
    os.chdir(app_dir)
    
    
    try:
        print("Running create_cleaning_pipeline.py...")
        subprocess.run([PYTHON_EXECUTABLE, "create_cleaning_pipeline.py"], check=True)
        print("Successfully created cleaning pipeline pickle.")
    except subprocess.CalledProcessError:
        print("Error: Failed to run create_cleaning_pipeline.py")
        sys.exit(1)

    
    try:
        print("Running create_main_pipeline.py...")
        subprocess.run([PYTHON_EXECUTABLE, "create_main_pipeline.py"], check=True)
        print("Successfully created main pipeline pickle.")
    except subprocess.CalledProcessError:
        print("Error: Failed to run create_main_pipeline.py")
        sys.exit(1)
        
    
    os.chdir(original_dir)
    print("All scripts executed successfully.")


def get_pipeline():

    try:
        
        pipeline_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "main_pipeline.pkl")
        if not os.path.exists(pipeline_path):
            print("Pipeline not found, creating it...")
            try:
                check_files_exist()
                run_scripts()
            except Exception as e:
                print(f"Error creating pipeline with scripts: {str(e)}")
                print("Creating a mock pipeline as fallback...")
                return create_mock_pipeline()
        if os.path.exists(pipeline_path):
            try:
                print("Loading existing pipeline...")
                main_pipeline = joblib.load(pipeline_path)
                print(f"Pipeline loaded, type: {type(main_pipeline)}")
                
                
                if not isinstance(main_pipeline, MainPipeline):
                    print("Loaded pipeline is not of type MainPipeline")
                    return create_mock_pipeline()
                
                if not hasattr(main_pipeline, 'transform_and_predict'):
                    print("Loaded pipeline doesn't have transform_and_predict method")
                    return create_mock_pipeline()
                
                return main_pipeline
            except Exception as e:
                print(f"Error loading pipeline: {str(e)}")
                print("Creating a mock pipeline as fallback...")
                return create_mock_pipeline()
        else:
            print("Failed to create pipeline")
            return create_mock_pipeline()
    except Exception as e:
        print(f"Error in get_pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return create_mock_pipeline()
def create_mock_pipeline():

    print("Creating mock pipeline...")
    
    class MockModelPipeline:
        def predict(self, data):
            import numpy as np
            return np.zeros(len(data), dtype=int)
        
        def predict_proba(self, data):
            import numpy as np
            return np.array([[0.9, 0.1] for _ in range(len(data))])
    
    cleaning_pipeline = DataCleaningPipeline()
    model_pipeline = MockModelPipeline()
    main_pipeline = MainPipeline(cleaning_pipeline, model_pipeline)
    print("Mock pipeline created successfully")
    return main_pipeline

def process_file(file_path):
    try:
        
        pipeline_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "main_pipeline.pkl")
        if not os.path.exists(pipeline_path):
            print(f"Pipeline not found at {pipeline_path}, creating it...")
            check_files_exist()
            run_scripts()

        print(f"Loading pipeline from {pipeline_path}")
        main_pipeline = joblib.load(pipeline_path)
        
        
        print(f"Reading CSV file from {file_path}")
        try:
            data = pd.read_csv(file_path)
            print(f"CSV loaded with shape: {data.shape}")
            
            label_columns = [col for col in data.columns if 'label' in col.lower()]
            for col in label_columns:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    print(f"Converting non-numeric label column '{col}' to numeric")
                    
                    
                    data[col] = data[col].apply(lambda x: 0 if not isinstance(x, (int, float)) else x)

            print("Running predictions through the pipeline")
            predictions = main_pipeline.transform_and_predict(data)
            print(f"Generated {len(predictions)} predictions")
            return predictions
            
        except pd.errors.ParserError as e:
            print(f"Error parsing CSV file: {str(e)}")
            
            import numpy as np
            return np.array([])
            
        except Exception as e:
            print(f"Error processing CSV data: {str(e)}")
            import traceback
            traceback.print_exc()
            
            import numpy as np
            return np.array([])
            
    except Exception as e:
        print(f"Error in process_file: {str(e)}")
        import traceback
        traceback.print_exc()
        
        import numpy as np
        return np.array([])

def create_pipelines():
    try:
        
        original_dir = os.getcwd()
        app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
        os.chdir(app_dir)
        
        print(f"Running create_cleaning_pipeline.py...")
        result1 = subprocess.run([PYTHON_EXECUTABLE, 'create_cleaning_pipeline.py'], capture_output=True, text=True)
        
        if result1.returncode != 0:
            print(f"Error running create_cleaning_pipeline.py: {result1.stderr}")
            return False
        else:
            print("create_cleaning_pipeline.py completed successfully")
        
        
        print(f"Running create_main_pipeline.py...")
        result2 = subprocess.run([PYTHON_EXECUTABLE, 'create_main_pipeline.py'], capture_output=True, text=True)
        
        if result2.returncode != 0:
            print(f"Error running create_main_pipeline.py: {result2.stderr}")
            return False
        else:
            print("create_main_pipeline.py completed successfully")
        
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"Error creating pipelines: {e}")
        return False

def predict(file_path):

    try:
        
        app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
        pipeline_path = os.path.join(app_dir, "main_pipeline.pkl")
        if not os.path.exists(pipeline_path):
            print("Pipeline not found, creating it...")
            if not create_pipelines():
                print("Failed to create pipelines")
                return np.array([])
        
        
        print(f"Loading pipeline from {pipeline_path}")
        main_pipeline = joblib.load(pipeline_path)
        
        
        print(f"Reading CSV file from {file_path}")
        try:
            data = pd.read_csv(file_path)
            print(f"CSV loaded with shape: {data.shape}")
            
            label_columns = [col for col in data.columns if 'label' in col.lower()]
            for col in label_columns:
                if not pd.api.types.is_numeric_dtype(data[col]):
                    print(f"Converting non-numeric label column '{col}' to numeric")
                    data[col] = data[col].apply(lambda x: 0 if not isinstance(x, (int, float)) else x)
            print("Running predictions through the pipeline")
            predictions = main_pipeline.transform_and_predict(data)
            print(f"Generated {len(predictions)} predictions")
            return predictions
            
        except pd.errors.ParserError as e:
            print(f"Error parsing CSV file: {str(e)}")
            
            import numpy as np
            return np.array([])
            
        except Exception as e:
            print(f"Error processing CSV data: {str(e)}")
            import traceback
            traceback.print_exc()
            
            import numpy as np
            return np.array([])
            
    except Exception as e:
        print(f"Error in predict: {str(e)}")
        import traceback
        traceback.print_exc()
        
        import numpy as np
        return np.array([])

def main_process_file(file_path):
    try:
        app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app")
        pipeline_path = os.path.join(app_dir, "main_pipeline.pkl")
        if not os.path.exists(pipeline_path):
            print(f"Pipeline not found at {pipeline_path}, creating it...")
            if not create_pipelines():
                print("Failed to create pipelines")
                return np.array([])
        
        
        return predict(file_path)
        
    except Exception as e:
        print(f"Error in main_process_file: {e}")
        import traceback
        traceback.print_exc()
        return np.array([])

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} not found")
            sys.exit(1)
        predictions = main_process_file(file_path)
        print(predictions)
    else:
        print("Usage: python use_mainpipeline.py <csv_file>")
        sys.exit(1) 