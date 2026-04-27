/**
 * UI Controller - Manages UI state and interactions
 */

class UIController {
    constructor() {
        this.currentMode = 'bg'; // 'bg' or 'object'
        this.isProcessing = false;
        this.processedImageUrl = null;
        
        this.initElements();
        this.initEventListeners();
        this.initTheme();
    }

    /**
     * Initialize DOM elements
     */
    initElements() {
        this.elements = {
            modeBgBtn: document.getElementById('modeBgBtn'),
            modeObjectBtn: document.getElementById('modeObjectBtn'),
            objectTools: document.getElementById('objectTools'),
            brushToolBtn: document.getElementById('brushToolBtn'),
            circleToolBtn: document.getElementById('circleToolBtn'),
            brushSize: document.getElementById('brushSize'),
            brushSizeVal: document.getElementById('brushSizeVal'),
            undoBtn: document.getElementById('undoMaskBtn'),
            redoBtn: document.getElementById('redoMaskBtn'),
            clearMaskBtn: document.getElementById('clearMaskBtn'),
            processBtn: document.getElementById('processBtn'),
            downloadBtn: document.getElementById('downloadBtn'),
            resetBtn: document.getElementById('resetBtn'),
            uploadArea: document.getElementById('uploadArea'),
            fileInput: document.getElementById('fileInput'),
            compareSlider: document.getElementById('compareSlider'),
            compareRange: document.getElementById('sliderCompare'),
            statusMsg: document.getElementById('statusMsg'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            imagePlaceholder: document.getElementById('imagePlaceholder'),
            imageInfo: document.getElementById('imageInfo'),
            imageDimensions: document.getElementById('imageDimensions')
        };
    }

    /**
     * Initialize event listeners
     */
    initEventListeners() {
        // Mode switching
        this.elements.modeBgBtn?.addEventListener('click', () => this.setMode('bg'));
        this.elements.modeObjectBtn?.addEventListener('click', () => this.setMode('object'));
        
        // Tool selection
        this.elements.brushToolBtn?.addEventListener('click', () => this.setActiveTool('brush'));
        this.elements.circleToolBtn?.addEventListener('click', () => this.setActiveTool('circle'));
        
        // Brush size
        this.elements.brushSize?.addEventListener('input', (e) => {
            const size = e.target.value;
            this.elements.brushSizeVal.textContent = `${size}px`;
            if (window.canvasManager) {
                window.canvasManager.setBrushSize(parseInt(size));
            }
        });
        
        // Mask operations
        this.elements.undoBtn?.addEventListener('click', () => {
            if (window.canvasManager) {
                window.canvasManager.undo();
            }
        });
        
        this.elements.redoBtn?.addEventListener('click', () => {
            if (window.canvasManager) {
                window.canvasManager.redo();
            }
        });
        
        this.elements.clearMaskBtn?.addEventListener('click', () => {
            if (window.canvasManager) {
                window.canvasManager.clearMask();
            }
        });
        
        // File upload
        this.elements.uploadArea?.addEventListener('click', () => {
            this.elements.fileInput?.click();
        });
        
        this.elements.fileInput?.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                this.handleImageUpload(e.target.files[0]);
            }
        });
        
        // Drag and drop
        this.setupDragAndDrop();
        
        // Action buttons
        this.elements.processBtn?.addEventListener('click', () => this.processImage());
        this.elements.downloadBtn?.addEventListener('click', () => this.downloadImage());
        this.elements.resetBtn?.addEventListener('click', () => this.reset());
        
        // Compare slider
        this.elements.compareRange?.addEventListener('input', (e) => {
            this.handleCompareSlider(e.target.value);
        });
    }

    /**
     * Setup drag and drop
     */
    setupDragAndDrop() {
        const uploadArea = this.elements.uploadArea;
        if (!uploadArea) return;
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                this.handleImageUpload(file);
            }
        });
    }

    /**
     * Handle image upload
     */
    async handleImageUpload(file) {
        this.showStatus('Loading image...', '⏳');
        
        try {
            const { img, width, height } = await window.imageProcessor.loadImageFromFile(file);
            
            // Hide placeholder
            if (this.elements.imagePlaceholder) {
                this.elements.imagePlaceholder.style.display = 'none';
            }
            
            // Show image info
            if (this.elements.imageInfo) {
                this.elements.imageInfo.style.display = 'flex';
                this.elements.imageDimensions.textContent = `${width} × ${height}`;
            }
            
            // Load into canvas
            if (window.canvasManager) {
                window.canvasManager.loadImage(img, width, height);
            }
            
            this.showStatus('Image loaded successfully', '✅');
            this.elements.processBtn.disabled = false;
            
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, '❌');
            console.error('Upload error:', error);
        }
    }

    /**
     * Set active mode
     */
    setMode(mode) {
        this.currentMode = mode;
        
        // Update UI
        if (mode === 'bg') {
            this.elements.modeBgBtn?.classList.add('active');
            this.elements.modeObjectBtn?.classList.remove('active');
            this.elements.objectTools.style.display = 'none';
            
            if (window.canvasManager) {
                window.canvasManager.setMaskDrawingEnabled(false);
            }
            
            this.showStatus('Background removal mode active', '🖼️');
        } else {
            this.elements.modeObjectBtn?.classList.add('active');
            this.elements.modeBgBtn?.classList.remove('active');
            this.elements.objectTools.style.display = 'block';
            
            if (window.canvasManager) {
                window.canvasManager.setMaskDrawingEnabled(true);
            }
            
            this.showStatus('Object removal mode active - paint over objects to remove', '✏️');
        }
    }

    /**
     * Set active tool
     */
    setActiveTool(tool) {
        if (tool === 'brush') {
            this.elements.brushToolBtn?.classList.add('tool-active');
            this.elements.circleToolBtn?.classList.remove('tool-active');
        } else {
            this.elements.circleToolBtn?.classList.add('tool-active');
            this.elements.brushToolBtn?.classList.remove('tool-active');
        }
        
        if (window.canvasManager) {
            window.canvasManager.setActiveTool(tool);
        }
    }

    /**
     * Process image with backend API
     */
    async processImage() {
        if (!window.canvasManager || !window.canvasManager.originalImage) {
            this.showStatus('Please upload an image first', '⚠️');
            return;
        }

        if (this.currentMode === 'bg' && !window.apiService.isRenderConnected) {
            this.showStatus('Background removal service not connected', '🔌');
            return;
        }

        this.isProcessing = true;
        this.showLoading(true);
        this.elements.processBtn.disabled = true;

        try {
            if (this.currentMode === 'object') {
                // Object removal is now on Hugging Face Spaces
                const hfUrl = window.apiService.getObjectRemovalURL();
                this.showStatus('Redirecting to object removal service...', '🔗');

                // Show a modal or redirect after a short delay
                setTimeout(() => {
                    window.open(hfUrl, '_blank');
                    this.showStatus('Object removal service opened in new tab', '✅');
                }, 1000);

                this.isProcessing = false;
                this.showLoading(false);
                this.elements.processBtn.disabled = false;
                return;
            }

            // Background removal via Render API
            const imageBlob = await window.canvasManager.getImageBlob();
            const response = await window.apiService.processImage(imageBlob, this.currentMode);

            if (response instanceof Blob) {
                const url = URL.createObjectURL(response);
                this.processedImageUrl = url;
                window.canvasManager.displayProcessedImage(url);
                this.showCompareSlider(true);
                this.elements.downloadBtn.disabled = false;
                this.showStatus('Background removal complete!', '✅');
            }

        } catch (error) {
            this.showStatus(`Processing failed: ${error.message}`, '❌');
            console.error('Process error:', error);
        } finally {
            this.isProcessing = false;
            this.showLoading(false);
            this.elements.processBtn.disabled = false;
        }
    }

    /**
     * Download processed image
     */
    downloadImage() {
        if (!this.processedImageUrl) {
            this.showStatus('No processed image available', '⚠️');
            return;
        }
        
        const a = document.createElement('a');
        a.href = this.processedImageUrl;
        a.download = `pixerase_${Date.now()}.png`;
        a.click();
        
        this.showStatus('Download started', '⬇️');
    }

    /**
     * Reset to original image
     */
    reset() {
        if (window.canvasManager) {
            window.canvasManager.reset();
        }
        
        this.processedImageUrl = null;
        this.showCompareSlider(false);
        this.elements.downloadBtn.disabled = true;
        this.showStatus('Reset to original', '⟳');
    }

    /**
     * Handle compare slider
     */
    handleCompareSlider(value) {
        // Implement before/after comparison
        // This would toggle between original and processed
        const val = parseInt(value);
        // Simplified: for production, implement smooth transition
    }

    /**
     * Show/hide compare slider
     */
    showCompareSlider(show) {
        if (this.elements.compareSlider) {
            this.elements.compareSlider.style.display = show ? 'flex' : 'none';
        }
    }

    /**
     * Show status message
     */
    showStatus(message, icon = '✅') {
        if (this.elements.statusMsg) {
            this.elements.statusMsg.innerHTML = `<span class="status-icon">${icon}</span><span>${message}</span>`;
        }
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
        
        if (show) {
            document.body.classList.add('disabled-ui');
        } else {
            document.body.classList.remove('disabled-ui');
        }
    }

    /**
     * Initialize theme
     */
    initTheme() {
        const themeToggle = document.getElementById('themeToggle');
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme === 'light') {
            document.body.classList.add('light');
        }
        
        themeToggle?.addEventListener('click', () => {
            document.body.classList.toggle('light');
            const isLight = document.body.classList.contains('light');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
        });
    }
}