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
    'session_file': 'session.json'
}

class ImageProcessor:
    def __init__(self, source_folder):
        self.source_folder = Path(source_folder)
        self.images = []
        self.load_images()
        
    def load_images(self):
        """Load all image files from source folder"""
        if not self.source_folder.exists():
            return
            
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
        self.images = []
        
        for file_path in self.source_folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                self.images.append(file_path)
        
        # Sort by creation time or name
        self.images.sort(key=lambda x: x.stat().st_mtime)
    
    def get_image_info(self, image_path):
        """Get detailed image information"""
        try:
            img = Image.open(image_path)
            
            # Basic info
            info = {
                'path': str(image_path),
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
                'is_blurry': blur_score < 100,  # Threshold for blur
                'is_dark': brightness < 50,
                'is_low_contrast': contrast < 20
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
    
    def find_duplicates(self):
        """Find potential duplicate images"""
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
    
    if not source_folder or not Path(source_folder).exists():
        return jsonify({'error': 'Invalid source folder'}), 400
    
    config['source_folder'] = source_folder
    config['categories'] = categories
    
    # Initialize processor
    processor = ImageProcessor(source_folder)
    
    # Create category folders
    source_path = Path(source_folder)
    for category in categories:
        (source_path / category).mkdir(exist_ok=True)
    
    # Create utility folders
    (source_path / config['deleted_folder']).mkdir(exist_ok=True)
    (source_path / config['backup_folder']).mkdir(exist_ok=True)
    
    # Load session if exists
    load_session()
    
    return jsonify({
        'success': True,
        'total_images': len(processor.images),
        'categories': categories,
        'current_index': config['current_image_index']
    })

@app.route('/api/images/current')
def get_current_image():
    """Get current image information"""
    if not processor or not processor.images:
        return jsonify({'error': 'No images loaded'}), 400
    
    if config['current_image_index'] >= len(processor.images):
        return jsonify({'finished': True})
    
    current_image = processor.images[config['current_image_index']]
    image_info = processor.get_image_info(current_image)
    
    return jsonify({
        'image': image_info,
        'index': config['current_image_index'],
        'total': len(processor.images),
        'progress': (config['current_image_index'] / len(processor.images)) * 100
    })

@app.route('/api/images/file/<path:filename>')
def serve_image(filename):
    """Serve image file"""
    try:
        file_path = Path(config['source_folder']) / filename
        if file_path.exists() and file_path.is_file():
            return send_file(file_path)
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
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
    custom_name = data.get('custom_name', '')
    
    current_image = processor.images[config['current_image_index']]
    source_path = Path(config['source_folder'])
    
    try:
        # Create backup
        backup_path = source_path / config['backup_folder'] / current_image.name
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
            # Move to selected categories
            for category in categories:
                category_path = source_path / category
                
                # Determine filename
                if custom_name:
                    filename = f"{custom_name}{current_image.suffix}"
                else:
                    filename = current_image.name
                
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
            'custom_name': custom_name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Move to next image
        config['current_image_index'] += 1
        
        # Save session
        save_session()
        
        return jsonify({
            'success': True,
            'next_index': config['current_image_index'],
            'total': len(processor.images)
        })
        
    except Exception as e:
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

@app.route('/api/categories', methods=['GET', 'POST'])
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
    """Find duplicate images"""
    if not processor:
        return jsonify({'error': 'No images loaded'}), 400
    
    duplicates = processor.find_duplicates()
    return jsonify({'duplicates': duplicates})

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
