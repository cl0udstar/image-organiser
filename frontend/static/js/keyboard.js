// Keyboard shortcuts management for Image Organizer

const keyboard = {
    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Skip if typing in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                // Allow Enter in the dynamic category input
                if (e.target.id === 'newCategoryDynamic' && e.key === 'Enter') {
                    e.preventDefault();
                    actions.addNewCategory();
                }
                return;
            }

            const key = e.key.toLowerCase();
            
            switch (key) {
                case 'd':
                    e.preventDefault();
                    actions.deleteImage();
                    break;
                case 's':
                    e.preventDefault();
                    actions.skipImage();
                    break;
                case 'arrowleft':
                    e.preventDefault();
                    actions.previousImage();
                    break;
                case 'enter':
                    e.preventDefault();
                    actions.processCurrentImage();
                    break;
                case ' ':
                    e.preventDefault();
                    ui.toggleZoom();
                    break;
                case 'r':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        actions.rotateImage(90);
                    } else if (e.shiftKey) {
                        e.preventDefault();
                        ui.loadCategoriesFromDirectoryDuringProcessing();
                    }
                    break;
                case 't':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        ui.toggleTheme();
                    }
                    break;
                default:
                    // Check for number keys (1-9)
                    const num = parseInt(key);
                    if (num >= 1 && num <= 9 && num <= categories.length) {
                        e.preventDefault();
                        ui.toggleCategory(categories[num - 1]);
                    }
                    break;
            }
        });
    },

    // Show keyboard shortcuts help
    showShortcutsHelp() {
        const shortcutsHelp = document.getElementById('shortcutsHelp');
        shortcutsHelp.classList.add('show');
        setTimeout(() => shortcutsHelp.classList.remove('show'), 5000);
    }
};

// Export for global use
window.keyboard = keyboard;