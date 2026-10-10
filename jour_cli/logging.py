from datetime import datetime
from typing import Optional
from shared.file_ops import FileOperations

def get_history_path(file_ops: Optional[FileOperations] = FileOperations(),):
    """Get the path to the history log file."""
    home_dir = file_ops.path.expanduser("~")
    logs_dir = file_ops.path.join(home_dir, ".jour", "logs")
    history_file = file_ops.path.join(logs_dir, "history")
    
    # Create directory if it doesn't exist
    file_ops.makedirs(logs_dir, exist_ok=True)
    
    return history_file

def log_command(command, args=None, file_ops: Optional[FileOperations] = FileOperations()):
    """Log a command with timestamp to the history file."""
    history_path = get_history_path(file_ops)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the command line
    if args:
        # Convert args to string representation
        args_str = ", ".join([f"{k}={v}" for k, v in vars(args).items() if v is not None])
        log_line = f"[{timestamp}] {command} {args_str}\n"
    else:
        log_line = f"[{timestamp}] {command}\n"
    
    with open(history_path, "a") as f:
        f.write(log_line)

def read_history(limit=20, file_ops: Optional[FileOperations] = FileOperations()):
    """Read and return the last N lines from the history file."""
    history_path = get_history_path(file_ops)
    
    if not file_ops.path.exists(history_path):
        # Create empty history file to ensure it exists for future logging
        with open(history_path, "w") as f:
            pass
        return []
    
    with open(history_path, "r") as f:
        lines = f.readlines()
    
    # Return last N lines (or all if fewer than N)
    return [line.rstrip("\n") for line in lines[-limit:]]
