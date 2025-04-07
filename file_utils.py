"""
File utility functions for the comparison tool.
Handles file operations including reading, path resolution, and validation.
"""
import os
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Set, Tuple

def read_file(file_path: str) -> Optional[List[str]]:
    """
    Read a file and return its content as a list of lines.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        List of lines in the file, or None if file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    except (IOError, UnicodeDecodeError) as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def get_file_paths(
    directory_path: str, 
    recursive: bool = False,
    ignore_patterns: List[str] = []
) -> List[str]:
    """
    Get all file paths in a directory.
    
    Args:
        directory_path: Path to the directory
        recursive: Whether to recursively search subdirectories
        ignore_patterns: List of patterns to ignore
        
    Returns:
        List of file paths
    """
    file_paths = []
    base_path = Path(directory_path)
    
    def should_ignore(path: str) -> bool:
        """Check if file matches any ignore patterns."""
        filename = os.path.basename(path)
        return any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns)
    
    if recursive:
        for root, _, files in os.walk(directory_path):
            for file in files:
                path = os.path.join(root, file)
                if not should_ignore(path):
                    file_paths.append(path)
    else:
        try:
            for item in os.listdir(directory_path):
                path = os.path.join(directory_path, item)
                if os.path.isfile(path) and not should_ignore(path):
                    file_paths.append(path)
        except OSError as e:
            print(f"Error accessing directory {directory_path}: {str(e)}")
    
    return file_paths

def get_relative_path(base_path: str, full_path: str) -> str:
    """
    Get the relative path from a base path.
    
    Args:
        base_path: Base directory path
        full_path: Full path to get relative path for
        
    Returns:
        Relative path
    """
    return os.path.relpath(full_path, base_path)
