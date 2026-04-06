/**
 * Image Processor - Handles image manipulation utilities
 */

class ImageProcessor {
    constructor() {
        this.supportedFormats = ['image/jpeg', 'image/png', 'image/webp'];
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
    }

    /**
     * Validate image file
     */
    validateImage(file) {
        if (!file) {
            throw new Error('No file provided');
        }
        
        if (!this.supportedFormats.includes(file.type)) {
            throw new Error(`Unsupported format. Please use ${this.supportedFormats.join(', ')}`);
        }
        
        if (file.size > this.maxFileSize) {
            throw new Error(`File too large. Max size: ${this.maxFileSize / 1024 / 1024}MB`);
        }
        
        return true;
    }

    /**
     * Load image from file and return HTMLImageElement
     */
    loadImageFromFile(file) {
        return new Promise((resolve, reject) => {
            this.validateImage(file);
            
            const img = new Image();
            const url = URL.createObjectURL(file);
            
            img.onload = () => {
                URL.revokeObjectURL(url);
                resolve({
                    img: img,
                    width: img.width,
                    height: img.height,
                    url: url
                });
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load image'));
            };
            
            img.src = url;
        });
    }

    /**
     * Load image from URL
     */
    loadImageFromUrl(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                resolve({
                    img: img,
                    width: img.width,
                    height: img.height
                });
            };
            
            img.onerror = () => reject(new Error('Failed to load image from URL'));
            img.src = url;
        });
    }

    /**
     * Convert canvas to blob
     */
    canvasToBlob(canvas, type = 'image/png', quality = 1.0) {
        return new Promise((resolve) => {
            canvas.toBlob(resolve, type, quality);
        });
    }

    /**
     * Create a copy of ImageData
     */
    copyImageData(imageData) {
        const copy = new ImageData(
            new Uint8ClampedArray(imageData.data),
            imageData.width,
            imageData.height
        );
        return copy;
    }

    /**
     * Resize image maintaining aspect ratio
     */
    resizeImage(img, maxWidth, maxHeight) {
        let width = img.width;
        let height = img.height;
        
        if (width > maxWidth) {
            height = (height * maxWidth) / width;
            width = maxWidth;
        }
        
        if (height > maxHeight) {
            width = (width * maxHeight) / height;
            height = maxHeight;
        }
        
        return { width: Math.floor(width), height: Math.floor(height) };
    }

    /**
     * Draw mask overlay for preview
     */
    drawMaskOverlay(maskCanvas, maskData, color = { r: 255, g: 50, b: 50, a: 180 }) {
        const ctx = maskCanvas.getContext('2d');
        const imgData = ctx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
        
        for (let i = 0; i < imgData.data.length; i += 4) {
            // Check if mask has alpha > 128 (painted area)
            if (maskData.data[i + 3] > 128) {
                imgData.data[i] = color.r;
                imgData.data[i + 1] = color.g;
                imgData.data[i + 2] = color.b;
                imgData.data[i + 3] = color.a;
            } else {
                imgData.data[i + 3] = 0;
            }
        }
        
        ctx.putImageData(imgData, 0, 0);
    }

    /**
     * Create blank mask (fully transparent)
     */
    createBlankMask(width, height) {
        const imageData = new ImageData(width, height);
        for (let i = 0; i < imageData.data.length; i += 4) {
            imageData.data[i + 3] = 0;
        }
        return imageData;
    }

    /**
     * Get image dimensions from file
     */
    async getImageDimensions(file) {
        const { width, height } = await this.loadImageFromFile(file);
        return { width, height };
    }

    /**
     * Compress image if needed
     */
    async compressImage(canvas, maxSize = 1920) {
        let { width, height } = canvas;
        
        if (width > maxSize || height > maxSize) {
            if (width > height) {
                height = (height * maxSize) / width;
                width = maxSize;
            } else {
                width = (width * maxSize) / height;
                height = maxSize;
            }
            
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = Math.floor(width);
            tempCanvas.height = Math.floor(height);
            const ctx = tempCanvas.getContext('2d');
            ctx.drawImage(canvas, 0, 0, tempCanvas.width, tempCanvas.height);
            
            return tempCanvas;
        }
        
        return canvas;
    }
}

// Create global instance
window.imageProcessor = new ImageProcessor();