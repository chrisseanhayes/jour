import os
from datetime import datetime

def get_history_path():
    """Get the path to the history log file."""
    home_dir = os.path.expanduser("~")
    logs_dir = os.path.join(home_dir, ".jour", "logs")
    history_file = os.path.join(logs_dir, "history")
    
    # Create directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    return history_file

def log_command(command, args=None):
    """Log a command with timestamp to the history file."""
    history_path = get_history_path()
    
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
