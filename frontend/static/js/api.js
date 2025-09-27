// API communication module for Image Organizer

// API base URL
const API_BASE = 'http://localhost:5000/api';

// API communication functions
const api = {
    // Setup application
    async setup(sourceFolder, categories, handleDuplicates = true) {
        const response = await fetch(`${API_BASE}/setup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                source_folder: sourceFolder, 
                categories: categories,
                handle_duplicates: handleDuplicates
            })
        });
        return await response.json();
    },

    // Get current image
    async getCurrentImage() {
        const response = await fetch(`${API_BASE}/images/current`);
        return await response.json();
    },

    // Process current image
    async processImage(action, categories = [], filenameTemplate = {}, customName = '') {
        const requestData = {
            action: action,
            categories: categories
        };

        if (customName) {
            requestData.custom_name = customName;
        } else {
            requestData.filename_template = filenameTemplate;
        }

        const response = await fetch(`${API_BASE}/images/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        return await response.json();
    },

    // Skip current image
    async skipImage() {
        const response = await fetch(`${API_BASE}/images/skip`, { method: 'POST' });
        return await response.json();
    },

    // Go to previous image
    async previousImage() {
        const response = await fetch(`${API_BASE}/images/previous`, { method: 'POST' });
        return await response.json();
    },

    // Rotate image
    async rotateImage(degrees) {
        const response = await fetch(`${API_BASE}/images/rotate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ degrees: degrees })
        });
        return await response.json();
    },

    // Get statistics
    async getStats() {
        const response = await fetch(`${API_BASE}/stats`);
        return await response.json();
    },

    // Manage categories
    async getCategories() {
        const response = await fetch(`${API_BASE}/categories`);
        return await response.json();
    },

    async updateCategories(categories) {
        const response = await fetch(`${API_BASE}/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ categories: categories })
        });
        return await response.json();
    },

    async addCategory(categoryName) {
        const response = await fetch(`${API_BASE}/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'add', category: categoryName })
        });
        return await response.json();
    },

    // Get categories from directory
    async getCategoriesFromDirectory() {
        const response = await fetch(`${API_BASE}/categories/from-directory`);
        return await response.json();
    },

    // Sequence management
    async getSequenceForEvent(eventName) {
        const response = await fetch(`${API_BASE}/sequence/${encodeURIComponent(eventName)}`);
        return await response.json();
    },

    async getSequenceForCategory(categoryName) {
        const response = await fetch(`${API_BASE}/sequence/category/${encodeURIComponent(categoryName)}`);
        return await response.json();
    },

    async getAllSequences() {
        const response = await fetch(`${API_BASE}/sequences`);
        return await response.json();
    },

    // Duplicate management
    async findDuplicates() {
        const response = await fetch(`${API_BASE}/duplicates`);
        return await response.json();
    },

    async getStartupDuplicatesInfo() {
        const response = await fetch(`${API_BASE}/duplicates/startup-info`);
        return await response.json();
    },

    // Session management
    async saveSession() {
        const response = await fetch(`${API_BASE}/session/save`, { method: 'POST' });
        return await response.json();
    },

    async loadSession() {
        const response = await fetch(`${API_BASE}/session/load`, { method: 'POST' });
        return await response.json();
    },

    // Get image file URL
    getImageUrl(filename) {
        return `${API_BASE}/images/file/${filename}`;
    }
};

// Error handling wrapper
const apiWithErrorHandling = {
    async call(apiFunction, ...args) {
        try {
            const result = await apiFunction(...args);
            if (result.error) {
                showNotification(result.error, 'error');
                return null;
            }
            return result;
        } catch (error) {
            console.error('API Error:', error);
            showNotification('Connection error. Make sure the server is running.', 'error');
            return null;
        }
    }
};

// Export for use in other modules
window.api = api;
window.apiWithErrorHandling = apiWithErrorHandling;