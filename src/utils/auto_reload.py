"""
Auto-reload functionality for development.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Set
import threading

logger = logging.getLogger(__name__)


class FileWatcher:
    """
    Watches files for changes and triggers reload when needed.
    """
    
    def __init__(self, watch_dirs: List[str] = None, file_extensions: Set[str] = None):
        """
        Initialize file watcher.
        
        Args:
            watch_dirs: Directories to watch for changes
            file_extensions: File extensions to monitor
        """
        self.watch_dirs = watch_dirs or ['src']
        self.file_extensions = file_extensions or {'.py'}
        self.file_mtimes: Dict[str, float] = {}
        self.is_watching = False
        self.watch_thread = None
        self.reload_callback = None
        
    def start_watching(self, reload_callback=None):
        """
        Start watching for file changes.
        
        Args:
            reload_callback: Function to call when changes detected
        """
        if self.is_watching:
            return
            
        self.reload_callback = reload_callback
        self.is_watching = True
        self._scan_files()  # Initial scan
        
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        
        logger.info(f"Started watching {len(self.file_mtimes)} files for changes")
        
    def stop_watching(self):
        """Stop watching for file changes."""
        self.is_watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=1)
            
    def _scan_files(self):
        """Scan all files and record modification times."""
        for watch_dir in self.watch_dirs:
            if os.path.exists(watch_dir):
                for root, dirs, files in os.walk(watch_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in self.file_extensions):
                            file_path = os.path.join(root, file)
                            try:
                                self.file_mtimes[file_path] = os.path.getmtime(file_path)
                            except OSError:
                                pass  # File might be deleted/inaccessible
                                
    def _watch_loop(self):
        """Main watching loop."""
        while self.is_watching:
            try:
                time.sleep(1)  # Check every second
                
                changes_detected = False
                current_files = set()
                
                # Check existing files for modifications
                for file_path, old_mtime in list(self.file_mtimes.items()):
                    current_files.add(file_path)
                    try:
                        current_mtime = os.path.getmtime(file_path)
                        if current_mtime > old_mtime:
                            logger.info(f"File changed: {file_path}")
                            self.file_mtimes[file_path] = current_mtime
                            changes_detected = True
                    except OSError:
                        # File was deleted
                        logger.info(f"File deleted: {file_path}")
                        del self.file_mtimes[file_path]
                        changes_detected = True
                        
                # Check for new files
                for watch_dir in self.watch_dirs:
                    if os.path.exists(watch_dir):
                        for root, dirs, files in os.walk(watch_dir):
                            for file in files:
                                if any(file.endswith(ext) for ext in self.file_extensions):
                                    file_path = os.path.join(root, file)
                                    if file_path not in current_files:
                                        try:
                                            self.file_mtimes[file_path] = os.path.getmtime(file_path)
                                            logger.info(f"New file detected: {file_path}")
                                            changes_detected = True
                                        except OSError:
                                            pass
                                            
                # Trigger reload if changes detected
                if changes_detected and self.reload_callback:
                    try:
                        self.reload_callback()
                    except Exception as e:
                        logger.error(f"Error in reload callback: {e}")
                        
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                time.sleep(5)  # Wait before retrying


# Global file watcher instance
file_watcher = FileWatcher()


def enable_auto_reload(app_instance):
    """
    Enable auto-reload for the application.
    
    Args:
        app_instance: Application instance with reload method
    """
    def reload_callback():
        try:
            logger.info("Auto-reloading due to file changes...")
            app_instance._reload_modules()
            logger.info("Auto-reload completed")
        except Exception as e:
            logger.error(f"Auto-reload failed: {e}")
            
    file_watcher.start_watching(reload_callback)


def disable_auto_reload():
    """Disable auto-reload."""
    file_watcher.stop_watching()