# Image Organizer - Imagify

A modern web-based image organization tool that helps you efficiently sort, categorize, and manage large collections of images with smart features like duplicate detection, quality assessment, and automated filename generation.

![Image Organizer Preview](https://img.shields.io/badge/Status-Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.7+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3+-orange)

---

## ✨ Features

- **Smart Image Processing**: Automatic quality assessment (blur, brightness, contrast detection)
- **Duplicate Detection**: Finds and manages duplicate images automatically
- **Flexible Categorization**: Create custom categories or load from existing folders
- **Template-Based Naming**: Intelligent filename generation with event-based sequencing
- **Keyboard Shortcuts**: Efficient navigation and processing with hotkeys
- **Dark/Light Theme**: Modern UI with theme switching
- **Image Rotation**: Built-in image rotation capabilities
- **Progress Tracking**: Visual progress indicators and statistics
- **Session Management**: Resume where you left off

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### 1. Clone or Download
```bash
git clone https://github.com/cl0udstar/image-organiser.git
cd image-organiser
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Open in Browser
Visit `http://localhost:5000` and start organising!

---

## 📁 Project Structure

```
📁 image-organiser/
├── 📁 backend/
│   ├── image_processor.py         # Image processing logic
│   ├── api_routes.py              # API route handlers
│   ├── config.py                  # Configuration settings
│   └── utils.py                   # Utility functions
├── 📁 frontend/
│   ├── 📁 static/
│   │   ├── 📁 css/
│   │   │   ├── main.css           # Main styles
│   │   │   ├── components.css     # Component styles
│   │   │   └── themes.css         # Theme-related styles
│   │   ├── 📁 js/
│   │   │   ├── main.js            # Main application logic
│   │   │   ├── api.js             # API communication
│   │   │   ├── ui.js              # UI management
│   │   │   └── keyboard.js        # Keyboard shortcuts
│   │   └── 📁 images/
│   └── 📁 templates/
│       └── index.html             # Main HTML template
├── app.py                         # Main Flask application
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1-9` | Select category folders |
| `D` | Delete current image |
| `S` | Skip to next image |
| `←` | Go to previous image |
| `Enter` | Process with selected categories |
| `Space` | Zoom in/out on image |

---

## Usage

### Initial Setup

1. **Source Folder**: Enter the full path to your images folder
2. **Duplicate Detection**: Toggle automatic duplicate detection (recommended)
3. **Categories**: 
   - Click "Load from Folders" to scan existing directories
   - Click "Use Defaults" for preset categories
   - Or manually add custom categories
4. Click "Start Organising" to begin

### Processing Images

#### Category Selection
- Click category buttons or use number keys (1-9)
- Multiple categories can be selected for copying to multiple folders

#### Filename Templates
- **Person Name**: Name of person in image
- **Event**: Event name (auto-increments sequence per event)
- **Date**: Date in YYYYMMDD format (auto-fills current date)
- **Sequence Number**: Auto-generated based on event

#### Quick Actions
- **Skip**: Skip current image without processing
- **Delete**: Move image to deleted folder
- **Previous**: Go back to previous image
- **Rotate**: Rotate image in 90°, 180°, or 270° increments

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| 1-9 | Select category |
| D | Delete image |
| S | Skip image |
| ← | Previous image |
| Enter | Process current image |
| Space | Zoom in/out |
| Ctrl+R | Rotate 90° |
| Shift+R | Refresh categories |
| Ctrl+T | Toggle theme |

### Filename Generation

#### Template Mode
When template fields are filled, files are named as:
`PersonName_Event_Date_SequenceNumber.jpg`

Example: `John_Birthday_20241225_001.jpg`

#### Fallback Mode
When no template fields are filled, uses category-based naming:
`CategoryName_001.jpg`

Example: `Family_001.jpg`

---

## Features in Detail

### Duplicate Detection
- Uses perceptual hashing to find exact duplicates
- Moves duplicates to `duplicates_startup` folder
- Preserves original files in main directory
- Provides detailed duplicate information

### Quality Assessment
- **Blur Detection**: Identifies blurry images using Laplacian variance
- **Brightness Analysis**: Detects overly dark or bright images
- **Contrast Analysis**: Identifies low-contrast images
- Visual indicators overlay on images

### Session Management
- Automatically saves progress to `session.json`
- Resume processing from where you left off
- Tracks processed images and statistics

### Backup System
- Creates backups before any file operations
- Rotation backups stored separately
- Easy recovery of modified files

---

## Configuration

### Folder Structure Created
- `deleted/` - Deleted images
- `backup/` - Backup copies
- `duplicates_startup/` - Detected duplicates
- Category folders as specified

### File Types Supported
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- GIF (.gif)
- WebP (.webp)

---

## API Reference

### Setup
- `POST /api/setup` - Initialize application with source folder and categories

### Image Operations
- `GET /api/images/current` - Get current image information
- `POST /api/images/process` - Process current image (move/delete)
- `POST /api/images/skip` - Skip current image
- `POST /api/images/previous` - Go to previous image
- `POST /api/images/rotate` - Rotate current image

### Category Management
- `GET /api/categories` - Get current categories
- `POST /api/categories` - Update categories
- `GET /api/categories/from-directory` - Load categories from folders

### Sequence Management
- `GET /api/sequence/{event_name}` - Get next sequence for event
- `GET /api/sequences` - Get all sequence information

### Statistics
- `GET /api/stats` - Get processing statistics
- `GET /api/duplicates/startup-info` - Get duplicate detection info

---

## Troubleshooting

### Common Issues

1. **Images not loading**
   - Check source folder path
   - Ensure proper file permissions
   - Verify supported file formats

2. **Duplicate detection not working**
   - Ensure OpenCV is properly installed
   - Check available memory for large image collections

3. **Categories not saving**
   - Verify write permissions in source folder
   - Check for proper Flask session configuration

### Performance Tips

- Close other applications when processing large collections
- Use SSD storage for better performance
- Process images in batches for very large collections

---

## Development

### Backend Architecture
- **Flask**: Web framework and API server
- **PIL/Pillow**: Image processing and EXIF data
- **OpenCV**: Quality assessment and computer vision
- **NumPy**: Numerical operations

### Frontend Architecture
- **Vanilla JavaScript**: No framework dependencies
- **Modular Design**: Separated concerns (API, UI, Keyboard)
- **CSS Grid/Flexbox**: Responsive layout
- **CSS Custom Properties**: Theme system

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🆘 Support

Having issues? Check the troubleshooting section in the setup guide or open an issue on GitHub.

---

**Made with ❤️ by cl0udstar for better photo organization**
