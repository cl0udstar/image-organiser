#!/usr/bin/env python3
"""
API routes for Image Organizer Flask backend
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from flask import request, jsonify, send_file, render_template

from .config import config, save_session, load_session
from .image_processor import ImageProcessor
from .utils import (
    make_serializable, 
    generate_filename_from_template,
    create_backup,
    ensure_unique_destination,
    get_categories_from_directory
)

# Global processor instance
processor = None

def setup_routes(app):
    """Setup all API routes"""
    
    @app.route('/')
    def index():
        """Main application page"""
        try:
            return render_template('index.html')
        except Exception as e:
            # Fallback if template is not found
            return f"Template error: {e}. Please check if frontend/templates/index.html exists."
    
    @app.route('/test')
    def test():
        """Test route to verify server is working"""
        return "Server is working! 🎉"

    @app.route('/api/setup', methods=['POST'])
    def setup():
        """Setup source folder and categories"""
        global processor, config
        
        data = request.json
        source_folder = data.get('source_folder', '')
        categories = data.get('categories', config['categories'])
        handle_duplicates = data.get('handle_duplicates', True)  # Default to True
        
        # Normalize path for Windows
        source_folder = source_folder.replace('/', os.sep).replace('\\', os.sep)
        
        if not source_folder:
            return jsonify({'error': 'Please provide a source folder path'}), 400
            
        source_path = Path(source_folder)
        if not source_path.exists():
            return jsonify({'error': f'Folder does not exist: {source_folder}'}), 400
            
        if not source_path.is_dir():
            return jsonify({'error': f'Path is not a directory: {source_folder}'}), 400
        
        try:
            config['source_folder'] = str(source_path)
            config['categories'] = categories
            
            # Initialize processor
            processor = ImageProcessor(source_folder)
            
            if not processor.images:
                return jsonify({'error': 'No supported image files found in the selected folder'}), 400
            
            initial_count = len(processor.images)
            duplicates_count = 0
            duplicates_info = []
            
            # Handle duplicates if requested
            if handle_duplicates:
                print("Starting duplicate detection...")
                try:
                    duplicates_count, duplicates_info = processor.handle_duplicates_on_startup()
                except AttributeError:
                    # Fallback if method doesn't exist
                    print("Duplicate detection method not available, skipping...")
                    duplicates_count, duplicates_info = 0, []
            
            # Create category folders
            for category in categories:
                (source_path / category).mkdir(exist_ok=True)
            
            # Create utility folders
            (source_path / config['deleted_folder']).mkdir(exist_ok=True)
            (source_path / config['backup_folder']).mkdir(exist_ok=True)
            
            # Load session if exists
            load_session()
            
            print(f"Setup complete: {len(processor.images)} unique images found")
            if duplicates_count > 0:
                print(f"Moved {duplicates_count} duplicates to duplicates_startup folder")
            
            return jsonify({
                'success': True,
                'total_images': len(processor.images),
                'initial_count': initial_count,
                'duplicates_found': duplicates_count,
                'duplicates_info': duplicates_info,
                'categories': categories,
                'current_index': config['current_image_index']
            })
            
        except Exception as e:
            print(f"Setup error: {e}")
            return jsonify({'error': f'Setup failed: {str(e)}'}), 500

    @app.route('/api/images/current')
    def get_current_image():
        """Get current image information"""
        if not processor or not processor.images:
            return jsonify({'error': 'No images loaded'}), 400
        
        if config['current_image_index'] >= len(processor.images):
            return jsonify({'finished': True})
        
        try:
            current_image = processor.images[config['current_image_index']]
            image_info = processor.get_image_info(current_image)
            
            # Ensure all values are JSON serializable
            image_info = make_serializable(image_info)
            
            return jsonify({
                'image': image_info,
                'index': config['current_image_index'],
                'total': len(processor.images),
                'progress': (config['current_image_index'] / len(processor.images)) * 100
            })
        except Exception as e:
            print(f"Error getting current image: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/images/file/<path:filename>')
    def serve_image(filename):
        """Serve image file"""
        try:
            # Handle relative path from source folder
            file_path = Path(config['source_folder']) / filename.replace('/', os.sep)
            file_path = file_path.resolve()  # Resolve to absolute path
            
            # Security check: ensure the resolved path is within the source folder
            source_path = Path(config['source_folder']).resolve()
            if not str(file_path).startswith(str(source_path)):
                return jsonify({'error': 'Access denied'}), 403
            
            if file_path.exists() and file_path.is_file():
                response = send_file(str(file_path))
                # Add cache-busting headers to prevent browser caching issues
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
            else:
                print(f"File not found: {file_path}")
                return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            print(f"Error serving image {filename}: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/images/process', methods=['POST'])
    def process_image():
        """Process current image (move to category or delete)"""
        global config
        
        if not processor or not processor.images:
            return jsonify({'error': 'No images loaded'}), 400
        
        if config['current_image_index'] >= len(processor.images):
            return jsonify({'error': 'No more images to process'}), 400
        
        data = request.json
        action = data.get('action')  # 'move', 'delete', 'skip'
        categories = data.get('categories', [])
        filename_template = data.get('filename_template', {})
        custom_name = data.get('custom_name', '')
        
        current_image = processor.images[config['current_image_index']]
        source_path = Path(config['source_folder'])
        
        try:
            # Create backup
            backup_path = create_backup(source_path, current_image)
            shutil.copy2(current_image, backup_path)
            
            if action == 'delete':
                # Move to deleted folder
                deleted_path = source_path / config['deleted_folder'] / current_image.name
                deleted_path = ensure_unique_destination(deleted_path)
                shutil.move(current_image, deleted_path)
                
            elif action == 'move' and categories:
                # Generate filename based on template or fallback
                if custom_name:
                    filename = f"{custom_name}{current_image.suffix}"
                elif filename_template:
                    filename, used_fallback = generate_filename_from_template(filename_template, current_image, categories[0])
                    
                    if used_fallback:
                        # Increment category sequence for fallback naming
                        category_name = categories[0]  # Use first selected category
                        current_seq = config['category_sequences'].get(category_name, 0)
                        config['category_sequences'][category_name] = current_seq + 1
                    else:
                        # Increment event sequence for template naming
                        event_name = filename_template.get('event', '').strip()
                        if event_name:
                            current_seq = config['sequence_numbers'].get(event_name, 0)
                            config['sequence_numbers'][event_name] = current_seq + 1
                else:
                    filename = current_image.name
                
                # Move to selected categories
                for category in categories:
                    category_path = source_path / category
                    destination = category_path / filename
                    destination = ensure_unique_destination(destination)
                    
                    if len(categories) == 1:
                        # Move to single category
                        shutil.move(current_image, destination)
                    else:
                        # Copy to multiple categories
                        shutil.copy2(current_image, destination)
                
                # If copied to multiple categories, remove original
                if len(categories) > 1 and current_image.exists():
                    current_image.unlink()
            
            # Record processed image
            config['processed_images'].append({
                'original_path': str(current_image),
                'action': action,
                'categories': categories,
                'filename_template': filename_template,
                'custom_name': custom_name,
                'timestamp': datetime.now().isoformat()
            })
            
            # Move to next image and reset rotation
            config['current_image_index'] += 1
            config['current_rotation'] = 0
            
            # Save session
            save_session()
            
            return jsonify({
                'success': True,
                'next_index': config['current_image_index'],
                'total': len(processor.images)
            })
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/images/skip', methods=['POST'])
    def skip_image():
        """Skip current image"""
        global config
        config['current_image_index'] += 1
        save_session()
        return jsonify({
            'success': True,
            'next_index': config['current_image_index']
        })

    @app.route('/api/images/previous', methods=['POST'])
    def previous_image():
        """Go to previous image"""
        global config
        if config['current_image_index'] > 0:
            config['current_image_index'] -= 1
        save_session()
        return jsonify({
            'success': True,
            'current_index': config['current_image_index']
        })

    @app.route('/api/images/rotate', methods=['POST'])
    def rotate_image():
        """Rotate current image"""
        global config
        
        if not processor or not processor.images:
            return jsonify({'error': 'No images loaded'}), 400
        
        if config['current_image_index'] >= len(processor.images):
            return jsonify({'error': 'No current image'}), 400
        
        data = request.json
        degrees = data.get('degrees', 90)
        
        try:
            current_image = processor.images[config['current_image_index']]
            
            # Create backup before rotation
            source_path = Path(config['source_folder'])
            backup_path = create_backup(source_path, current_image, "rotation")
            shutil.copy2(current_image, backup_path)
            
            # Rotate the image
            success = processor.rotate_image(current_image, degrees)
            
            if success:
                # Update rotation tracking
                config['current_rotation'] = (config['current_rotation'] + degrees) % 360
                return jsonify({'success': True, 'rotation': config['current_rotation']})
            else:
                return jsonify({'error': 'Failed to rotate image'}), 500
                
        except Exception as e:
            print(f"Error rotating image: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/categories', methods=['GET', 'POST'])
    def manage_categories():
        """Get or update categories"""
        if request.method == 'GET':
            return jsonify({'categories': config['categories']})
        
        data = request.json
        action = data.get('action')
        
        if action == 'add':
            # Handle individual category addition
            category_name = data.get('category', '').strip()
            
            if not category_name:
                return jsonify({'error': 'Category name is required'}), 400
            
            if category_name in config['categories']:
                return jsonify({'error': 'Category already exists'}), 400
            
            # Add to categories list
            config['categories'].append(category_name)
            
            # Create folder
            if config['source_folder']:
                source_path = Path(config['source_folder'])
                try:
                    (source_path / category_name).mkdir(exist_ok=True)
                    print(f"Created category folder: {source_path / category_name}")
                except Exception as e:
                    print(f"Error creating category folder: {e}")
                    return jsonify({'error': f'Failed to create folder: {str(e)}'}), 500
            
            # Save session
            save_session()
            
            return jsonify({
                'success': True, 
                'categories': config['categories'],
                'message': f'Category "{category_name}" added successfully'
            })
        
        else:
            # Handle full categories list update (existing functionality)
            new_categories = data.get('categories', [])
            config['categories'] = new_categories
            
            # Create new category folders
            if config['source_folder']:
                source_path = Path(config['source_folder'])
                for category in new_categories:
                    try:
                        (source_path / category).mkdir(exist_ok=True)
                    except Exception as e:
                        print(f"Error creating folder for {category}: {e}")
            
            save_session()
            return jsonify({'success': True, 'categories': config['categories']})

    @app.route('/api/categories/from-directory')
    def categories_from_directory():
        """Get categories from existing directories"""
        if not config['source_folder']:
            return jsonify({'error': 'No source folder set'}), 400
        
        categories = get_categories_from_directory(config['source_folder'])
        return jsonify({'categories': categories})

    @app.route('/api/duplicates')
    def find_duplicates():
        """Find duplicate images (for manual review)"""
        if not processor:
            return jsonify({'error': 'No images loaded'}), 400
        
        duplicates = processor.find_duplicates()
        return jsonify({'duplicates': duplicates})

    @app.route('/api/duplicates/startup-info')
    def get_startup_duplicates_info():
        """Get information about duplicates moved during startup"""
        try:
            if not config['source_folder']:
                return jsonify({'error': 'No source folder set'}), 400
            
            duplicates_folder = Path(config['source_folder']) / 'duplicates_startup'
            
            if not duplicates_folder.exists():
                return jsonify({
                    'folder_exists': False,
                    'count': 0,
                    'files': []
                })
            
            # Count duplicate files
            duplicate_files = []
            for file_path in duplicates_folder.iterdir():
                if file_path.is_file():
                    duplicate_files.append({
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime
                    })
            
            return jsonify({
                'folder_exists': True,
                'count': len(duplicate_files),
                'files': duplicate_files,
                'folder_path': str(duplicates_folder)
            })
            
        except Exception as e:
            print(f"Error getting startup duplicates info: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/sequence/<event_name>')
    def get_sequence_for_event(event_name):
        """Get next sequence number for an event"""
        next_seq = config['sequence_numbers'].get(event_name, 0) + 1
        return jsonify({'sequence': next_seq})

    @app.route('/api/sequence/category/<category_name>')
    def get_sequence_for_category(category_name):
        """Get next sequence number for a category (fallback naming)"""
        next_seq = config['category_sequences'].get(category_name, 0) + 1
        return jsonify({'sequence': next_seq})

    @app.route('/api/sequences')
    def get_all_sequences():
        """Get all sequence information"""
        return jsonify({
            'event_sequences': config['sequence_numbers'],
            'category_sequences': config['category_sequences']
        })

    @app.route('/api/session/save', methods=['POST'])
    def save_session_endpoint():
        """Save current session"""
        save_session()
        return jsonify({'success': True})

    @app.route('/api/session/load', methods=['POST'])
    def load_session_endpoint():
        """Load saved session"""
        success = load_session()
        return jsonify({'success': success, 'current_index': config['current_image_index']})

    @app.route('/api/stats')
    def get_stats():
        """Get processing statistics"""
        total_processed = len(config['processed_images'])
        actions = {}
        for item in config['processed_images']:
            action = item['action']
            actions[action] = actions.get(action, 0) + 1
        
        return jsonify({
            'total_images': len(processor.images) if processor else 0,
            'total_processed': total_processed,
            'current_index': config['current_image_index'],
            'actions': actions,
            'categories': config['categories']
        })