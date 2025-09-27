// UI management functions for Image Organizer

// Global state
let currentImage = null;
let selectedCategories = new Set();
let categories = []; // Start with empty categories
let isZoomed = false;
let useCustomFilename = false;
let isDarkMode = localStorage.getItem('darkMode') === 'true';

// DOM elements
const setupScreen = document.getElementById('setupScreen');
const mainInterface = document.getElementById('mainInterface');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const stats = document.getElementById('stats');
const shortcutsHelp = document.getElementById('shortcutsHelp');

// UI Management Functions
const ui = {
    // Initialize UI
    init() {
        this.initializeTheme();
        this.initializeSetup();
        this.setupTemplatePreview();
        this.initializeDuplicateDetection();
        
        // Show shortcuts help after 3 seconds
        setTimeout(() => {
            shortcutsHelp.classList.add('show');
            setTimeout(() => shortcutsHelp.classList.remove('show'), 5000);
        }, 3000);
    },

    // Theme management
    initializeTheme() {
        if (isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.getElementById('themeIcon').textContent = '☀️';
        }
    },

    toggleTheme() {
        isDarkMode = !isDarkMode;
        localStorage.setItem('darkMode', isDarkMode);
        
        if (isDarkMode) {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.getElementById('themeIcon').textContent = '☀️';
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.getElementById('themeIcon').textContent = '🌙';
        }
    },

    // Setup form initialization
    initializeSetup() {
        const categoriesContainer = document.getElementById('categoriesContainer');
        const newCategoryInput = document.getElementById('newCategory');
        const setupForm = document.getElementById('setupForm');

        // Render initial categories
        this.renderCategoriesInSetup();

        // Add category on Enter key
        newCategoryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const value = e.target.value.trim();
                if (value && !categories.includes(value)) {
                    categories.push(value);
                    this.renderCategoriesInSetup();
                    e.target.value = '';
                }
            }
        });

        // Handle form submission
        setupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sourceFolder = document.getElementById('sourceFolder').value.trim();
            if (sourceFolder) {
                const submitBtn = e.target.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                
                // Show loading state
                submitBtn.innerHTML = '⏳ Starting...';
                submitBtn.disabled = true;
                
                try {
                    await this.setupApplication(sourceFolder, categories);
                } finally {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }
        });
    },

    // Render categories in setup screen
    renderCategoriesInSetup() {
        const categoriesContainer = document.getElementById('categoriesContainer');
        if (categories.length === 0) {
            categoriesContainer.innerHTML = '<div style="color: var(--text-light); font-style: italic; padding: 10px; text-align: center;">No categories yet. Use "Load from Folders" or "Use Defaults"</div>';
        } else {
            categoriesContainer.innerHTML = categories.map(cat => `
                <div class="category-tag">
                    ${cat}
                    <span class="remove" onclick="ui.removeCategory('${cat}')">×</span>
                </div>
            `).join('');
        }
    },

    // Remove category
    removeCategory(categoryName) {
        categories = categories.filter(cat => cat !== categoryName);
        this.renderCategoriesInSetup();
    },

    // Use default categories
    useDefaultCategories() {
        categories = ['Person1', 'Person2', 'Person3', 'Events', 'Family', 'Friends'];
        this.renderCategoriesInSetup();
        showNotification('Using default categories', 'info');
    },

    // Load categories from directory
    async loadCategoriesFromDirectory() {
        const sourceFolder = document.getElementById('sourceFolder').value.trim();
        
        if (!sourceFolder) {
            showNotification('Please enter a source folder path first', 'warning');
            return;
        }
        
        try {
            showNotification('Scanning directory for folders...', 'info');
            
            // Temporarily set the source folder for the API call
            const tempSetupResult = await api.setup(sourceFolder, []);
            
            if (!tempSetupResult || tempSetupResult.error) {
                showNotification(tempSetupResult?.error || 'Invalid folder path', 'error');
                return;
            }
            
            const data = await api.getCategoriesFromDirectory();
            
            if (data && data.categories && data.categories.length > 0) {
                categories = data.categories;
                this.renderCategoriesInSetup();
                
                // Show detailed feedback
                const folderList = data.categories.length > 5 
                    ? data.categories.slice(0, 5).join(', ') + ` and ${data.categories.length - 5} more`
                    : data.categories.join(', ');
                
                showNotification(`📁 Found ${data.categories.length} folders: ${folderList}`, 'success');
            } else {
                showNotification('📂 No existing folders found - you can start with defaults or create new ones', 'warning');
                categories = [];
                this.renderCategoriesInSetup();
            }
        } catch (error) {
            console.error('Error loading categories from directory:', error);
            showNotification('Error scanning directory for folders', 'error');
        }
    },

    // Load categories from directory during processing
    async loadCategoriesFromDirectoryDuringProcessing() {
        try {
            const data = await api.getCategoriesFromDirectory();
            
            if (data && data.categories && data.categories.length > 0) {
                // Update global categories but preserve current selections
                const previousSelections = Array.from(selectedCategories);
                categories = data.categories;
                this.renderCategoriesSidebar();
                
                // Restore selections that still exist
                selectedCategories.clear();
                previousSelections.forEach(cat => {
                    if (categories.includes(cat)) {
                        selectedCategories.add(cat);
                        const btn = document.querySelector(`[data-category="${cat}"]`);
                        if (btn) btn.classList.add('selected');
                    }
                });
                
                showNotification(`📁 Refreshed: Found ${data.categories.length} folders`, 'success');
                this.updateTemplatePreview();
            } else {
                showNotification('No folders found in directory', 'warning');
            }
        } catch (error) {
            console.error('Error loading categories from directory:', error);
            showNotification('Error scanning directory for folders', 'error');
        }
    },

    // Initialize duplicate detection
    initializeDuplicateDetection() {
        const duplicateCheckbox = document.getElementById('handleDuplicates');
        const duplicateBox = document.getElementById('duplicateDetectionBox');

        duplicateCheckbox.addEventListener('change', function() {
            if (this.checked) {
                duplicateBox.classList.remove('disabled');
                duplicateBox.classList.add('enabled');
            } else {
                duplicateBox.classList.add('disabled');
                duplicateBox.classList.remove('enabled');
            }
        });

        // Set initial state
        if (duplicateCheckbox.checked) {
            duplicateBox.classList.add('enabled');
        }
    },

    // Setup application
    async setupApplication(sourceFolder, categories) {
        try {
            const handleDuplicates = document.getElementById('handleDuplicates').checked;
            
            if (handleDuplicates) {
                showNotification('🔍 Setting up and detecting duplicates...', 'info');
            } else {
                showNotification('🔍 Setting up...', 'info');
            }
            
            const data = await api.setup(sourceFolder, categories, handleDuplicates);
            
            if (data && data.success) {
                setupScreen.style.display = 'none';
                mainInterface.style.display = 'grid';
                
                // Update global categories
                window.categories = categories;
                
                // Render categories in sidebar
                this.renderCategoriesSidebar();
                
                // Show duplicate detection results
                if (data.duplicates_found > 0) {
                    const duplicateMessage = `🎯 Found ${data.duplicates_found} duplicates out of ${data.initial_count} images. Duplicates moved to "duplicates_startup" folder. Processing ${data.total_images} unique images.`;
                    showNotification(duplicateMessage, 'success', 8000);
                    console.log('Duplicate detection results:', data.duplicates_info);
                } else if (data.initial_count > 0) {
                    showNotification(`✅ No duplicates found! Processing ${data.total_images} unique images.`, 'success');
                }
                
                // Load first image
                await this.loadCurrentImage();
                
                if (data.duplicates_found === 0) {
                    showNotification(`🚀 Ready! Found ${data.total_images} images`, 'success');
                }
            } else {
                showNotification(data?.error || 'Setup failed', 'error');
            }
        } catch (error) {
            console.error('Setup error:', error);
            showNotification('Connection error. Make sure the server is running.', 'error');
        }
    },

    // Render categories in sidebar
    renderCategoriesSidebar() {
        const categoriesList = document.getElementById('categoriesList');
        
        // Store current selections before re-rendering
        const currentSelections = Array.from(selectedCategories);
        
        console.log('Rendering categories:', categories);
        console.log('Current selections:', currentSelections);
        
        categoriesList.innerHTML = categories.map((cat, index) => `
            <button class="category-btn${currentSelections.includes(cat) ? ' selected' : ''}" 
                    onclick="ui.toggleCategory('${cat}')" 
                    data-category="${cat}">
                📁 ${cat} <span class="hotkey">${index + 1}</span>
            </button>
        `).join('');
        
        // Update category info when categories are rendered
        this.updateCategoryInfo();
        
        console.log('Categories rendered successfully. Total:', categories.length);
    },

    // Toggle category selection
    toggleCategory(categoryName) {
        const btn = document.querySelector(`[data-category="${categoryName}"]`);
        
        if (selectedCategories.has(categoryName)) {
            selectedCategories.delete(categoryName);
            btn.classList.remove('selected');
        } else {
            selectedCategories.add(categoryName);
            btn.classList.add('selected');
        }
        
        // Update preview when category selection changes
        this.updateTemplatePreview();
        // Update category info in the info panel
        this.updateCategoryInfo();
    },

    // Load current image
    async loadCurrentImage(forceReload = false) {
        try {
            const loadingSpinner = document.getElementById('loadingSpinner');
            const mainImage = document.getElementById('mainImage');
            
            loadingSpinner.style.display = 'flex';
            mainImage.style.display = 'none';

            const data = await api.getCurrentImage();

            if (data && data.finished) {
                showNotification('All images processed! 🎉', 'success');
                return;
            }

            if (data && data.image) {
                currentImage = data.image;
                
                // Update progress
                const progress = Math.round(data.progress);
                progressFill.style.width = `${progress}%`;
                progressText.textContent = `${data.index + 1} of ${data.total} (${progress}%)`;
                
                // Update stats
                await this.updateStats();
                
                // Load image - use relative path for better handling
                const imagePath = data.image.relative_path || data.image.name;
                let imageUrl = api.getImageUrl(imagePath);
                
                // Add cache-busting parameter if forcing reload (after rotation)
                if (forceReload) {
                    imageUrl += `?t=${Date.now()}`;
                }
                
                mainImage.src = imageUrl;
                mainImage.onload = () => {
                    loadingSpinner.style.display = 'none';
                    mainImage.style.display = 'block';
                    this.updateImageInfo();
                    this.updateImageOverlay();
                    this.updateQualityIndicators();
                };
                
                // Reset zoom and selections
                isZoomed = false;
                mainImage.classList.remove('zoomed');
                selectedCategories.clear();
                document.querySelectorAll('.category-btn').forEach(btn => btn.classList.remove('selected'));
                document.getElementById('customFilename').value = '';
                
                // Update preview with cleared state
                this.updateTemplatePreview();
            }
        } catch (error) {
            console.error('Error loading image:', error);
            showNotification('Error loading image', 'error');
        }
    },

    // Setup template preview
    setupTemplatePreview() {
        const inputs = ['personName', 'event', 'date', 'seqNumber'];
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => this.updateTemplatePreview());
            }
        });
        
        // Special handling for event field to auto-update sequence
        const eventInput = document.getElementById('event');
        if (eventInput) {
            eventInput.addEventListener('blur', () => this.updateSequenceForEvent());
            eventInput.addEventListener('input', this.debounce(() => this.updateSequenceForEvent(), 500));
        }
    },

    // Update sequence for event
    async updateSequenceForEvent() {
        const eventName = document.getElementById('event').value.trim();
        const seqInput = document.getElementById('seqNumber');
        
        if (eventName && seqInput) {
            try {
                // Show loading state
                const originalPlaceholder = seqInput.placeholder;
                seqInput.placeholder = 'Loading...';
                seqInput.style.background = '#f0f0f0';
                
                const data = await api.getSequenceForEvent(eventName);
                
                if (data && data.sequence) {
                    seqInput.value = data.sequence.toString().padStart(3, '0');
                    seqInput.style.background = '#e8f5e8';
                    this.updateTemplatePreview();
                    
                    // Reset background after a moment
                    setTimeout(() => {
                        seqInput.style.background = '#f8f9fa';
                    }, 1000);
                }
                
                seqInput.placeholder = originalPlaceholder;
            } catch (error) {
                console.error('Error getting sequence number:', error);
                if (!seqInput.value) {
                    seqInput.value = '001';
                    this.updateTemplatePreview();
                }
                seqInput.style.background = '#f8f9fa';
                seqInput.placeholder = 'Auto';
            }
        } else if (!eventName && seqInput) {
            seqInput.value = '';
            seqInput.style.background = '#f8f9fa';
            this.updateTemplatePreview();
        }
    },

    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Update template preview
    updateTemplatePreview() {
        const personName = document.getElementById('personName').value.trim();
        const event = document.getElementById('event').value.trim();
        const date = document.getElementById('date').value.trim();
        const seqNumber = document.getElementById('seqNumber').value.trim();
        
        // Check if any template fields have data
        const hasTemplateData = personName || event || date || seqNumber;
        
        if (hasTemplateData) {
            // Use template preview
            const parts = [];
            if (personName) parts.push(personName);
            if (event) parts.push(event);
            if (date) parts.push(date);
            if (seqNumber) parts.push(seqNumber);
            
            const preview = parts.length > 0 ? parts.join('_') + '.jpg' : 'filename.jpg';
            document.getElementById('templatePreview').innerHTML = `
                <span style="color: var(--success);">Template: ${preview}</span>
            `;
        } else {
            // Show fallback preview
            const selectedCats = Array.from(selectedCategories);
            if (selectedCats.length > 0) {
                this.updateFallbackPreview(selectedCats[0]);
            } else {
                document.getElementById('templatePreview').innerHTML = `
                    <span style="color: var(--text-light);">Select a category to see fallback naming</span>
                `;
            }
        }
    },

    // Update fallback preview
    async updateFallbackPreview(categoryName) {
        try {
            const data = await api.getSequenceForCategory(categoryName);
            
            if (data && data.sequence) {
                const fallbackName = `${categoryName}_${data.sequence.toString().padStart(3, '0')}.jpg`;
                document.getElementById('templatePreview').innerHTML = `
                    <span style="color: var(--warning);">📁 Fallback: ${fallbackName}</span>
                `;
            }
        } catch (error) {
            console.error('Error getting fallback preview:', error);
            document.getElementById('templatePreview').innerHTML = `
                <span style="color: var(--warning);">📁 Fallback: ${categoryName}_001.jpg</span>
            `;
        }
    },

    // Toggle zoom
    toggleZoom() {
        const mainImage = document.getElementById('mainImage');
        isZoomed = !isZoomed;
        
        if (isZoomed) {
            mainImage.classList.add('zoomed');
        } else {
            mainImage.classList.remove('zoomed');
        }
    },

    // Toggle custom filename
    toggleCustomFilename() {
        useCustomFilename = !useCustomFilename;
        const customInput = document.getElementById('customFilename');
        const templateDiv = document.querySelector('.filename-template');
        
        if (useCustomFilename) {
            customInput.style.display = 'block';
            templateDiv.style.display = 'none';
        } else {
            customInput.style.display = 'none';
            templateDiv.style.display = 'block';
        }
    },

    // Clear template inputs
    clearTemplateInputs() {
        // Clear most fields but keep event and sequence for continuity
        document.getElementById('personName').value = '';
        document.getElementById('date').value = '';
        document.getElementById('customFilename').value = '';
        this.updateTemplatePreview();
    },

    // Clear all template inputs
    clearAllTemplateInputs() {
        document.getElementById('personName').value = '';
        document.getElementById('event').value = '';
        document.getElementById('date').value = '';
        document.getElementById('seqNumber').value = '';
        document.getElementById('customFilename').value = '';
        this.updateTemplatePreview();
    }
};

// Tooltip functions
function showTooltip(element) {
    const tooltip = element.querySelector('.info-tooltip');
    if (tooltip) {
        tooltip.classList.add('show');
    }
}

function hideTooltip(element) {
    const tooltip = element.querySelector('.info-tooltip');
    if (tooltip) {
        tooltip.classList.remove('show');
    }
}

// Utility functions
function formatFileSize(bytes) {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString();
}

function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, duration);
}

// Export for global use
window.ui = ui;
window.showNotification = showNotification;