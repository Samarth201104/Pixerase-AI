/**
 * CONFIGURATION TEMPLATE
 * 
 * Before deploying, update the following values:
 * 1. Replace YOUR_HF_USERNAME with your Hugging Face username
 * 2. Replace pixerase-ai with your Space name (if different)
 * 3. Update RENDER_BASE_URL if using a different domain
 */

// ============================================
// HUGGING FACE SPACES CONFIGURATION
// ============================================

const HF_SPACES_CONFIG = {
    // Your Hugging Face Space URL
    // Format: https://huggingface.co/spaces/{your-username}/{space-name}
    // Or if you have a custom domain, use that instead
    BASE_URL: 'https://huggingface.co/spaces/YOUR_HF_USERNAME/pixerase-ai',
    
    // For embedded deployment (optional)
    // Enable this if deploying the frontend as a separate service
    EMBED_IFRAME: false,
    IFRAME_HEIGHT: '800px',
};

// ============================================
// UPDATE INSTRUCTIONS
// ============================================

/*
STEP 1: Update your HF Space URL
   Replace: 'YOUR_HF_USERNAME'
   With: Your actual Hugging Face username (e.g., 'john-doe')
   
   Replace: 'pixerase-ai'
   With: Your actual Space name (if you named it differently)

STEP 2: Update in api-service.js
   Open: frontend/js/api-service.js
   Find: const API_CONFIG = {
   Update: HF_SPACES_URL: 'https://huggingface.co/spaces/YOUR_HF_USERNAME/pixerase-ai',

STEP 3: Test the deployment
   - Open your frontend
   - Click "Process" button
   - Should redirect to HF Spaces in a new tab

STEP 4: (Optional) Custom domain
   If using a custom domain for your HF Space:
   Update HF_SPACES_CONFIG.BASE_URL to your custom domain

STEP 5: (Optional) Embedded deployment
   If you want to embed HF Spaces in your frontend:
   - Set EMBED_IFRAME to true
   - Update index.html to include iframe
   - Update css for responsive design
*/

// ============================================
// DEVELOPMENT vs PRODUCTION
// ============================================

const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

// Use local testing URL in development
const API_BASE_URL = isDevelopment 
    ? 'http://localhost:7860'  // Local Gradio development
    : HF_SPACES_CONFIG.BASE_URL;  // Production HF Spaces

// ============================================
// EXPORT FOR USE
// ============================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        HF_SPACES_CONFIG,
        API_BASE_URL,
    };
}
