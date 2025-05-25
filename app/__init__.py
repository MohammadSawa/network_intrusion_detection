"""
Network Anomaly Detection System

This package provides tools to detect anomalies in network traffic data.
"""

import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
def ensure_directories():
    """Create required directories if they don't exist."""
    # Get the base directory
    base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    
    # Define required directories
    required_dirs = [
        base_dir / 'csv_output',
        base_dir / 'processed',
        base_dir / 'results',
        base_dir / 'logs',
        # Make sure static and installers dirs exist
        Path(__file__).parent / 'static',
        Path(__file__).parent / 'static' / 'installers'
    ]
    
    # Create directories if they don't exist
    for directory in required_dirs:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)

# Call ensure_directories when the module is imported
ensure_directories()

# Version information
__version__ = '1.0.0' 