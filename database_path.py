"""
Database path utilities.

Provides a default database path and helper functions for locating the JMDict database.
Uses platform-appropriate user data directories for installed packages.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_user_data_dir() -> Path:
    """
    Get the platform-specific user data directory for this application.
    
    Returns:
        Path to user data directory:
        - Linux: ~/.local/share/tentoku
        - macOS: ~/Library/Application Support/tentoku
        - Windows: %APPDATA%/tentoku
    """
    if sys.platform == "win32":
        # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            # Fallback to user home
            base = Path.home()
        return base / "tentoku"
    elif sys.platform == "darwin":
        # macOS
        return Path.home() / "Library" / "Application Support" / "tentoku"
    else:
        # Linux and other Unix-like systems
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if xdg_data_home:
            base = Path(xdg_data_home)
        else:
            base = Path.home() / ".local" / "share"
        return base / "tentoku"


def get_default_database_path() -> Path:
    """
    Get the default database path.
    
    For installed packages (PyPI), uses user data directory.
    For development (source), uses module's data directory.
    
    Returns:
        Path to the default jmdict.db file
    """
    # Check if we're in an installed package (not in source tree)
    module_dir = Path(__file__).parent
    module_data_dir = module_dir / "data"
    
    # If module is in site-packages or similar, use user data dir
    # Check if module_dir looks like an installed package location
    if "site-packages" in str(module_dir) or "dist-packages" in str(module_dir):
        # Installed package - use user data directory
        user_data_dir = get_user_data_dir()
        user_data_dir.mkdir(parents=True, exist_ok=True)
        return user_data_dir / "jmdict.db"
    else:
        # Development/source tree - use module's data directory
        module_data_dir.mkdir(parents=True, exist_ok=True)
        return module_data_dir / "jmdict.db"


def find_database_path() -> Optional[Path]:
    """
    Find the JMDict database file, checking multiple locations.
    
    Checks in order:
    1. User data directory (for installed packages)
    2. Module's data directory (for development)
    3. Parent directory's python-jmdict-sqlite-db/jmdict.db
    4. Parent directory's data-processing/jmdict.db
    
    Returns:
        Path to the database file if found, None otherwise
    """
    # Check user data directory first (for installed packages)
    user_data_path = get_user_data_dir() / "jmdict.db"
    if user_data_path.exists():
        return user_data_path
    
    # Check default location (module data directory)
    default_path = get_default_database_path()
    if default_path.exists():
        return default_path
    
    # Check other common locations (for development)
    module_dir = Path(__file__).parent
    parent_dir = module_dir.parent
    
    alternative_paths = [
        parent_dir / "python-jmdict-sqlite-db" / "jmdict.db",
        parent_dir / "data-processing" / "jmdict.db",
    ]
    
    for path in alternative_paths:
        if path.exists():
            return path
    
    return None
