import os
import sys
import time
import json
import shutil
import logging
import requests
import argparse
import getpass
from datetime import datetime
from pathlib import Path


API_BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/login"
PROCESS_ENDPOINT = f"{API_BASE_URL}/api/direct-process"
DEFAULT_CHECK_INTERVAL = 10  
DEFAULT_REQUEST_TIMEOUT = 60  


def get_script_directory():
    
    if getattr(sys, 'frozen', False):
        
        return os.path.dirname(sys.executable)
    else:
        
        return os.path.dirname(os.path.abspath(__file__))

def authenticate_user():
    
    print("="*63)
    print("Network Anomaly Detection Monitor - Authentication".center(63))
    print("="*63)
    print("\nPlease enter your credentials to continue:")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            
            username = input("\nUsername: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
                
            password = getpass.getpass("Password: ")
            if not password:
                print("Password cannot be empty.")
                continue
            
            
            print("\nAuthenticating...")
            auth_data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(
                LOGIN_ENDPOINT,
                json=auth_data,
                timeout=DEFAULT_REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                user_data = response.json()
                api_key = user_data.get('api_key')
                if api_key:
                    print(f"✓ Authentication successful! Welcome, {username}")
                    return api_key
                else:
                    print("✗ Authentication failed: No API key received")
            elif response.status_code == 401:
                print("✗ Authentication failed: Invalid username or password")
            else:
                print(f"✗ Authentication failed: Server error ({response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to the server.")
            return None
        except requests.exceptions.Timeout:
            print("✗ Authentication request timed out.")
        except Exception as e:
            print(f"✗ Authentication error: {str(e)}")
        
        if attempt < max_attempts - 1:
            print(f"\nAttempt {attempt + 1} of {max_attempts} failed. Please try again.")
        else:
            print(f"\nMaximum authentication attempts ({max_attempts}) exceeded.")
    
    return None

def get_workspace_selection(api_key):
    
    print("\n" + "="*63)
    print("Workspace Selection".center(63))
    print("="*63)
    
    try:
        
        print("\nFetching your workspaces...")
        headers = {'X-API-Key': api_key}
        response = requests.get(
            f"{API_BASE_URL}/api/workspaces-for-monitor",
            headers=headers,
            timeout=DEFAULT_REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            print("✗ Failed to fetch workspaces")
            return None, None
        
        workspaces = response.json()
        
        if not workspaces:
            print("✗ No workspaces found. Please create a workspace first.")
            return None, None
        
        
        print("\nAvailable Workspaces:")
        for i, workspace in enumerate(workspaces, 1):
            description = workspace.get('description', 'No description')
            print(f"{i}. {workspace['name']} (ID: {workspace['id']})")
            if description and description != 'No description':
                print(f"   Description: {description}")
        
        
        while True:
            try:
                choice = input(f"\nSelect workspace for monitoring (1-{len(workspaces)}): ").strip()
                if not choice:
                    continue
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(workspaces):
                    selected_workspace = workspaces[choice_num - 1]
                    workspace_id = selected_workspace['id']
                    workspace_name = selected_workspace['name']
                    print(f"✓ Selected: {workspace_name}")
                    return workspace_id, workspace_name
                else:
                    print(f"Please enter a number between 1 and {len(workspaces)}")
            except ValueError:
                print("Please enter a valid number")
                
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to the server to fetch workspaces.")
        return None, None
    except requests.exceptions.Timeout:
        print("✗ Request timed out while fetching workspaces.")
        return None, None
    except Exception as e:
        print(f"✗ Error fetching workspaces: {str(e)}")
        return None, None

def get_monitoring_preferences():
    
    print("\n" + "="*63)
    print("Monitoring Configuration".center(63))
    print("="*63)
    
    
    while True:
        try:
            interval_input = input(f"\nCheck interval in seconds (default: {DEFAULT_CHECK_INTERVAL}): ").strip()
            if not interval_input:
                check_interval = DEFAULT_CHECK_INTERVAL
                break
            else:
                check_interval = int(interval_input)
                if check_interval < 1:
                    print("Check interval must be at least 1 second.")
                    continue
                break
        except ValueError:
            print("Please enter a valid number.")
    
    script_dir = get_script_directory()
    print(f"\nCSV file monitoring directory:")
    print(f"Press Enter to use the same directory as this program: {script_dir}")
    csv_dir_input = input("Or enter a custom path: ").strip()
    
    if not csv_dir_input:
        csv_dir = script_dir
    else:
        csv_dir = os.path.abspath(csv_dir_input)
        
        try:
            os.makedirs(csv_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory {csv_dir}: {str(e)}")
            print(f"Using default directory: {script_dir}")
            csv_dir = script_dir
    
    return check_interval, csv_dir

def save_session_config(api_key, check_interval, csv_dir, workspace_id, workspace_name):
    
    script_dir = get_script_directory()
    
    safe_workspace_name = "".join(c for c in workspace_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_workspace_name = safe_workspace_name.replace(' ', '_').lower()
    session_file = os.path.join(script_dir, f".session_config_{safe_workspace_name}")
    
    config_data = {
        "api_key": api_key,
        "check_interval": check_interval,
        "csv_dir": csv_dir,
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        with open(session_file, 'w') as f:
            json.dump(config_data, f)
        return True
    except Exception as e:
        print(f"Warning: Could not save session config: {str(e)}")
        return False

def load_session_config(workspace_name=None):
    
    script_dir = get_script_directory()
    
    
    if workspace_name:
        safe_workspace_name = "".join(c for c in workspace_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_workspace_name = safe_workspace_name.replace(' ', '_').lower()
        session_file = os.path.join(script_dir, f".session_config_{safe_workspace_name}")
    else:
        
        session_files = [f for f in os.listdir(script_dir) if f.startswith('.session_config')]
        if not session_files:
            return None
        
        session_files.sort(key=lambda x: os.path.getmtime(os.path.join(script_dir, x)), reverse=True)
        session_file = os.path.join(script_dir, session_files[0])
    
    if not os.path.exists(session_file):
        return None
    
    try:
        with open(session_file, 'r') as f:
            config_data = json.load(f)
        
        session_time = datetime.fromisoformat(config_data.get('timestamp', ''))
        time_diff = datetime.now() - session_time
        
        if time_diff.total_seconds() > 86400:  
            os.remove(session_file)
            return None
        
        return config_data
    except Exception:
        
        try:
            os.remove(session_file)
        except:
            pass
        return None

def check_running_instances():
    
    script_dir = get_script_directory()
    session_files = [f for f in os.listdir(script_dir) if f.startswith('.session_config_')]
    
    if session_files:
        print("\n📊 Other Running Monitor Instances:")
        for session_file in session_files:
            try:
                with open(os.path.join(script_dir, session_file), 'r') as f:
                    config = json.load(f)
                workspace_name = config.get('workspace_name', 'Unknown')
                print(f"  • {workspace_name}")
            except:
                continue
        print()

def parse_arguments():
    
    parser = argparse.ArgumentParser(description="Network Anomaly Detection Monitor")
    
    parser.add_argument("--reset-session", action="store_true",
                        help="Reset saved session and re-authenticate")
    parser.add_argument("--interval", type=int,
                        help=f"Override check interval in seconds")
    parser.add_argument("--csv-dir",
                        help="Override CSV directory path")
    
    return parser.parse_args()

def initialize_configuration():
    
    args = parse_arguments()

    
    check_running_instances()
    
    if not args.reset_session:
        session_config = load_session_config()
        if session_config:
            workspace_name = session_config.get('workspace_name', 'Unknown')
            print(f"Found existing session for workspace: {workspace_name}")
            print("Using saved configuration...")
            api_key = session_config['api_key']
            workspace_id = session_config['workspace_id']
            workspace_name = session_config['workspace_name']
            check_interval = args.interval if args.interval else session_config['check_interval']
            csv_dir = args.csv_dir if args.csv_dir else session_config['csv_dir']
            return api_key, check_interval, csv_dir, workspace_id, workspace_name
    
    api_key = authenticate_user()
    if not api_key:
        print("\nAuthentication failed. Cannot continue.")
        print("Please ensure:")
        print("1. Your username and password are correct")
        print("2. You have a valid account")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    workspace_id, workspace_name = get_workspace_selection(api_key)
    if not workspace_id:
        print("\nWorkspace selection failed. Cannot continue.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    
    check_interval, csv_dir = get_monitoring_preferences()
    
    
    if args.interval:
        check_interval = args.interval
    if args.csv_dir:
        csv_dir = os.path.abspath(args.csv_dir)
    
    
    save_session_config(api_key, check_interval, csv_dir, workspace_id, workspace_name)
    
    return api_key, check_interval, csv_dir, workspace_id, workspace_name


API_KEY, CHECK_INTERVAL, CSV_DIR, WORKSPACE_ID, WORKSPACE_NAME = initialize_configuration()


SCRIPT_DIR = get_script_directory()
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "processed")
FAILED_DIR = os.path.join(SCRIPT_DIR, "failed")
LOGS_DIR = os.path.join(SCRIPT_DIR, "logs")


for directory in [CSV_DIR, PROCESSED_DIR, FAILED_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "monitor.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def display_header():
    
    print("\n" + "="*63)
    print("Network Anomaly Detection Monitor - Active".center(63))
    print("="*63)
    print("\nMonitoring service is now running...")
    print(f"\nConfiguration:")
    print(f"- Workspace: {WORKSPACE_NAME} (ID: {WORKSPACE_ID})")
    print(f"- Check Interval: {CHECK_INTERVAL} seconds")
    print(f"- CSV Directory: {CSV_DIR}")
    print("\nInstructions:")
    if CSV_DIR == SCRIPT_DIR:
        print("1. Place CSV files in the same directory as this program to process them.")
    else:
        print(f"1. Place CSV files in the {os.path.basename(CSV_DIR)} directory to process them.")
    print("2. Processed files will be moved to the 'processed' directory.")
    print("3. Failed files will be moved to the 'failed' directory.")
    print("4. Check 'logs/monitor.log' for detailed processing information.")
    print("5. Press Ctrl+C to stop the monitoring service.")
    print("="*63)
    print("\nThe monitor is now running...\n")
    
    logger.info("Network monitor started")
    logger.info(f"Workspace: {WORKSPACE_NAME} (ID: {WORKSPACE_ID})")
    logger.info(f"Check Interval: {CHECK_INTERVAL} seconds")
    logger.info(f"CSV Directory: {CSV_DIR}")

def send_csv_file(file_path):
    
    logger.info(f"Processing file: {file_path}")
    
    try:
        
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")
        
        with open(file_path, 'r') as f:
            csv_content = f.read()

        headers = {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'csv_text': csv_content,
            'workspace_id': WORKSPACE_ID
        }

        response = requests.post(
            PROCESS_ENDPOINT, 
            json=payload, 
            headers=headers, 
            timeout=DEFAULT_REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                if 'predictions' in response_data and len(response_data['predictions']) > 0:
                    pred_counts = {}
                    for pred in response_data['predictions']:
                        if pred in pred_counts:
                            pred_counts[pred] += 1
                        else:
                            pred_counts[pred] = 1
                    logger.info(f"Processing complete. Prediction summary: {pred_counts}")
                else:
                    logger.info("File processed successfully")
                
                
                processed_path = os.path.join(PROCESSED_DIR, os.path.basename(file_path))
                shutil.move(file_path, processed_path)
                logger.info(f"Moved processed file to: {processed_path}")
                
                return True, response_data.get('message', 'Success')
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                return False, f"Error parsing response: {str(e)}"
        else:
            logger.error(f"Failed to send file. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False, f"API error {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out after {DEFAULT_REQUEST_TIMEOUT} seconds")
        return False, f"Request timed out after {DEFAULT_REQUEST_TIMEOUT} seconds"
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return False, f"Request error: {str(e)}"
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return False, f"Error: {str(e)}"

def process_csv_directory():
    
    csv_files = [f for f in os.listdir(CSV_DIR) if f.lower().endswith('.csv')]
    logger.info(f"Found {len(csv_files)} CSV files to process.")
    
    if not csv_files:
        return
    
    
    for csv_file in csv_files:
        csv_path = os.path.join(CSV_DIR, csv_file)
        
        if os.path.exists(os.path.join(PROCESSED_DIR, csv_file)):
            logger.info(f"File already exists in processed directory: {csv_file} (skipping)")
            continue
            
        success, message = send_csv_file(csv_path)
        
        if not success and os.path.exists(csv_path):
            failed_path = os.path.join(FAILED_DIR, csv_file)
            logger.error(f"Failed to process file: {csv_file}")
            logger.error(f"Error: {message}")
            shutil.move(csv_path, failed_path)
            logger.info(f"Moved failed file to: {failed_path}")

def main():
    
    display_header()
    
    try:
        while True:
            logger.info("Checking for CSV files...")
            process_csv_directory()
            
            
            print(f"Waiting {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\nError: {str(e)}")
    
    print("\nThe monitoring service has stopped.")
    print("\nPress Enter to exit...")
    input()

if __name__ == "__main__":
    main() 