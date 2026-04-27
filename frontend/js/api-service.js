/**
 * API Service - UPDATED FOR SPLIT DEPLOYMENT ARCHITECTURE
 * Background Removal: Render (Flask API)
 * Object Removal: Hugging Face Spaces (Gradio Interface)
 */

const API_CONFIG = {
    // Render service for background removal
    RENDER_BASE_URL: 'https://pixerase-ai.onrender.com',
    RENDER_ENDPOINTS: {
        REMOVE_BACKGROUND: '/api/remove-background',
        HEALTH: '/api/health'
    },
    // Hugging Face Spaces for object removal (Gradio interface)
    HF_SPACES_URL: 'https://your-huggingface-space-url.hf.space',
    TIMEOUT: 30000,
    MAX_RETRIES: 2
};

class APIService {
    constructor() {
        this.isRenderConnected = false;
        this.connectionCheckInterval = null;
        this.initHealthCheck();
    }

    initHealthCheck() {
        this.checkRenderHealth();
        this.connectionCheckInterval = setInterval(() => this.checkRenderHealth(), 30000);
    }

    async checkRenderHealth() {
        try {
            const res = await fetch(`${API_CONFIG.RENDER_BASE_URL}${API_CONFIG.RENDER_ENDPOINTS.HEALTH}`);
            const data = await res.json();
            this.isRenderConnected = data?.status === 'ok';
            this.updateConnectionStatus();
        } catch {
            this.isRenderConnected = false;
            this.updateConnectionStatus();
        }
    }

    updateConnectionStatus() {
        const indicator = document.querySelector('.status-indicator');
        const statusText = document.getElementById('statusText');

        if (indicator) {
            indicator.className = `status-indicator ${this.isRenderConnected ? 'online' : 'offline'}`;
        }

        if (statusText) {
            statusText.textContent = this.isRenderConnected ?
                'Background Removal: Connected' :
                'Background Removal: Not Connected';
        }

        window.dispatchEvent(new CustomEvent('apiStatusChange', {
            detail: { renderConnected: this.isRenderConnected }
        }));
    }

    /**
     * Request method for Render API calls
     */
    async request(endpoint, options = {}) {
        const url = `${API_CONFIG.RENDER_BASE_URL}${endpoint}`;

        let lastError;

        for (let i = 0; i <= API_CONFIG.MAX_RETRIES; i++) {
            try {
                const response = await fetch(url, options);

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.error || `HTTP ${response.status}`);
                }

                const contentType = response.headers.get("content-type");

                // Handle image responses
                if (contentType && contentType.includes("image")) {
                    return await response.blob();
                }

                return await response.json();

            } catch (err) {
                lastError = err;

                if (i < API_CONFIG.MAX_RETRIES) {
                    await new Promise(r => setTimeout(r, 1000));
                }
            }
        }

        throw lastError;
    }

    /**
     * Process image based on mode
     * Background removal: Uses Render API
     * Object removal: Redirects to Hugging Face Spaces
     */
    async processImage(imageBlob, mode, maskBlob = null) {
        if (mode === "bg" || mode === "background") {
            // Background removal via Render API
            const formData = new FormData();
            formData.append("image", imageBlob, "image.png");

            return await this.request(API_CONFIG.RENDER_ENDPOINTS.REMOVE_BACKGROUND, {
                method: "POST",
                body: formData
            });

        } else if (mode === "object") {
            // Object removal via Hugging Face Spaces
            // Since Gradio doesn't provide REST API, we'll show a message
            // and provide a link to the Hugging Face Space
            throw new Error("Object removal is now available on our dedicated service. Please visit: " + API_CONFIG.HF_SPACES_URL);
        } else {
            throw new Error("Invalid processing mode. Use 'background' or 'object'");
        }
    }

    /**
     * Get Hugging Face Spaces URL for object removal
     */
    getObjectRemovalURL() {
        return API_CONFIG.HF_SPACES_URL;
    }

    destroy() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
    }
}

window.apiService = new APIService();