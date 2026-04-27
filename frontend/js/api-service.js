/**
 * API Service - UPDATED FOR HUGGING FACE SPACES DEPLOYMENT
 * Both Background Removal and Object Removal now run on HF Spaces via Gradio
 */

const API_CONFIG = {
    // Hugging Face Spaces URLs for both services
    HF_SPACES_URL: 'https://your-huggingface-username-pixerase-ai.hf.space',
    TIMEOUT: 30000,
    MAX_RETRIES: 2
};

class APIService {
    constructor() {
        this.isHFConnected = true; // Always assume HF is available (handled by redirects)
        this.connectionCheckInterval = null;
    }

    /**
     * Get Hugging Face Spaces URL for background removal
     */
    getBackgroundRemovalURL() {
        return API_CONFIG.HF_SPACES_URL;
    }

    /**
     * Get Hugging Face Spaces URL for object removal
     */
    getObjectRemovalURL() {
        return API_CONFIG.HF_SPACES_URL;
    }

    /**
     * Process image - redirects to HF Spaces
     * Both modes use the same Gradio interface
     */
    async processImage(imageBlob, mode, maskBlob = null) {
        if (mode === "bg" || mode === "background") {
            // Redirect to HF Spaces for background removal
            window.open(this.getBackgroundRemovalURL(), '_blank');
            return { redirected: true, url: this.getBackgroundRemovalURL() };
        } else if (mode === "object") {
            // Redirect to HF Spaces for object removal
            window.open(this.getObjectRemovalURL(), '_blank');
            return { redirected: true, url: this.getObjectRemovalURL() };
        } else {
            throw new Error("Invalid processing mode. Use 'background' or 'object'");
        }
    }

    /**
     * Check HF connection status (always true since we use web redirects)
     */
    checkHFConnection() {
        this.isHFConnected = true;
    }

    destroy() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
    }
}

window.apiService = new APIService();