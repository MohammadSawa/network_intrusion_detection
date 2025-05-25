import logging
import os
from datetime import datetime
from pathlib import Path

class InstallationLogger:
    def __init__(self, workspace_id=None):
        # Create logs directory if it doesn't exist
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create installation logs directory
        self.install_logs_dir = self.logs_dir / "installations"
        self.install_logs_dir.mkdir(exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace_prefix = f"workspace_{workspace_id}_" if workspace_id else ""
        self.log_filename = self.install_logs_dir / f"{workspace_prefix}installation_{timestamp}.log"
        
        # Configure logger
        self.logger = logging.getLogger(f"installation_{timestamp}")
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_filename)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add them to the handlers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_step(self, step_name, status, details=None):
        """Log an installation step with its status and details."""
        message = f"Step: {step_name} - Status: {status}"
        if details:
            message += f" - Details: {details}"
        
        if status.lower() == "success":
            self.logger.info(message)
        elif status.lower() == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def log_error(self, error_message, exception=None):
        """Log an error with optional exception details."""
        if exception:
            self.logger.error(f"{error_message} - Exception: {str(exception)}", exc_info=True)
        else:
            self.logger.error(error_message)
    
    def log_info(self, message):
        """Log an informational message."""
        self.logger.info(message)
    
    def log_debug(self, message):
        """Log a debug message."""
        self.logger.debug(message)
    
    def get_log_file_path(self):
        """Return the path to the log file."""
        return str(self.log_filename) 