"""
Utility helper functions for the document review system
"""

import os


def ensure_directory(directory: str):
    """Ensure a directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def load_file(file_path: str) -> str:
    """Load content from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {str(e)}")


def save_file(file_path: str, content: str):
    """Save content to a text file"""
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_directory(directory)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"Error saving file {file_path}: {str(e)}")
