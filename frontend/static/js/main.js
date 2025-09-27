// Main application logic for Image Organizer

// Actions module for all user actions
const actions = {
    // Process current image
    async processCurrentImage() {
        if (selectedCategories.size === 0) {
            showNotification('Please select at least one category', 'warning');
            return;
        }

        try {
            let requestData = {
                action: 'move',
                categories: Array.from(selectedCategories)
            };

            if (useCustomFilename) {
                const customName = document.getElementById('customFilename').value.trim();
                requestData.custom_name = customName;
            } else {
                // Use filename template
                const template = {
                    person_name: document.getElementById('personName').value.trim(),
                    event: document.getElementById('event').value.trim(),
                    date: document.getElementById('date').value.trim(),
                    seq_number: document.getElementById('seqNumber').value.trim()
                };
                requestData.filename_template = template;
            }
            
            const data = await api.processImage(
                requestData.action,
                requestData.categories,
                requestData.filename_template || {},
                requestData.custom_name || ''
            );
            
            if (data && data.success) {
                showNotification(`Moved to ${Array.from(selectedCategories).join(', ')}`, 'success');
                
                // Clear template inputs for next image (but keep event/sequence)
                ui.clearTemplateInputs();
                
                // Update sequence numbers display
                await infoPanel.updateSequenceDetails();
                
                await ui.loadCurrentImage();
            } else {
                showNotification(data?.error || 'Failed to process image', 'error');
            }
        } catch (error) {
            console.error('Error processing image:', error);
            showNotification('Error processing image', 'error');
        }
    },

    // Skip current image
    async skipImage() {
        try {
            const data = await api.skipImage();
            
            if (data && data.success) {
                showNotification('Skipped', 'info');
                await ui.loadCurrentImage();
            }
        } catch (error) {
            console.error('Error skipping image:', error);
            showNotification('Error skipping image', 'error');
        }
    },

    // Delete current image
    async deleteImage() {
        if (!confirm('Are you sure you want to delete this image?')) return;

        try {
            const data = await api.processImage('delete');
            
            if (data && data.success) {
                showNotification('Deleted', 'success');
                await ui.loadCurrentImage();
            } else {
                showNotification(data?.error || 'Failed to delete image', 'error');
            }
        } catch (error) {
            console.error('Error deleting image:', error);
            showNotification('Error deleting image', 'error');
        }
    },

    // Go to previous image
    async previousImage() {
        try {
            const data = await api.previousImage();
            
            if (data && data.success) {
                await ui.loadCurrentImage();
            }
        } catch (error) {
            console.error('Error going to previous image:', error);
            showNotification('Error going to previous image', 'error');
        }
    },

    // Rotate image
    async rotateImage(degrees) {
        try {
            showNotification('Rotating image...', 'info');
            
            const data = await api.rotateImage(degrees);
            
            if (data && data.success) {
                // Force reload the image to show rotation (with cache-busting)
                await ui.loadCurrentImage(true);
                showNotification(`Rotated ${degrees}°`, 'success');
            } else {
                showNotification(data?.error || 'Failed to rotate image', 'error');
            }
        } catch (error) {
            console.error('Error rotating image:', error);
            showNotification('Error rotating image', 'error');
        }
    },

    // Add new category during processing
    async addNewCategory() {
        const input = document.getElementById('newCategoryDynamic');
        const categoryName = input.value.trim();
        
        if (!categoryName) {
            showNotification('Please enter a category name', 'warning');
            return;
        }
        
        if (categories.includes(categoryName)) {
            showNotification('Category already exists', 'warning');
            return;
        }
        
        try {
            console.log('Categories before adding:', categories);
            
            const data = await api.addCategory(categoryName);
            
            if (data && data.success) {
                console.log('Server response categories:', data.categories);
                
                // Update global categories array with server response
                categories = [...data.categories]; // Create new array to ensure reactivity
                window.categories = categories; // Ensure global reference is updated
                
                console.log('Categories after update:', categories);
                
                // Clear the input first
                input.value = '';
                
                // Re-render the categories sidebar with slight delay to ensure state is updated
                setTimeout(() => {
                    ui.renderCategoriesSidebar();
                    // Update category info panel
                    ui.updateCategoryInfo();
                }, 10);
                
                // Show success message
                showNotification(data.message || `Added category: ${categoryName}`, 'success');
                
            } else {
                showNotification(data?.error || 'Failed to add category', 'error');
            }
        } catch (error) {
            console.error('Error adding category:', error);
            showNotification('Error adding category', 'error');
        }
    }
};

// Info panel update functions
const infoPanel = {
    // Update image info panel
    updateImageInfo() {
        if (!currentImage) return;

        const imageDetails = document.getElementById('imageDetails');
        const qualityDetails = document.getElementById('qualityDetails');

        imageDetails.innerHTML = `
            <div class="info-item">
                <span class="info-label">Name:</span>
                <span class="info-value">${currentImage.name}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Size:</span>
                <span class="info-value">${formatFileSize(currentImage.size)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Dimensions:</span>
                <span class="info-value">${currentImage.dimensions}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Format:</span>
                <span class="info-value">${currentImage.format}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Created:</span>
                <span class="info-value">${formatDate(currentImage.created)}</span>
            </div>
        `;

        if (currentImage.quality && !currentImage.quality.error) {
            const quality = currentImage.quality;
            qualityDetails.innerHTML = `
                <div class="info-item">
                    <span class="info-label">Blur Score:</span>
                    <span class="info-value">${Math.round(quality.blur_score)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Brightness:</span>
                    <span class="info-value">${Math.round(quality.brightness)}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Contrast:</span>
                    <span class="info-value">${Math.round(quality.contrast)}</span>
                </div>
            `;
        } else {
            qualityDetails.innerHTML = '<div class="info-item">Quality analysis unavailable</div>';
        }
    },

    // Update image overlay
    updateImageOverlay() {
        if (!currentImage) return;

        const overlay = document.getElementById('imageOverlay');
        overlay.textContent = currentImage.name;
    },

    // Update quality indicators
    updateQualityIndicators() {
        if (!currentImage || !currentImage.quality || currentImage.quality.error) return;

        const indicators = document.getElementById('qualityIndicators');
        const quality = currentImage.quality;
        const badges = [];

        if (quality.is_blurry) {
            badges.push('<span class="quality-badge danger">Blurry</span>');
        }
        if (quality.is_dark) {
            badges.push('<span class="quality-badge warning">Dark</span>');
        }
        if (quality.is_low_contrast) {
            badges.push('<span class="quality-badge warning">Low Contrast</span>');
        }

        indicators.innerHTML = badges.join('');
    },

    // Update statistics
    async updateStats() {
        try {
            const data = await api.getStats();
            
            stats.innerHTML = `
                <span>📁 ${data.total_images} images</span>
                <span>✅ ${data.total_processed} processed</span>
            `;

            // Update all info panels
            await this.updateSequenceDetails();
            await this.updateDuplicateInfo();
            this.updateCategoryInfo();
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    },

    // Update duplicate information
    async updateDuplicateInfo() {
        try {
            const data = await api.getStartupDuplicatesInfo();
            const duplicateInfo = document.getElementById('duplicateInfo');
            
            if (data && data.folder_exists && data.count > 0) {
                duplicateInfo.innerHTML = `
                    <div class="info-item">
                        <span class="info-label">Found:</span>
                        <span class="info-value">${data.count}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Status:</span>
                        <span class="info-value">Moved to folder</span>
                    </div>
                    <div class="info-item" style="margin-top: 8px;">
                        <span class="info-label">Location:</span>
                        <span class="info-value" style="word-break: break-word; font-size: 11px;">duplicates_startup/</span>
                    </div>
                `;
            } else {
                duplicateInfo.innerHTML = `
                    <div class="info-item">
                        <span class="info-label">Status:</span>
                        <span class="info-value">✅ None found</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error updating duplicate info:', error);
            const duplicateInfo = document.getElementById('duplicateInfo');
            if (duplicateInfo) {
                duplicateInfo.innerHTML = '<div class="info-item">Error loading duplicate info</div>';
            }
        }
    },

    // Update category information
    updateCategoryInfo() {
        const categoryInfo = document.getElementById('categoryInfo');
        
        if (categories && categories.length > 0) {
            const selectedCount = selectedCategories.size;
            const totalCount = categories.length;
            
            let content = `
                <div class="info-item">
                    <span class="info-label">Total:</span>
                    <span class="info-value">${totalCount}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Selected:</span>
                    <span class="info-value">${selectedCount}</span>
                </div>
            `;
            
            if (selectedCount > 0) {
                const selectedList = Array.from(selectedCategories).join(', ');
                content += `
                    <div class="info-item" style="margin-top: 8px;">
                        <span class="info-label">Current:</span>
                        <span class="info-value" style="word-break: break-word;">${selectedList}</span>
                    </div>
                `;
            }
            
            categoryInfo.innerHTML = content;
        } else {
            categoryInfo.innerHTML = '<div class="info-item">No categories loaded</div>';
        }
    },

    // Update sequence details
    async updateSequenceDetails() {
        try {
            const data = await api.getAllSequences();
            const sequenceDetails = document.getElementById('sequenceDetails');
            
            let content = '';
            
            // Event sequences
            if (data && data.event_sequences && Object.keys(data.event_sequences).length > 0) {
                content += '<div style="margin-bottom: 10px;"><strong>📅 Events:</strong></div>';
                const eventItems = Object.entries(data.event_sequences)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([event, count]) => `
                        <div class="info-item">
                            <span class="info-label">${event}:</span>
                            <span class="info-value">Next: ${count + 1}</span>
                        </div>
                    `).join('');
                content += eventItems;
            }
            
            // Category sequences (fallback naming)
            if (data && data.category_sequences && Object.keys(data.category_sequences).length > 0) {
                if (content) content += '<div style="margin: 10px 0; border-top: 1px solid var(--border); padding-top: 10px;"></div>';
                content += '<div style="margin-bottom: 10px;"><strong>📁 Categories:</strong></div>';
                const categoryItems = Object.entries(data.category_sequences)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([category, count]) => `
                        <div class="info-item">
                            <span class="info-label">${category}:</span>
                            <span class="info-value">Next: ${count + 1}</span>
                        </div>
                    `).join('');
                content += categoryItems;
            }
            
            if (content) {
                sequenceDetails.innerHTML = content;
            } else {
                sequenceDetails.innerHTML = '<div class="info-item">No sequences yet</div>';
            }
        } catch (error) {
            console.error('Error updating sequence details:', error);
            const sequenceDetails = document.getElementById('sequenceDetails');
            if (sequenceDetails) {
                sequenceDetails.innerHTML = '<div class="info-item">Error loading sequences</div>';
            }
        }
    }
};

// Global functions for backwards compatibility
function toggleTheme() {
    ui.toggleTheme();
}

function loadCategoriesFromDirectory() {
    ui.loadCategoriesFromDirectory();
}

function useDefaultCategories() {
    ui.useDefaultCategories();
}

function loadCategoriesFromDirectoryDuringProcessing() {
    ui.loadCategoriesFromDirectoryDuringProcessing();
}

function toggleCustomFilename() {
    ui.toggleCustomFilename();
}

function clearAllTemplateInputs() {
    ui.clearAllTemplateInputs();
}

function processCurrentImage() {
    actions.processCurrentImage();
}

function skipImage() {
    actions.skipImage();
}

function deleteImage() {
    actions.deleteImage();
}

function previousImage() {
    actions.previousImage();
}

function rotateImage(degrees) {
    actions.rotateImage(degrees);
}

function addNewCategory() {
    actions.addNewCategory();
}

// Update UI methods to use info panel
ui.updateImageInfo = infoPanel.updateImageInfo;
ui.updateImageOverlay = infoPanel.updateImageOverlay;
ui.updateQualityIndicators = infoPanel.updateQualityIndicators;
ui.updateStats = infoPanel.updateStats;
ui.updateCategoryInfo = infoPanel.updateCategoryInfo;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    ui.init();
    keyboard.setupKeyboardShortcuts();
    
    // Click to zoom functionality
    document.getElementById('mainImage').addEventListener('click', ui.toggleZoom);
});

// Export for global use
window.actions = actions;
window.infoPanel = infoPanel;