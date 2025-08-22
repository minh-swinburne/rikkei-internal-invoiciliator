"""
Single Instance Manager for Invoice Reconciliator
Ensures only one instance of the application runs at a time across different platforms.
Works for both development Python and built executable versions.
"""

import os
import sys
import time
import socket
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SingleInstanceManager:
    """
    Cross-platform single instance manager using socket binding.
    This approach works on Windows, macOS, and Linux for both Python and executable versions.
    """
    
    def __init__(self, app_name: str = "InvoiceReconciliator", port_base: int = 47821):
        self.app_name = app_name
        self.port = port_base
        self.socket: Optional[socket.socket] = None
        self.lock_file = self._get_lock_file_path()
        
        # Add a small delay to allow proper socket cleanup
        import time
        time.sleep(0.1)
        
    def _get_lock_file_path(self) -> Path:
        """Get platform-appropriate lock file path"""
        if sys.platform == "win32":
            # Windows: Use temp directory
            lock_dir = Path(os.environ.get('TEMP', os.environ.get('TMP', '.')))
        else:
            # Unix-like: Use /tmp or user home
            lock_dir = Path('/tmp') if Path('/tmp').exists() else Path.home()
            
        return lock_dir / f".{self.app_name.lower()}.lock"
    
    def is_already_running(self) -> bool:
        """
        Check if another instance is already running.
        Uses socket binding as primary method with lock file as backup.
        """
        # Method 1: Try to bind to a specific port
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)  # Disable reuse
            self.socket.bind(('127.0.0.1', self.port))
            self.socket.listen(1)
            
            # If we can bind, we're the first instance
            self._create_lock_file()
            logger.info(f"Single instance lock acquired on port {self.port}")
            return False
            
        except socket.error as e:
            # Port is already in use, another instance is running
            logger.info(f"Another instance detected on port {self.port}: {e}")
            return True
    
    def _create_lock_file(self):
        """Create lock file with process information"""
        try:
            with open(self.lock_file, 'w') as f:
                f.write(f"PID={os.getpid()}\n")
                f.write(f"START_TIME={time.time()}\n")
                f.write(f"EXECUTABLE={sys.executable}\n")
                f.write(f"SCRIPT={sys.argv[0]}\n")
        except Exception as e:
            logger.warning(f"Could not create lock file: {e}")
    
    def cleanup(self):
        """Clean up resources when application exits"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Single instance socket closed")
            except Exception as e:
                logger.warning(f"Error closing socket: {e}")
        
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("Lock file removed")
        except Exception as e:
            logger.warning(f"Could not remove lock file: {e}")
    
    def try_show_existing_instance(self) -> bool:
        """
        Attempt to bring existing instance to foreground.
        Returns True if successful, False otherwise.
        """
        try:
            # Send a simple message to the existing instance
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(2.0)  # 2 second timeout
            client_socket.connect(('127.0.0.1', self.port))
            client_socket.send(b"SHOW_WINDOW")
            client_socket.close()
            logger.info("Sent show window signal to existing instance")
            return True
        except Exception as e:
            logger.warning(f"Could not communicate with existing instance: {e}")
            return False


class SingleInstanceListener:
    """
    Listener component that runs in the main application instance
    to handle requests from secondary instances.
    """
    
    def __init__(self, manager: SingleInstanceManager, show_window_callback=None):
        self.manager = manager
        self.show_window_callback = show_window_callback
        self.running = False
        
    def start_listening(self):
        """Start listening for requests from other instances"""
        if not self.manager.socket:
            return
            
        self.running = True
        
        def listen_worker():
            while self.running:
                try:
                    self.manager.socket.settimeout(1.0)  # Non-blocking with timeout
                    conn, addr = self.manager.socket.accept()
                    data = conn.recv(1024)
                    
                    if data == b"SHOW_WINDOW" and self.show_window_callback:
                        logger.info("Received show window request")
                        self.show_window_callback()
                    
                    conn.close()
                except socket.timeout:
                    continue  # Normal timeout, keep listening
                except Exception as e:
                    if self.running:  # Only log if we're supposed to be running
                        logger.warning(f"Error in instance listener: {e}")
                    break
        
        # Start listener in a separate thread
        import threading
        self.listener_thread = threading.Thread(target=listen_worker, daemon=True)
        self.listener_thread.start()
        logger.info("Single instance listener started")
    
    def stop_listening(self):
        """Stop listening for requests"""
        self.running = False
        logger.info("Single instance listener stopped")


# Convenience function for easy integration
def ensure_single_instance(app_name: str = "InvoiceReconciliator") -> tuple[SingleInstanceManager, bool]:
    """
    Ensure only one instance of the application runs.
    
    Returns:
        tuple: (SingleInstanceManager, is_first_instance)
        - SingleInstanceManager: Manager object for cleanup
        - is_first_instance: True if this is the first instance, False if another exists
    """
    manager = SingleInstanceManager(app_name)
    
    if manager.is_already_running():
        # Try to show existing instance
        manager.try_show_existing_instance()
        return manager, False
    
    return manager, True
