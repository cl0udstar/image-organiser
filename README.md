# 📸 Image Organizer

A modern, web-based tool for organizing and categorizing large photo collections with intelligent features and a clean interface.

![Image Organizer Preview](https://img.shields.io/badge/Status-Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.7+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3+-orange)

## ✨ Features

- **🎯 Smart Organization**: Easily categorize images into custom folders
- **⚡ Keyboard Shortcuts**: Lightning-fast processing with hotkeys
- **🔍 Quality Assessment**: Automatic blur, brightness, and contrast detection
- **📊 Progress Tracking**: Visual progress bars and processing statistics
- **💾 Session Recovery**: Resume processing from where you left off
- **🖼️ Modern Viewer**: Zoom, pan, and navigate images effortlessly
- **📱 Responsive Design**: Works perfectly on desktop and mobile
- **🔄 Backup System**: Automatic backups before any changes

---

## 🚀 Quick Start

### 1. Clone or Download
```bash
git clone https://github.com/yourusername/image-organizer.git
cd image-organizer
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
Visit `http://localhost:5000` and start organizing!

---

## 📁 Project Structure

```
image-organizer/
├── app.py              # Flask backend server
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Web interface
└── README.md
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

## 🎯 How to Use

1. **Setup**: Enter your source folder path and customize categories
2. **Review**: Examine each image with quality indicators
3. **Select**: Choose destination categories (supports multiple selection)
4. **Process**: Move images to selected folders with optional custom naming
5. **Continue**: Automatic progression to next image

---

## 🛠️ Advanced Features

### Quality Assessment
- **Blur Detection**: Automatically identifies blurry images
- **Brightness Analysis**: Flags overly dark or bright images
- **Contrast Evaluation**: Detects low-contrast photos

### Multi-Category Assignment
- Move single images to multiple folders
- Custom filename templates
- Automatic conflict resolution

### Session Management
- Automatic progress saving
- Resume interrupted sessions
- Processing history tracking

---

## 🎨 Customization

### Adding Categories
- Pre-define categories in setup
- Add new categories during processing
- Hierarchical organization support

### Styling
Modify CSS variables in `templates/index.html`:
```css
:root {
    --primary: #6366f1;     /* Accent color */
    --secondary: #f1f5f9;   /* Background */
    --radius: 8px;          /* Border radius */
}
```

---

## 📋 Requirements

- Python 3.7+
- Modern web browser
- Local file system access

---

## 🔧 Dependencies

- **Flask**: Web framework
- **Pillow**: Image processing
- **OpenCV**: Quality assessment
- **NumPy**: Numerical operations

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
