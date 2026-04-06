/**
 * Main Application Entry Point
 * Initializes all components and sets up the application
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Pixerase.AI - Initializing application...');
    
    // Get canvas elements
    const mainCanvas = document.getElementById('mainCanvas');
    const maskCanvas = document.getElementById('maskCanvas');
    
    if (!mainCanvas || !maskCanvas) {
        console.error('Canvas elements not found!');
        return;
    }
    
    // Initialize Canvas Manager
    window.canvasManager = new CanvasManager(mainCanvas, maskCanvas);
    
    // Initialize UI Controller
    window.uiController = new UIController();
    
    // Set default tool
    if (window.uiController) {
        window.uiController.setActiveTool('brush');
        window.uiController.setMode('bg');
    }
    
    // Listen for API status changes
    window.addEventListener('apiStatusChange', (event) => {
        const { connected } = event.detail;
        console.log(`API Status: ${connected ? 'Connected' : 'Disconnected'}`);
        
        if (!connected && window.uiController) {
            window.uiController.showStatus(
                'Backend not connected. Please start the Flask server on http://localhost:5000',
                '🔌'
            );
        }
    });
    
    // Check API health after initialization
    setTimeout(() => {
        if (window.apiService) {
            window.apiService.checkHealth();
        }
    }, 1000);
    
    console.log('Pixerase.AI - Ready!');
});

// Handle page unload cleanup
window.addEventListener('beforeunload', () => {
    if (window.apiService) {
        window.apiService.destroy();
    }
    
    // Revoke any blob URLs
    if (window.uiController && window.uiController.processedImageUrl) {
        URL.revokeObjectURL(window.uiController.processedImageUrl);
    }
});