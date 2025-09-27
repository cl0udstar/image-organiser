#!/usr/bin/env python3
"""
Configuration and global state management for Image Organizer
"""

import json
from pathlib import Path

# Global configuration
config = {
    'source_folder': '',
    'categories': [],  # Start with empty categories
    'current_image_index': 0,
    'processed_images': [],
    'deleted_folder': 'deleted',
    'backup_folder': 'backup',
    'session_file': 'session.json',
    'current_rotation': 0,
    'sequence_numbers': {},  # Track sequence numbers per event
    'category_sequences': {}  # Track sequence numbers per category (for fallback naming)
}

def save_session():
    """Save current session to file"""
    if config['source_folder']:
        session_path = Path(config['source_folder']) / config['session_file']
        with open(session_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)

def load_session():
    """Load session from file"""
    if config['source_folder']:
        session_path = Path(config['source_folder']) / config['session_file']
        if session_path.exists():
            try:
                with open(session_path, 'r') as f:
                    saved_config = json.load(f)
                    config.update(saved_config)
                return True
            except:
                pass
    return False

def reset_config():
    """Reset configuration to defaults"""
    global config
    config = {
        'source_folder': '',
        'categories': [],
        'current_image_index': 0,
        'processed_images': [],
        'deleted_folder': 'deleted',
        'backup_folder': 'backup',
        'session_file': 'session.json',
        'current_rotation': 0,
        'sequence_numbers': {},
        'category_sequences': {}
    }
