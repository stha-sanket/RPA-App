import subprocess
import threading
import logging
import os
import time
import sys
from datetime import datetime
from typing import Callable, Optional, Any

def create_logger(log_file: str) -> logging.Logger:
    """
    Create a logger that writes to both the console and a file
    
    Args:
        log_file: Path to the log file
        
    Returns:
        A configured logger instance
    """
    # Create logger
    logger = logging.getLogger("rpa_runner")
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Clear any existing handlers
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    
    return logger

def execute_script(
    script_path: str, 
    log_file: str,
    on_complete: Callable[[], None],
    on_result: Callable[[Any], None],
    on_status_change: Callable[[str], None]
) -> None:
    """
    Execute an RPA script in a separate thread and capture its output
    
    Args:
        script_path: Path to the script to execute
        log_file: Path to the log file
        on_complete: Callback to execute when script completes
        on_result: Callback to receive the script result
        on_status_change: Callback to update execution status
    """
    def run_script():
        logger = create_logger(log_file)
        result = None
        
        try:
            logger.info(f"Starting script execution: {os.path.basename(script_path)}")
            logger.info(f"Command: python {script_path}")
            
            # Execute the script as a subprocess
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Process output in real-time
            stdout_output = []
            stderr_output = []
            
            # Function to read from a pipe and log it
            def read_pipe(pipe, output_list, level):
                for line in iter(pipe.readline, ''):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    formatted_line = f"[{timestamp}] {line.strip()}"
                    if level == "ERROR":
                        logger.error(line.strip())
                    else:
                        logger.info(line.strip())
                    output_list.append(line)
            
            # Create threads to read stdout and stderr
            stdout_thread = threading.Thread(
                target=read_pipe, 
                args=(process.stdout, stdout_output, "INFO")
            )
            stderr_thread = threading.Thread(
                target=read_pipe, 
                args=(process.stderr, stderr_output, "ERROR")
            )
            
            # Start the threads
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for the process to complete
            return_code = process.wait()
            
            # Wait for threads to complete
            stdout_thread.join()
            stderr_thread.join()
            
            # Collect results
            stdout_str = ''.join(stdout_output)
            stderr_str = ''.join(stderr_output)
            
            if return_code == 0:
                logger.info("Script execution completed successfully")
                on_status_change("Completed")
                # Store the result
                result = stdout_str if stdout_str.strip() else "Script executed successfully with no output."
            else:
                logger.error(f"Script execution failed with return code {return_code}")
                on_status_change("Failed")
                # Include error in result
                result = f"Script execution failed with return code {return_code}.\n\nSTDERR:\n{stderr_str}\n\nSTDOUT:\n{stdout_str}"
                
            # Parse the result if it looks like structured data
            if stdout_str.strip().startswith('{') and stdout_str.strip().endswith('}'):
                try:
                    import json
                    parsed_result = json.loads(stdout_str)
                    result = parsed_result
                except:
                    # If parsing fails, use the string version
                    pass
                    
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            on_status_change("Failed")
            result = f"Error executing script: {str(e)}"
        
        finally:
            logger.info("Script execution thread completed")
            on_result(result)
            on_complete()
    
    # Start execution in a separate thread
    thread = threading.Thread(target=run_script)
    thread.daemon = True
    thread.start()
