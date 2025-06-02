# Network Anomaly Detection Monitor

A comprehensive network traffic anomaly detection system that uses machine learning to identify suspicious network activities.

## Features


- **Real-time Monitoring**: Continuously monitors directories for new CSV files
- **Machine Learning Detection**: Uses XGBoost and random forest to detect various types of network anomalies
- **Web Dashboard**: User-friendly interface for viewing results and managing workspaces

- **Flexible Configuration**: Customizable monitoring intervals and directories

## Quick Start
### 0. install python version 3.9
### 1. Setup Virtual Environment (Recommended)
```bash
# Create virtual environment
py -3.9 -m venv venv

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
- **CICFlowMeter format**: Files must be generated using CICFlowMeter, or if you want to use another tool see this: If you are an engineer and prefer to use another network analysis tool, ensure your CSV files contain exactly these 78 features in the correct order:

Destination Port, Flow Duration, Total Fwd Packets, Total Backward Packets, Total Length of Fwd Packets, Total Length of Bwd Packets, Fwd Packet Length Max, Fwd Packet Length Min, Fwd Packet Length Mean, Fwd Packet Length Std, Bwd Packet Length Max, Bwd Packet Length Min, Bwd Packet Length Mean, Bwd Packet Length Std, Flow Bytes/s, Flow Packets/s, Flow IAT Mean, Flow IAT Std, Flow IAT Max, Flow IAT Min, Fwd IAT Total, Fwd IAT Mean, Fwd IAT Std, Fwd IAT Max, Fwd IAT Min, Bwd IAT Total, Bwd IAT Mean, Bwd IAT Std, Bwd IAT Max, Bwd IAT Min, Fwd PSH Flags, Bwd PSH Flags, Fwd URG Flags, Bwd URG Flags, Fwd Header Length, Bwd Header Length, Fwd Packets/s, Bwd Packets/s, Min Packet Length, Max Packet Length, Packet Length Mean, Packet Length Std, Packet Length Variance, FIN Flag Count, SYN Flag Count, RST Flag Count, PSH Flag Count, ACK Flag Count, URG Flag Count, CWE Flag Count, ECE Flag Count, Down/Up Ratio, Average Packet Size, Avg Fwd Segment Size, Avg Bwd Segment Size, Fwd Header Length.1, Fwd Avg Bytes/Bulk, Fwd Avg Packets/Bulk, Fwd Avg Bulk Rate, Bwd Avg Bytes/Bulk, Bwd Avg Packets/Bulk, Bwd Avg Bulk Rate, Subflow Fwd Packets, Subflow Fwd Bytes, Subflow Bwd Packets, Subflow Bwd Bytes, Init_Win_bytes_forward, Init_Win_bytes_backward, act_data_pkt_fwd, min_seg_size_forward, Active Mean, Active Std, Active Max, Active Min, Idle Mean, Idle Std, Idle Max, Idle Min
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
- **Web Attack** - Web-based attacks
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

### API Endpoints
- `POST /api/login` - User authentication
- `POST /api/direct-process` - Process CSV data
- `GET /api/logs` - Retrieve processing logs
- `GET /api/workspaces` - Manage workspaces

## Security

- **Local processing**: All data processed locally

## Requirements

- Python 3.9+
- CICFlowMeter for traffic capture 