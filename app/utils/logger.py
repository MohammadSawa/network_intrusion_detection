import logging
import os
from datetime import datetime
from pathlib import Path

class InstallationLogger:
    def __init__(self, workspace_id=None):
        
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        
        self.install_logs_dir = self.logs_dir / "installations"
        self.install_logs_dir.mkdir(exist_ok=True)
        
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace_prefix = f"workspace_{workspace_id}_" if workspace_id else ""
        self.log_filename = self.install_logs_dir / f"{workspace_prefix}installation_{timestamp}.log"
        
        
        self.logger = logging.getLogger(f"installation_{timestamp}")
        self.logger.setLevel(logging.DEBUG)
        
        
        file_handler = logging.FileHandler(self.log_filename)
        file_handler.setLevel(logging.DEBUG)
        
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_step(self, step_name, status, details=None):
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
        if exception:
            self.logger.error(f"{error_message} - Exception: {str(exception)}", exc_info=True)
        else:
            self.logger.error(error_message)
    
    def log_info(self, message):
        self.logger.info(message)
    
    def log_debug(self, message):
        self.logger.debug(message)
    
    def get_log_file_path(self):
        return str(self.log_filename) 