#!/usr/bin/env python3
"""
Image Organizer - Flask Backend
Modern web-based image organization tool
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ExifTags
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# Global configuration
config = {
    'source_folder': '',
    'categories': ['Person1', 'Person2', 'Person3', 'Events', 'Family', 'Friends'],
    'current_image_index': 0,
    'processed_images': [],
    'deleted_folder': 'deleted',
    'backup_folder': 'backup',
    'session_file': 'session.json',
    'current_rotation': 0,
    'sequence_numbers': {},  # Track sequence numbers per event
    'category_sequences': {}  # Track sequence numbers per category (for fallback naming)
}

class ImageProcessor:
    def __init__(self, source_folder):
        self.source_folder = Path(source_folder)
        self.images = []
        self.load_images()
        
    def load_images(self):
        """Load all image files from source folder"""
        if not self.source_folder.exists():
            print(f"Source folder does not exist: {self.source_folder}")
            return
            
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
        self.images = []
        
        try:
            for file_path in self.source_folder.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    self.images.append(file_path)
            
            # Sort by creation time or name
            self.images.sort(key=lambda x: x.stat().st_mtime)
            print(f"Found {len(self.images)} images in {self.source_folder}")
        except Exception as e:
            print(f"Error loading images: {e}")
            self.images = []
    
    def get_image_info(self, image_path):
        """Get detailed image information"""
        try:
            img = Image.open(image_path)
            
            # Get relative path from source folder for serving
            relative_path = image_path.relative_to(self.source_folder)
            
            # Basic info
            info = {
                'path': str(image_path),
                'relative_path': str(relative_path).replace('\\', '/'),  # Use forward slashes for URLs
                'name': image_path.name,
                'size': image_path.stat().st_size,
                'dimensions': f"{img.width}x{img.height}",
                'format': img.format,
                'mode': img.mode,
                'created': datetime.fromtimestamp(image_path.stat().st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(image_path.stat().st_mtime).isoformat()
            }
            
            # EXIF data
            try:
                exif = img._getexif()
                if exif:
                    info['exif'] = {}
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        info['exif'][tag] = str(value)
            except:
                info['exif'] = {}
            
            # Quality assessment
            info['quality'] = self.assess_image_quality(image_path)
            
            return info
        except Exception as e:
            print(f"Error getting image info for {image_path}: {e}")
            return {'error': str(e), 'path': str(image_path), 'name': image_path.name}
    
    def assess_image_quality(self, image_path):
        """Assess image quality (blur, brightness, etc.)"""
        try:
            # Load image with OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                return {'error': 'Could not load image'}
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Blur detection using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Brightness analysis
            brightness = np.mean(gray)
            
            # Contrast analysis
            contrast = gray.std()
            
            return {
                'blur_score': float(blur_score),
                'brightness': float(brightness),
                'contrast': float(contrast),
                'is_blurry': bool(blur_score < 100),  # Convert numpy bool to Python bool
                'is_dark': bool(brightness < 50),
                'is_low_contrast': bool(contrast < 20)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_image_hash(self, image_path):
        """Calculate perceptual hash for duplicate detection"""
        try:
            img = Image.open(image_path)
            img = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if pixel >= avg else '0' for pixel in pixels)
            return bits
        except:
            return None
    
    def rotate_image(self, image_path, degrees):
        """Rotate image by specified degrees"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Rotate image
                rotated = img.rotate(-degrees, expand=True)  # Negative for clockwise rotation
                
                # Save rotated image (overwrite original)
                rotated.save(image_path, quality=95, optimize=True)
                return True
        except Exception as e:
            print(f"Error rotating image {image_path}: {e}")
            return False
    def find_duplicates(self):
        """Find potential duplicate images (for manual review)"""
        hashes = {}
        duplicates = []
        
        for img_path in self.images:
            img_hash = self.calculate_image_hash(img_path)
            if img_hash:
                if img_hash in hashes:
                    duplicates.append({
                        'original': str(hashes[img_hash]),
                        'duplicate': str(img_path),
                        'similarity': 'exact'
                    })
                else:
                    hashes[img_hash] = img_path
        
        return duplicates

# Global processor instance
processor = None

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

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
            duplicates_count, duplicates_info = processor.handle_duplicates_on_startup()
        
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
        def make_serializable(obj):
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
            return send_file(str(file_path))
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
        backup_path = source_path / config['backup_folder'] / current_image.name
        counter = 1
        while backup_path.exists():
            stem = current_image.stem
            suffix = current_image.suffix
            backup_path = source_path / config['backup_folder'] / f"{stem}_backup_{counter}{suffix}"
            counter += 1
        shutil.copy2(current_image, backup_path)
        
        if action == 'delete':
            # Move to deleted folder
            deleted_path = source_path / config['deleted_folder'] / current_image.name
            counter = 1
            while deleted_path.exists():
                stem = current_image.stem
                suffix = current_image.suffix
                deleted_path = source_path / config['deleted_folder'] / f"{stem}_{counter}{suffix}"
                counter += 1
            
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
                counter = 1
                while destination.exists():
                    stem = Path(filename).stem
                    suffix = Path(filename).suffix
                    destination = category_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
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
        backup_path = source_path / config['backup_folder'] / f"rotation_{current_image.name}"
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
def manage_categories():
    """Get or update categories"""
    if request.method == 'GET':
        return jsonify({'categories': config['categories']})
    
    data = request.json
    new_categories = data.get('categories', [])
    config['categories'] = new_categories
    
    # Create new category folders
    if config['source_folder']:
        source_path = Path(config['source_folder'])
        for category in new_categories:
            (source_path / category).mkdir(exist_ok=True)
    
    save_session()
    return jsonify({'success': True, 'categories': config['categories']})

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

if __name__ == '__main__':
    print("🖼️  Image Organizer Server Starting...")
    print("📁 Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
