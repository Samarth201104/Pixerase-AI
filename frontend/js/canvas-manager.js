/**
 * Canvas Manager - Handles all canvas drawing and mask operations
 */

class CanvasManager {
    constructor(mainCanvas, maskCanvas) {
        this.mainCanvas = mainCanvas;
        this.maskCanvas = maskCanvas;
        this.ctxMain = mainCanvas.getContext('2d');
        this.ctxMask = maskCanvas.getContext('2d');
        
        this.imgWidth = 0;
        this.imgHeight = 0;
        this.originalImage = null;
        this.maskData = null;
        this.maskHistory = [];
        this.historyIndex = -1;
        
        this.isDrawing = false;
        this.activeTool = 'brush';
        this.brushSize = 24;
        
        this.lastX = 0;
        this.lastY = 0;
        
        this.initDrawingEvents();
    }

    /**
     * Initialize drawing event listeners
     */
    initDrawingEvents() {
        const getCoords = (e) => {
            const rect = this.maskCanvas.getBoundingClientRect();
            const scaleX = this.maskCanvas.width / rect.width;
            const scaleY = this.maskCanvas.height / rect.height;
            
            let clientX, clientY;
            if (e.touches) {
                clientX = e.touches[0].clientX;
                clientY = e.touches[0].clientY;
            } else {
                clientX = e.clientX;
                clientY = e.clientY;
            }
            
            let canvasX = (clientX - rect.left) * scaleX;
            let canvasY = (clientY - rect.top) * scaleY;
            
            canvasX = Math.min(Math.max(0, canvasX), this.maskCanvas.width);
            canvasY = Math.min(Math.max(0, canvasY), this.maskCanvas.height);
            
            return { x: canvasX, y: canvasY };
        };
        
        const startDraw = (e) => {
            this.isDrawing = true;
            const { x, y } = getCoords(e);
            this.lastX = x;
            this.lastY = y;
            this.drawAt(x, y);
            e.preventDefault();
        };
        
        const drawMove = (e) => {
            if (!this.isDrawing) return;
            const { x, y } = getCoords(e);
            
            if (this.activeTool === 'brush') {
                const steps = Math.hypot(x - this.lastX, y - this.lastY);
                if (steps > 1) {
                    for (let step = 0; step <= steps; step += 2) {
                        const t = step / steps;
                        const ix = this.lastX + (x - this.lastX) * t;
                        const iy = this.lastY + (y - this.lastY) * t;
                        this.drawAt(ix, iy);
                    }
                } else {
                    this.drawAt(x, y);
                }
            } else {
                this.drawCircle(x, y);
            }
            
            this.lastX = x;
            this.lastY = y;
            e.preventDefault();
        };
        
        const endDraw = () => {
            if (this.isDrawing) {
                this.saveToHistory();
                this.isDrawing = false;
            }
        };
        
        this.maskCanvas.addEventListener('mousedown', startDraw);
        this.maskCanvas.addEventListener('mousemove', drawMove);
        this.maskCanvas.addEventListener('mouseup', endDraw);
        this.maskCanvas.addEventListener('touchstart', startDraw);
        this.maskCanvas.addEventListener('touchmove', drawMove);
        this.maskCanvas.addEventListener('touchend', endDraw);
    }

    /**
     * Draw at specific coordinates
     */
    drawAt(x, y) {
        if (!this.maskData) return;
        
        const rad = this.brushSize;
        const imageData = this.ctxMask.getImageData(0, 0, this.imgWidth, this.imgHeight);
        
        for (let dy = -rad; dy <= rad; dy++) {
            for (let dx = -rad; dx <= rad; dx++) {
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist <= rad) {
                    const px = Math.floor(x + dx);
                    const py = Math.floor(y + dy);
                    if (px >= 0 && px < this.imgWidth && py >= 0 && py < this.imgHeight) {
                        const idx = (py * this.imgWidth + px) * 4;
                        imageData.data[idx + 3] = 255; // Mark for removal
                    }
                }
            }
        }
        
        this.ctxMask.putImageData(imageData, 0, 0);
        this.maskData = imageData;
        this.updateMaskOverlay();
    }

    /**
     * Draw circle selection
     */
    drawCircle(x, y) {
        if (!this.maskData) return;
        
        const rad = this.brushSize;
        const imageData = this.ctxMask.getImageData(0, 0, this.imgWidth, this.imgHeight);
        
        for (let dy = -rad; dy <= rad; dy++) {
            for (let dx = -rad; dx <= rad; dx++) {
                if (Math.sqrt(dx * dx + dy * dy) <= rad) {
                    const px = Math.floor(x + dx);
                    const py = Math.floor(y + dy);
                    if (px >= 0 && px < this.imgWidth && py >= 0 && py < this.imgHeight) {
                        const idx = (py * this.imgWidth + px) * 4;
                        imageData.data[idx + 3] = 255;
                    }
                }
            }
        }
        
        this.ctxMask.putImageData(imageData, 0, 0);
        this.maskData = imageData;
        this.updateMaskOverlay();
    }

    /**
     * Update mask overlay visualization
     */
    updateMaskOverlay() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.imgWidth;
        tempCanvas.height = this.imgHeight;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.putImageData(this.maskData, 0, 0);
        
        this.ctxMask.clearRect(0, 0, this.imgWidth, this.imgHeight);
        this.ctxMask.globalCompositeOperation = 'source-over';
        this.ctxMask.drawImage(tempCanvas, 0, 0);
        
        // Apply red overlay
        const imgData = this.ctxMask.getImageData(0, 0, this.imgWidth, this.imgHeight);
        for (let i = 0; i < imgData.data.length; i += 4) {
            if (imgData.data[i + 3] > 128) {
                imgData.data[i] = 255;
                imgData.data[i + 1] = 50;
                imgData.data[i + 2] = 50;
                imgData.data[i + 3] = 180;
            } else {
                imgData.data[i + 3] = 0;
            }
        }
        this.ctxMask.putImageData(imgData, 0, 0);
    }

    /**
     * Load image into canvas
     */
    loadImage(imgElement, width, height) {
        this.imgWidth = width;
        this.imgHeight = height;
        
        this.mainCanvas.width = width;
        this.mainCanvas.height = height;
        this.maskCanvas.width = width;
        this.maskCanvas.height = height;
        
        this.ctxMain.drawImage(imgElement, 0, 0, width, height);
        this.originalImage = imgElement;
        
        this.initBlankMask();
    }

    /**
     * Initialize blank mask
     */
    initBlankMask() {
        const imageData = this.ctxMask.createImageData(this.imgWidth, this.imgHeight);
        for (let i = 0; i < imageData.data.length; i += 4) {
            imageData.data[i + 3] = 0;
        }
        this.ctxMask.putImageData(imageData, 0, 0);
        this.maskData = imageData;
        this.saveToHistory();
        this.updateMaskOverlay();
    }

    /**
     * Save current mask to history
     */
    saveToHistory() {
        const copy = this.ctxMask.getImageData(0, 0, this.imgWidth, this.imgHeight);
        this.maskHistory = this.maskHistory.slice(0, this.historyIndex + 1);
        this.maskHistory.push(copy);
        this.historyIndex++;
    }

    /**
     * Undo last mask operation
     */
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.ctxMask.putImageData(this.maskHistory[this.historyIndex], 0, 0);
            this.maskData = this.maskHistory[this.historyIndex];
            this.updateMaskOverlay();
            return true;
        }
        return false;
    }

    /**
     * Redo last mask operation
     */
    redo() {
        if (this.historyIndex < this.maskHistory.length - 1) {
            this.historyIndex++;
            this.ctxMask.putImageData(this.maskHistory[this.historyIndex], 0, 0);
            this.maskData = this.maskHistory[this.historyIndex];
            this.updateMaskOverlay();
            return true;
        }
        return false;
    }

    /**
     * Clear current mask
     */
    clearMask() {
        this.initBlankMask();
    }

    /**
     * Set active tool
     */
    setActiveTool(tool) {
        this.activeTool = tool;
    }

    /**
     * Set brush size
     */
    setBrushSize(size) {
        this.brushSize = size;
    }

    /**
     * Get mask blob for API
     */
    async getMaskBlob() {
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.imgWidth;
        tempCanvas.height = this.imgHeight;
        const tempCtx = tempCanvas.getContext('2d');
        tempCtx.putImageData(this.maskData, 0, 0);
        
        return new Promise(resolve => {
            tempCanvas.toBlob(resolve, 'image/png');
        });
    }

    /**
     * Get main canvas blob
     */
    async getImageBlob() {
        return new Promise(resolve => {
            this.mainCanvas.toBlob(resolve, 'image/png');
        });
    }

    /**
     * Display processed image
     */
    displayProcessedImage(imageUrl) {
        const img = new Image();
        img.onload = () => {
            this.ctxMain.clearRect(0, 0, this.imgWidth, this.imgHeight);
            this.ctxMain.drawImage(img, 0, 0, this.imgWidth, this.imgHeight);
        };
        img.src = imageUrl;
    }

    /**
     * Reset to original image
     */
    reset() {
        if (this.originalImage) {
            this.ctxMain.drawImage(this.originalImage, 0, 0, this.imgWidth, this.imgHeight);
            this.initBlankMask();
        }
    }

    /**
     * Enable/disable mask drawing
     */
    setMaskDrawingEnabled(enabled) {
        this.maskCanvas.style.pointerEvents = enabled ? 'auto' : 'none';
        this.maskCanvas.style.opacity = enabled ? '0.7' : '0';
    }
}