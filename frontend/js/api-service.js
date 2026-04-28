/**
 * API Service - calls the Render backend API.
 * Set `API_BASE_URL` to your Render instance URL (e.g. https://my-app.onrender.com)
 */

const API_CONFIG = {
    API_BASE_URL: window.__API_BASE__ || 'https://RENDER_APP.onrender.com',
    TIMEOUT: 60000,
};

class APIService {
    constructor() {
        this.base = API_CONFIG.API_BASE_URL.replace(/\/$/, '');
    }

    async processImage(imageBlob, mode, maskBlob = null) {
        const form = new FormData();
        form.append('image', imageBlob, 'image.png');
        if (maskBlob) form.append('mask', maskBlob, 'mask.png');

        const endpoint = mode === 'object' ? '/api/remove_object' : '/api/remove_background';
        const url = this.base + endpoint;

        const resp = await fetch(url, { method: 'POST', body: form });
        if (!resp.ok) {
            const txt = await resp.text();
            throw new Error(`Processing failed: ${resp.status} ${txt}`);
        }

        const blob = await resp.blob();
        return { blob };
    }

    async health() {
        try {
            const res = await fetch(this.base + '/api/health');
            return res.ok;
        } catch (e) {
            return false;
        }
    }
}

window.apiService = new APIService();