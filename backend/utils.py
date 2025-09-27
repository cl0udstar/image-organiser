#!/usr/bin/env python3
"""
Utility functions for Image Organizer
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from .config import config

def make_serializable(obj):
    """Ensure all values are JSON serializable"""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(v) for v in obj]
    elif hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    elif isinstance(obj, (np.bool_, np.integer, np.floating)):
        return obj.item()
    else:
        return obj

def generate_filename_from_template(template, image_path, primary_category=None):
    """Generate filename from template parameters or fallback to category naming"""
    try:
        person_name = template.get('person_name', '').strip()
        event = template.get('event', '').strip()
        date = template.get('date', '').strip()
        seq_number = template.get('seq_number', '').strip()
        
        # Check if any meaningful template data is provided
        has_template_data = any([person_name, event, date, seq_number])
        
        if not has_template_data and primary_category:
            # Use fallback naming: category_XXX.ext
            current_seq = config['category_sequences'].get(primary_category, 0) + 1
            filename = f"{primary_category}_{current_seq:03d}{image_path.suffix}"
            return filename, True  # Return True to indicate fallback was used
        
        # Use template naming
        # If date is empty, use current date
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # Build filename parts
        parts = []
        if person_name:
            parts.append(person_name)
        if event:
            parts.append(event)
        if date:
            parts.append(date)
        if seq_number:
            parts.append(seq_number)
        
        if parts:
            filename = '_'.join(parts) + image_path.suffix
        else:
            # Even if no parts, still try fallback if we have a category
            if primary_category:
                current_seq = config['category_sequences'].get(primary_category, 0) + 1
                filename = f"{primary_category}_{current_seq:03d}{image_path.suffix}"
                return filename, True
            else:
                filename = image_path.name
        
        # Clean filename (remove invalid characters)
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        return filename, False  # Return False to indicate template was used
        
    except Exception as e:
        print(f"Error generating filename: {e}")
        # Ultimate fallback
        if primary_category:
            current_seq = config['category_sequences'].get(primary_category, 0) + 1
            return f"{primary_category}_{current_seq:03d}{image_path.suffix}", True
        return image_path.name, False

def create_backup(source_path, current_image, purpose="backup"):
    """Create a backup of the current image"""
    backup_path = source_path / config['backup_folder'] / f"{purpose}_{current_image.name}"
    counter = 1
    while backup_path.exists():
        stem = current_image.stem
        suffix = current_image.suffix
        backup_path = source_path / config['backup_folder'] / f"{purpose}_{stem}_{counter}{suffix}"
        counter += 1
    return backup_path

def ensure_unique_destination(destination_path):
    """Ensure destination path is unique by adding counter if needed"""
    destination = Path(destination_path)
    counter = 1
    while destination.exists():
        stem = destination.stem
        suffix = destination.suffix
        destination = destination.parent / f"{stem}_{counter}{suffix}"
        counter += 1
    return destination

def get_categories_from_directory(source_folder):
    """Get list of existing directories that could be used as categories"""
    try:
        source_path = Path(source_folder)
        if not source_path.exists():
            return []
        
        categories = []
        for item in source_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Skip utility folders
                if item.name not in [config['deleted_folder'], config['backup_folder'], 'duplicates_startup']:
                    categories.append(item.name)
        
        return sorted(categories)
    except Exception as e:
        print(f"Error getting categories from directory: {e}")
        return []