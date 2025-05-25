# Network Anomaly Detection Monitor

A comprehensive network traffic anomaly detection system that uses machine learning to identify suspicious network activities.

## Features

- **Automated Authentication**: Simple username/password login - no API key management needed
- **Real-time Monitoring**: Continuously monitors directories for new CSV files
- **Machine Learning Detection**: Uses trained models to detect various types of network anomalies
- **Web Dashboard**: User-friendly interface for viewing results and managing workspaces
- **Session Management**: Remembers your settings for 24 hours
- **Flexible Configuration**: Customizable monitoring intervals and directories

## Quick Start

### 1. Setup Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the API Server
```bash
# Start the server (make sure venv is activated)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Create an Account
- Visit `http://localhost:8000` in your browser
- Register a new account with username, email, and password
- Create a workspace for your monitoring activities

### 4. Run the Network Monitor
```bash
# Run the monitor executable
python network_monitor.py
```

The monitor will:
1. **Prompt for credentials**: Enter your username and password
2. **Ask for preferences**: 
   - Check interval (how often to scan for files)
   - CSV directory (where to monitor for files, default: same as executable)
3. **Save your session**: Settings are remembered for 24 hours
4. **Start monitoring**: Automatically process any CSV files found

## Usage

### First Time Setup
When you run the monitor for the first time:

```
===============================================================
Network Anomaly Detection Monitor - Authentication
===============================================================

Please enter your credentials to continue:

Username: your_username
Password: [hidden]

✓ Authentication successful! Welcome, your_username

===============================================================
                    Monitoring Configuration
===============================================================

Check interval in seconds (default: 10): 30
CSV file monitoring directory:
Press Enter to use the same directory as this program: C:\path\to\monitor
Or enter a custom path: 

Found existing session. Using saved configuration...
```

### Subsequent Runs
The monitor remembers your settings:
   ```
Found existing session. Using saved configuration...
```

### Command Line Options
```bash
# Reset saved session and re-authenticate
python network_monitor.py --reset-session

# Override check interval
python network_monitor.py --interval 30

# Override CSV directory
python network_monitor.py --csv-dir "C:\custom\path"
```

## File Processing

### Input Requirements
- **CSV files**: Place CSV files in the monitored directory
- **CICFlowMeter format**: Files must be generated using CICFlowMeter
- **Automatic processing**: Files are processed automatically when detected

### Output Directories
The monitor creates these directories automatically:
- `processed/` - Successfully processed files
- `failed/` - Files that couldn't be processed  
- `logs/` - Detailed processing logs

### Supported Anomaly Types
The system can detect:
- **DoS** - Denial of Service attacks
- **DDoS** - Distributed Denial of Service attacks
- **PortScan** - Port scanning activities
- **Brute Force** - Brute force attacks
- **Bot** - Automated/bot traffic
- **BENIGN** - Normal traffic

## Web Interface

Access the web dashboard at `http://localhost:8000`:

- **Dashboard**: View workspace overview and download monitor
- **Logs**: Browse detected anomalies with filtering and search
- **Workspaces**: Manage multiple monitoring projects

## Configuration

### Session Management
- Sessions last 24 hours
- Configuration saved automatically
- Use `--reset-session` to start fresh

### Directory Structure
```
monitor_directory/
├── network_monitor.exe     # The monitor executable
├── .session_config         # Saved session (auto-created)
├── processed/              # Successfully processed files
├── failed/                 # Failed processing attempts
└── logs/                   # Processing logs
    └── monitor.log
```

## Troubleshooting

### Authentication Issues
- Ensure the API server is running on `http://localhost:8000`
- Verify your username and password are correct
- Check that you have a registered account

### Connection Problems
- Confirm the API server is accessible
- Check firewall settings
- Verify network connectivity

### File Processing Issues
- Ensure CSV files are in CICFlowMeter format
- Check `logs/monitor.log` for detailed error messages
- Verify file permissions and disk space

### Reset Configuration
```bash
# Clear saved session and start fresh
python network_monitor.py --reset-session
```

## Development

### Project Structure
```
├── app/                    # Web application
│   ├── api/               # API endpoints
│   ├── core/              # Database and authentication
│   ├── templates/         # HTML templates
│   └── static/            # Static files
├── network_monitor.py     # Main monitor script
└── requirements.txt       # Dependencies
```

### API Endpoints
- `POST /api/login` - User authentication
- `POST /api/direct-process` - Process CSV data
- `GET /api/logs` - Retrieve processing logs
- `GET /api/workspaces` - Manage workspaces

## Security

- **No exposed API keys**: API keys are managed internally
- **Session-based**: Temporary session storage (24 hours)
- **Secure authentication**: Password hashing with bcrypt
- **Local processing**: All data processed locally

## Requirements

- Python 3.8+
- Windows 7 or later (for executable)
- CICFlowMeter for traffic capture
- 100MB+ free disk space 