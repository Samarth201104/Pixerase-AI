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
        const { renderConnected } = event.detail;
        console.log(`Render API Status: ${renderConnected ? 'Connected' : 'Disconnected'}`);
        
        if (!renderConnected && window.uiController) {
            window.uiController.showStatus(
                'Background removal service not connected. Please check the Render deployment.',
                '🔌'
            );
        }
    });
    
    // Check API health after initialization
    setTimeout(() => {
        if (window.apiService) {
            window.apiService.checkRenderHealth();
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