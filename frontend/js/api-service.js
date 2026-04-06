/**
 * API Service - FIXED VERSION (CRITICAL BUG RESOLVED)
 */

const API_CONFIG = {
    BASE_URL: 'http://localhost:5000',
    ENDPOINTS: {
        PROCESS: '/api/process',
        HEALTH: '/api/health'
    },
    TIMEOUT: 30000,
    MAX_RETRIES: 2
};

class APIService {
    constructor() {
        this.isConnected = false;
        this.connectionCheckInterval = null;
        this.initHealthCheck();
    }

    initHealthCheck() {
        this.checkHealth();
        this.connectionCheckInterval = setInterval(() => this.checkHealth(), 30000);
    }

    async checkHealth() {
        try {
            const res = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`);
            const data = await res.json();
            this.isConnected = data?.status === 'ok';
            this.updateConnectionStatus(this.isConnected);
        } catch {
            this.isConnected = false;
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.status-indicator');
        const statusText = document.getElementById('statusText');

        if (indicator) {
            indicator.className = `status-indicator ${connected ? 'online' : 'offline'}`;
        }

        if (statusText) {
            statusText.textContent = connected ? 'Backend: Connected' : 'Backend: Not Connected';
        }

        window.dispatchEvent(new CustomEvent('apiStatusChange', {
            detail: { connected }
        }));
    }

    /**
     * 🔥 FIXED REQUEST METHOD
     */
    async request(endpoint, options = {}) {
        const url = `${API_CONFIG.BASE_URL}${endpoint}`;

        let lastError;

        for (let i = 0; i <= API_CONFIG.MAX_RETRIES; i++) {
            try {
                const response = await fetch(url, options);

                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.error || `HTTP ${response.status}`);
                }

                const contentType = response.headers.get("content-type");

                // ✅ IMPORTANT FIX
                if (contentType && contentType.includes("image")) {
                    return await response.blob();   // 🔥 RETURN BLOB
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

    async processImage(imageBlob, mode, maskBlob = null) {
        const formData = new FormData();
        formData.append("image", imageBlob, "image.png");
        formData.append("mode", mode === "bg" ? "background" : "object");

        if (mode === "object" && maskBlob) {
            formData.append("mask", maskBlob, "mask.png");
        }

        return await this.request(API_CONFIG.ENDPOINTS.PROCESS, {
            method: "POST",
            body: formData
        });
    }

    destroy() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
    }
}

window.apiService = new APIService();