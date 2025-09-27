#!/usr/bin/env python3
"""
Image processing and analysis functionality for Image Organizer
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from PIL import Image, ExifTags

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
