
import os
import zipfile
import shutil
import sys
from pathlib import Path

def create_package(output_path=None):
    
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_dir = os.path.dirname(current_dir)  
    
    
    temp_dir = os.path.join(base_dir, 'temp_package')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    
    app_dir = os.path.join(temp_dir, 'app')
    os.makedirs(app_dir)
    
    
    required_files = [
        'process_csv.py',
        'data_cleaning_pipeline.py',
        'main_pipeline.py',
        'model_pipeline.py',
        'main_pipeline.pkl',
        '__init__.py',
        'create_cleaning_pipeline.py',
        'create_main_pipeline.py',
        'rf_pipeline_without_smote.pkl',
        'create_test_rf_pickle.py',
        'test_pipeline.py'
    ]
    
    
    for file in required_files:
        src_path = os.path.join(current_dir, file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, app_dir)
        else:
            print(f"Warning: Required file '{file}' not found at {src_path}")
    
    
    readme_path = os.path.join(temp_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write("""

This package contains a Python-based system for detecting anomalies in network traffic data.



1. Install dependencies:
   ```
   pip install pandas numpy scikit-learn
   ```

2. Run the monitoring script:
   ```
   python -m app.process_csv "path/to/your/directory"
   ```

3. Place CSV files containing network traffic data in the "csv_output" directory.

4. View results in the "results" directory.



- app/ - Contains the core processing logic
- csv_output/ - Place CSV files to analyze here
- processed/ - Processed files are moved here
- results/ - Analysis results appear here
- logs/ - System logs are stored here



To process files only once without continuous monitoring:
```
python -m app.process_csv "path/to/your/directory" --single
```



This system uses machine learning to identify unusual patterns in network traffic data.
It can help identify potential security threats, performance issues, and other network anomalies.
""")
    
    
    requirements_path = os.path.join(temp_dir, 'requirements.txt')
    with open(requirements_path, 'w') as f:
        f.write("""pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=0.24.0
joblib>=1.0.0
""")
    
    
    batch_path = os.path.join(temp_dir, 'start_monitoring.bat')
    with open(batch_path, 'w') as f:
        f.write("""@echo off
echo Starting Network Anomaly Detection System...
python -m app.process_csv "%~dp0"
pause
""")
    
    
    shell_path = os.path.join(temp_dir, 'start_monitoring.sh')
    with open(shell_path, 'w') as f:
        f.write("""
echo "Starting Network Anomaly Detection System..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
python -m app.process_csv "$DIR"
""")
    
    
    os.chmod(shell_path, 0o755)
    
    
    if not output_path:
        static_dir = os.path.join(current_dir, 'static', 'installers')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        output_path = os.path.join(static_dir, 'network_anomaly_detection.zip')
    
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    
    shutil.rmtree(temp_dir)
    
    print(f"Package created successfully: {output_path}")
    return output_path

if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else None
    create_package(output_path) 